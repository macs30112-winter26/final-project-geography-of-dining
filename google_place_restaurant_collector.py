"""
Author: Jessica Xu

This code uses the Google Places API to collect restaurants in Chicago by building a Chicago boundary polygon, 
generating a grid of query points, and keeping only restaurants (by place_id) located inside the polygon. 
It de-duplicates previously collected places and supports different grid sizes to increase coverage without duplication. 
(note: each nearby search request returns at most 20 places)

References:
https://developers.google.com/maps/documentation/places/web-service/nearby-search
https://shapely.readthedocs.io/en/stable/geometry.html
https://docs.python.org/3/tutorial/errors.html

AI used only for debugging and minor modifications.
"""

import os
import pandas as pd
import json
import requests
import time
import math
import random
from shapely import wkt
from shapely.geometry import Point
from shapely.ops import unary_union

# Set Path
"""
cd local path
export GOOGLE_PLACES_API_KEY="API_KEY"
python3 file_name.py
"""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Source: Chicago Data Portal - Boundaries - Community Areas - Map
# https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-Map/cauq-8yn6
BOUNDARY_COMMUNITY_AREAS_CSV = os.path.join(BASE_DIR, "Boundaries_-_Community_Areas_20260202.csv")

OUT_DIR = os.path.join(BASE_DIR, "Google_Place_Chicago_restaurants")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_CSV = os.path.join(OUT_DIR, "gp_chicago.csv")
OUT_ERRORLOG = os.path.join(OUT_DIR, "gp_chicago_error_log.jsonl")


# Settings 


# os.environ["GOOGLE_PLACES_API_KEY"] = "API_KEY"
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
assert API_KEY, "Missing GOOGLE_PLACES_API_KEY"

# Stop after N unique restaurants/place_id
gp_stop_after_n = 9000 

# Google Places Api Nearby Search
URL = "https://places.googleapis.com/v1/places:searchNearby"

# Per-grid-point query settings
gp_max_per_point = 20 # Google Places API Nearby Search only returns up to 20 results
gp_radius_m = 900.0 # in meter
gp_sleep = 0.10 

# frequent save to reduce risk in data loss
SAVE_EVERY_POINTS = 10
save_every = 200 


LOW_NEW_WINDOW = 30
LOW_NEW_THRESHOLD = 1  # None to disable
STEP_km = 1.4

# save geometry column in the boundary CSV
Boundry_geom_cols = ["the_geom", "the_geom_webmercator", "geometry"]


# Build chicago polygon with city_poly
df_b = pd.read_csv(BOUNDARY_COMMUNITY_AREAS_CSV)

geom_col = None
for c in Boundry_geom_cols:
    if c in df_b.columns:
        geom_col = c
        break
assert geom_col is not None, f"Cannot find geometry column"

polys = []
for s in df_b[geom_col].dropna().astype(str):
    try:
        polys.append(wkt.loads(s))
    except Exception:
        pass

assert len(polys) > 0, "Failed"
city_poly = unary_union(polys)  # merge community areas into a whole Chicago polygon
# print("Chicago:", city_poly.geom_type)


# Calculate grid points

# Approximate degree step sizes for a given distance in km at a reference latitude.
def approx_deg_step_km(km, lat_ref):
    dlat = km / 111.0
    dlon = km / (111.0 * max(0.1, math.cos(math.radians(lat_ref))))
    return dlat, dlon

# Generate a lat/lon grid over a polygon and keep only points inside the polygon
def make_grid_points_within_polygon(poly, step_km=1.4, lat_offset=0.0, lon_offset=0.0):
    minx, miny, maxx, maxy = poly.bounds  # x=lon, y=lat
    lat_ref = (miny + maxy)/2.0
    dlat, dlon = approx_deg_step_km(step_km, lat_ref)

    pts = []
    lat = miny +lat_offset
    while lat <= maxy:
        lon = minx + lon_offset
        while lon <= maxx:
            if poly.contains(Point(lon, lat)):
                pts.append((lat, lon))
            lon += dlon
        lat += dlat
    return pts, dlat, dlon

# base grid
grid_base, dlat, dlon = make_grid_points_within_polygon(city_poly, step_km=STEP_km, lat_offset=0.0, lon_offset=0.0)

# additional grid
grid_offset, _, _ = make_grid_points_within_polygon(city_poly, step_km=STEP_km, lat_offset=dlat/2.0, lon_offset=dlon/2.0)

# avoid duplication of (lat, lon) points; round them and keep only one point per location
def dedup_points(points, ndigits=6):
    seen = set()
    out = []
    for lat, lon in points:
        key = (round(lat, ndigits), round(lon, ndigits))
        if key in seen:
            continue
        seen.add(key)
        out.append((lat, lon))
    return out

grid_points = dedup_points(grid_base + grid_offset, ndigits=6)

random.seed(42)
random.shuffle(grid_points)


# Fieldmask required by Google Places API
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.priceRange",
        "places.priceLevel",
        "places.types",
        "places.primaryType",
        "places.rating",
        "places.userRatingCount",
        "places.businessStatus",
        "places.regularOpeningHours",
        "places.takeout",
        "places.delivery",
        "places.dineIn",
        "places.reservable"
    ])
}


# Saving
with open(OUT_ERRORLOG, "w") as f:
    pass

def append_rows_to_csv(rows, out_csv): # Overwrite error log each run
    if not rows:
        return
    df = pd.DataFrame(rows)
    file_exists = os.path.exists(out_csv)
    df.to_csv(out_csv, mode="a", header=not file_exists, index=False)

def log_error(idx, gp_query_lat, gp_query_lon, status_code=None, msg=None, text=None):
    """ Append API/error record to OUT_ERRORLOG"""
    rec = {
        "idx": idx,
        "gp_query_lat": gp_query_lat,
        "gp_query_lon": gp_query_lon,
        "status_code": status_code,
        "msg": msg,
        "text_head": (text[:200] if isinstance(text, str) else None),
    }
    with open(OUT_ERRORLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


# check if it can resume, de-duplicate by place_id, add polygon filter per place

seen_place_ids = set()

# check if it can resume
if os.path.exists(OUT_CSV):
    try:
        df_existing = pd.read_csv(OUT_CSV, usecols=["gp_place_id"])
        existing_ids = df_existing["gp_place_id"].dropna().astype(str).tolist()  
        seen_place_ids.update(existing_ids) #load existing place_ids so we do not repeat
        print(f"Resume: loaded {len(existing_ids)} existing place_ids from {OUT_CSV}")
    except Exception as e:
        print("Resume: found existing CSV but failed to read it; continue without resume")
        print("Reason:", str(e))
else:
    print(f"A new file will be created at: {OUT_CSV}")

buffer_rows = [] 
points_since_save = 0
total_points = len(grid_points)

# Track new-place rate 
new_counts_window = []

def place_in_chicago(place_obj) -> bool:
    """Keep only places with coordinates inside the Chicago polygon."""
    loc = place_obj.get("location") or {}
    lat = loc.get("latitude") 
    lon = loc.get("longitude")
    if lat is None or lon is None:
        return False
    return city_poly.contains(Point(lon,lat))

# search restaurants within a radius around this grid point
for idx, (gp_query_lat, gp_query_lon) in enumerate(grid_points, start=1):
    payload = {
        "includedTypes": ["restaurant"],
        "maxResultCount": gp_max_per_point,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": gp_query_lat, "longitude": gp_query_lon},
                "radius": gp_radius_m,
            }
        }
    }

    # make API request
    try:
        resp = requests.post(URL, json=payload, headers=HEADERS, timeout=30)
    except Exception as e: # try to catch request error
        print(f"[{idx}/{total_points}] Request error:", str(e))
        log_error(idx, gp_query_lat, gp_query_lon, msg="reqesterror", text=str(e)) # log the failure abd skip
        points_since_save += 1
        time.sleep(gp_sleep)
        continue

    if resp.status_code != 200: # try to catch http error
        print(f"[{idx}/{total_points}] HTTP {resp.status_code}: {resp.text[:150]}")
        log_error(idx, gp_query_lat, gp_query_lon, status_code=resp.status_code, msg="httperror", text=resp.text) # log the failure abd skip
        points_since_save +=1
        time.sleep(gp_sleep)
        continue

    data = resp.json()
    new_this_point = 0 # count new places added from this grid point

    for place in data.get("places", []):
        gp_place_id = place.get("id")
        if (not gp_place_id) or (gp_place_id in seen_place_ids): # skip place with missing ID or those we have collected from another grid point
            continue

        if not place_in_chicago(place): # skip place not in Chicago boundary polygon
            continue

        seen_place_ids.add(gp_place_id) # save in set to avoid repetition
        new_this_point += 1
        
        # Save selected fields into output row
        buffer_rows.append({
            "gp_place_id": gp_place_id,
            "gp_name": (place.get("displayName") or {}).get("text"),
            "gp_address": place.get("formattedAddress"),
            "gp_latitude": (place.get("location") or {}).get("latitude"),
            "gp_longitude": (place.get("location") or {}).get("longitude"),
            "gp_price_range_raw": place.get("priceRange"),
            "gp_price_level": place.get("priceLevel"),
            "gp_types": ",".join(place.get("types", [])),
            "gp_primary_type": place.get("primaryType"),
            "gp_rating": place.get("rating"),
            "gp_review_count": place.get("userRatingCount"),
            "gp_business_status": place.get("businessStatus"),
            "gp_regular_opening_hours_raw": place.get("regularOpeningHours"),
            "gp_takeout": place.get("takeout"),
            "gp_delivery": place.get("delivery"),
            "gp_dine_in": place.get("dineIn"),
            "gp_reservable": place.get("reservable"),
            "gp_query_lat": gp_query_lat,
            "gp_query_lon": gp_query_lon,
        })

        if len(seen_place_ids) >= gp_stop_after_n:
            break

    # Update early-stop condition
    new_counts_window.append(new_this_point)
    if len(new_counts_window) > LOW_NEW_WINDOW:
        new_counts_window.pop(0)

    points_since_save += 1 # track update grid points from last CSV file

    if idx % 25 == 0: # print progress every 25 grid points 
        avg_new = sum(new_counts_window) / max(1, len(new_counts_window))
        print(f"[{idx}/{total_points}] unique={len(seen_place_ids)} | "
            f"new_this_point={new_this_point} | avg_new(last{len(new_counts_window)})={avg_new:.2f}")

    # Write buffered rows to disk regularly to reduce risk
    if (len(buffer_rows) >= save_every) or (points_since_save >= SAVE_EVERY_POINTS):
        append_rows_to_csv(buffer_rows, OUT_CSV)
        buffer_rows.clear()
        points_since_save = 0
        print(f"Saved at grid point {idx}. unique={len(seen_place_ids)} | csv={OUT_CSV}")

    # Stop if reached target N unique restaurants
    if len(seen_place_ids) >= gp_stop_after_n:
        append_rows_to_csv(buffer_rows, OUT_CSV)
        buffer_rows.clear()
        print("Stop condition met N:", gp_stop_after_n)
        break

    # Stop if recent grid points are not finding many new places
    if LOW_NEW_THRESHOLD is not None and len(new_counts_window) == LOW_NEW_WINDOW:
        avg_new = sum(new_counts_window) / LOW_NEW_WINDOW
        if avg_new < LOW_NEW_THRESHOLD:
            append_rows_to_csv(buffer_rows, OUT_CSV)
            buffer_rows.clear()
            print(f"Stop condition met (low new rate): avg_new(last{LOW_NEW_WINDOW})={avg_new:.2f} < {LOW_NEW_THRESHOLD}")
            break

    
    time.sleep(gp_sleep)

# Final save
append_rows_to_csv(buffer_rows, OUT_CSV)
buffer_rows.clear()

print("DONE. Total unique places collected:", len(seen_place_ids))
print("Saved CSV:",OUT_CSV)
print("Saved error log JSONL:", OUT_ERRORLOG)
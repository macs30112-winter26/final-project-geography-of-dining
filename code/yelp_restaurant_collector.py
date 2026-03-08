"""
Author: Jessica Xu

This code uses the Yelp Fusion API to collect restaurant data for Chicago ZIP codes. 

References:
https://docs.developer.yelp.com/docs/places-intro

AI used only for debugging and minor modifications.
"""

import os
import pandas as pd
import requests
import time


"""
cd local path
export YELP_FUSION_API_KEY="API_KEY"
python3 file_name.py
"""

# set Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUT_DIR = os.path.join(BASE_DIR, "Yelp_Chicago_restaurants")
os.makedirs(OUT_DIR, exist_ok=True)

INPUT_ZIP_PATH = os.path.join(BASE_DIR, "chicago_unique_zipcodes.csv")
OUTPUT_PATH = os.path.join(OUT_DIR, "yelp_chicago.csv")

API_KEY = os.getenv("YELP_FUSION_API_KEY") 
SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

if not API_KEY:
    raise ValueError("Missing Yelp API key")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


# load Chicago zipcodes
zip_df = pd.read_csv(INPUT_ZIP_PATH)
unique_zips = zip_df["gp_zipcode"].astype(str).tolist()


# collect data
yelp_records = []
seen_ids = set()  # deduplicate restaurants across zipcodes

limit = 40 # number of restaurants retrieved per API request
max_page_per_zip = 6 # pages per ZIP code; 6 * 40 = 240, matching Yelp API's maximum offset limit (240)

for zipcode in unique_zips:

    for page in range(max_page_per_zip):

        if page * limit + limit > 240: # adhere to Yelp's maximum offset
            break

        # required for Yelp Business Search API
        params = {
            "location": zipcode,
            "categories": "restaurants",
            "limit": limit,
            "offset": page * limit
        }

        response = requests.get(SEARCH_URL, headers=HEADERS, params=params,timeout=20) # make API request

        if response.status_code == 200:

            data = response.json()
            businesses = data.get("businesses", [])

            # no more results for this ZIP
            if not businesses:
                break

            new_in_page = 0
            for biz in businesses:

                bid = biz.get("id")
                if (not bid) or (bid in seen_ids):
                    continue

                seen_ids.add(bid)
                new_in_page += 1

                # select fields needed
                yelp_records.append({
                    "yelp_business_id": bid,
                    "yelp_name": biz.get("name"),
                    "yelp_display_address": " ".join(
                        biz["location"].get("display_address", [])),
                    "yelp_address1": biz["location"].get("address1"),
                    "yelp_zip_code": biz["location"].get("zip_code"),
                    "yelp_city": biz["location"].get("city"),
                    "yelp_state": biz["location"].get("state"),
                    "yelp_latitude": biz["coordinates"].get("latitude"),
                    "yelp_longitude": biz["coordinates"].get("longitude"),
                    "yelp_price": biz.get("price"),
                    "yelp_rating": biz.get("rating"),
                    "yelp_review_count": biz.get("review_count"),
                    "yelp_is_closed": biz.get("is_closed"),
                    "yelp_transactions": ",".join(biz.get("transactions", [])),
                    "yelp_categories": ",".join(
                        [c["title"] for c in biz.get("categories", [])])
                })

            print(f"ZIP {zipcode}; Retrieved {len(businesses)} businesses; New unique {new_in_page}; Total unique {len(seen_ids)}")

            # break if new page adds very few new restaurants
            if new_in_page < 3: # optimize API usage
                break

        else:
            print(f"error for ZIP {zipcode}")
            break

        time.sleep(0.2)

# final save
yelp_df = pd.DataFrame(yelp_records)
yelp_df.to_csv(OUTPUT_PATH, index=False)
print("Final unique restaurants:", yelp_df["yelp_business_id"].nunique())
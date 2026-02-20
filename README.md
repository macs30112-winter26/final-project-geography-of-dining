# Project Description
This project examines how restaurant characteristics vary across Chicago neighborhoods with different socioeconomic status (SES). Using Google Places and Yelp data mapped to community areas and linked to ACS-based income and education measures, I aggregate and visualize restaurant price levels and ranges, ratings and review volume, primary types, and operational signals to assess how neighborhood food environments align with Chicago’s socioeconomic geography.

# Research Questions
## RQ1
How are restaurant prices (price level and price range) associated with neighborhood socioeconomic status (SES), measured by median household income and educational attainment, across Chicago?
## RQ2
Beyond price, do restaurant characteristics (such as restaurant type, regular opening hours, and service offerings) as well as ratings and review volume vary systematically across Chicago neighborhoods?

# Data
This project collects restaurant data via:
- Google Places API
- Yelp Fusion API
## Chicago Data Portal – ACS 5-Year Data by Community Area (SES)
- Neighborhood SES indicators  
- https://data.cityofchicago.org/Community-Economic-Development/ACS-5-Year-Data-by-Community-Area/t68z-cikk/about_data
## Chicago Data Portal – Community Area Boundaries
- Official polygons for assigning restaurants to community areas  
- https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-Map/cauq-8yn6

# Libraries
TBA

# Repo Structure
## data
- Yelp_Chicago_restaurants – Raw and cleaned Yelp restaurant data
- Google_Place_Chicago_restaurants – Raw and cleaned Google Places restaurant data
- gp_yelp_matched.csv – Matched (raw) Google Places–Yelp merged dataset
- gp_yelp_matched_cleaned.csv – Matched (cleaned) merged dataset with engineered variables
- chicago_unique_zipcodes.csv – Chicago ZIP codes
## code
- google_place_restaurant_collector.py – Collects Chicago restaurants from the Google Places API
- yelp_restaurant_collector.py – Collects Chicago restaurants from the Yelp Fusion API
- data_clean_up.ipynb – Cleans and standardizes the Google Places and Yelp datasets
- data_merge.ipynb – Matches restaurants across platforms and produces the merged dataframe
- data_analysis.ipynb – Exploratory data analysis and downstream analysis/visualization

# Contributions
Jessica Xu

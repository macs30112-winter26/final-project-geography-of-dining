# Project Description

This project examines how restaurant characteristics vary across Chicago neighborhoods with different socioeconomic status (SES). Using Google Places and Yelp data mapped to community areas and linked to ACS-based income measures, I aggregate and visualize restaurant price levels, ratings and review volume, restaurant types, and operational features to assess how neighborhood food environments align with Chicago’s socioeconomic geography.

## Research Questions

### RQ1
How are restaurant prices (price level) associated with neighborhood socioeconomic status (SES), measured by median household income, across Chicago?

### RQ2
Do restaurant characteristics, including restaurant type, service options, hours, ratings, and review count, vary systematically across neighborhoods with different socioeconomic status?

## Key Findings

### 1. Socioeconomic Status and Restaurant Prices
- A clear SES-price gradient emerges across Chicago neighborhoods.
- Higher-income community areas tend to have higher average restaurant price levels.
- This relationship remains significant even after controlling for ratings, review volume, service features, and cuisine type.

### 2. Neighborhood Differences in Restaurant Features
- Restaurant characteristics vary systematically across neighborhoods.
- Higher-income areas show a greater concentration of formal dining features such as reservable and dine-in restaurants.

### 3. Operational Features and Price Levels
- Restaurants offering reservations tend to have higher price levels.
- Higher ratings and greater review volume are also associated with higher prices.
- In contrast, takeout availability is associated with lower price levels.

### 4. Cuisine Composition and Price Variation
- Cuisine composition differs across SES quintiles and contributes to restaurant price variation.
- Quick/Budget and Mexican restaurants are more concentrated in lower-income neighborhoods, while Mid-Range, Specialty Dining, and Other Cuisines become more prevalent in higher-income areas.
- This suggests that neighborhood SES shapes restaurant prices partly through differences in cuisine mix and overall dining diversity.

## Additional info

**Total lines of code**: 1102

**Methods and Analysis**: The project’s focus area is Descriptive Spatial Analysis and Maps. Restaurant data collected from the Google Places API are geocoded, assigned to Chicago community areas through spatial joins, and combined with ACS 5-Year SES measures to analyze and visualize how restaurant pricing and characteristics align with Chicago’s socioeconomic geography.

**Project strength**: This project integrates and cleans restaurant data from Google Places and Yelp, cross-validating the datasets to improve completeness and data quality.

# Data

### Google Places
- Collected via Google Places API

### Yelp
- Collected via Yelp Fusion API

### Chicago Data Portal
- **ACS 5-Year Data by Community Area (SES)**
  - Neighborhood SES indicators
  - Accessed via [Dataset page](https://data.cityofchicago.org/Community-Economic-Development/ACS-5-Year-Data-by-Community-Area/t68z-cikk/about_data)

- **Community Area Boundaries**
  - Official polygons for assigning restaurants to community areas
  - Accessed via [Dataset page](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-Map/cauq-8yn6)

# Libraries
- pandas==3.0.1
- Requests==2.32.5
- Shapely==2.1.2

# Repository Structure

```text
final-project-geography-of-dining/
├── data/
│   ├── Yelp_Chicago_restaurants/                # Raw and cleaned Yelp restaurant data
│   ├── Google_Place_Chicago_restaurants/        # Raw and cleaned Google Places restaurant data
│   ├── gp_yelp_matched.csv                      # Matched raw Google Places–Yelp merged dataset
│   ├── gp_yelp_matched_cleaned.csv              # Matched cleaned merged dataset with engineered variables
│   └── chicago_unique_zipcodes.csv              # Chicago ZIP codes
├── code/
│   ├── google_place_restaurant_collector.py     # Collects Chicago restaurants from the Google Places API
│   ├── yelp_restaurant_collector.py             # Collects Chicago restaurants from the Yelp Fusion API
│   ├── data_clean_up.ipynb                      # Cleans and standardizes the Google Places and Yelp datasets
│   ├── data_merge.ipynb                         # Matches restaurants across platforms and produces the merged dataframe
│   └── data_analysis.ipynb                      # Conducts exploratory data analysis and downstream analysis and visualization
├── slide/
│   ├── Geography_of_Dining_in_class.pptx        # In-class presentation slide
│   └── Geography_of_Dining_updated.pptx         # Updated presentation slide
└── README.md
```

# Demonstration Video

# Author
Jessica Xu

# AI Usage Statement
ChatGPT used only for debugging and minor modifications.


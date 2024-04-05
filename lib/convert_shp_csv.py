#!/usr/bin/env/python3

'''
Cleaning up shapefiles and exporting to CSVs.

Shapefiles obtained from MN Geospatial Commons (https://gisdata.mn.gov/),
   see readme in data directory for more information.

Usage (from lib directory): python3 convert_shp_csv.py
'''

import geopandas as gpd
import pandas as pd


# Read in shapefiles
## bikeways
bike_shp = gpd.read_file("../data/mn_geospatialcommons/bike_trails_metro_collab_2020/MetroCollaborativeTrailsBikeways.shp")
# bike_shp.info() # 43149 entries, 65 columns, 21.4+ MB
## parks
park_shp = gpd.read_file("../data/mn_geospatialcommons/parks_metro_collab_2020/MetroCollaborativeParks.shp")
# park_shp.info() # 3865 entries, 51 columns, 1.5+ MB
## buildings
build_shp = gpd.read_file("../data/mn_geospatialcommons/non_residential_building_2023/NonresidentialConstruction.shp")
# build_shp.info() # 10888 entries, 20 columns, 1.7+ MB


# Convert to pandas df
## note: not necessary but helpful to confirm geom is correctly written in CSV output
bike_df = pd.DataFrame(bike_shp)
park_df = pd.DataFrame(park_shp)
build_df = pd.DataFrame(build_shp)


# Cleaning up data (open trails/parks, relevant buildings if desired)
#    note: some "planned" trails/parks may be completed, but for simplicity only adding
#          trails which were open in 2020 since date of expected completion not provided.
#
# Open and relevant bikeways / trails
# print(bike_df.TRLSTATUS.value_counts()) # open, proposed, planned, etc.
# print(bike_df.GEN_TYPE.value_counts()) # off-street, on-street, unknown
# print(bike_df.SURFACETYP.value_counts()) # asphalt, concrete, snow, etc.
# print(bike_df.SUMMER_USE.value_counts()) # multi-use, sidewalk, bike lane, bikeable shoulder, etc.
# print(bike_df.WINTER_USE.value_counts()) # multi-use, sidewalk, bike lane, XC ski, snowshoe, etc.
## keep open trails
bike_df = bike_df[bike_df.TRLSTATUS.isin(['Open'])]
bike_df = bike_df.reset_index(drop=True)
## create boolean variables for types of bike/walking trails (specify trail types to get best results)
bike_df['SEP_BIKE_TRL'] = bike_df.GEN_TYPE.isin(['Off-Street','Unknown']) & bike_df.SUMMER_USE.isin(['Multi-Use Trail','Separated-Use Trail','Bike/Pedestrian Bridge','Cycle Track','Bike-Only Trail','Bike/Pedestrian Tunnel'])
bike_df['NONSEP_BIKE_TRL'] = bike_df.GEN_TYPE.isin(['On-Street','Unknown']) & bike_df.SUMMER_USE.isin(['Multi-Use Trail','Sharrow/Shared Lane','Bikeable Shoulder','Standard Bike Lane','Buffered Bike Lane','Bike Boulevard','Signed Bike Route','Advisory Bike Lane','Shared Bike/Bus Lane','Contraflow Bike Lane'])
bike_df['WALK_TRL'] = bike_df.GEN_TYPE.isin(['Off-Street','Unknown']) & bike_df.SUMMER_USE.isin(['Multi-Use Trail','Sidewalk','Pedestrian-Only Trail','Separated-Use Trail','Bike/Pedestrian Bridge'])
idx = bike_df[ (bike_df['SEP_BIKE_TRL'] == False) & (bike_df['NONSEP_BIKE_TRL'] == False) & (bike_df['WALK_TRL'] == False) ].index
bike_df.drop(idx, inplace=True)
bike_df = bike_df.reset_index()

## Open & free parks
# print(park_df.PARKSTATUS.value_counts()) # open, fee, proposed, etc.
park_df = park_df[park_df.PARKSTATUS.isin(['Open'])]
park_df.dropna(subset=['geometry'], inplace=True)
park_df = park_df.reset_index(drop=True)

## Relevant building codes (keeping everything for now)
# print(build_df.NONRES_TYP.value_counts()) # retail, office, schools, eat & drink, medical, public, government, etc.
### Extract common grocery stores (add in Target manually, usual has a grocery section)
gmask = build_df.BLDG_DESC.str.contains('Grocery') | build_df.BLDG_NAME.str.contains('Target')
build_df.loc[gmask , 'NONRES_TYP'] = 'Grocery'
### Extract hospitals, combine to medical delineation
mfmask = build_df.NONRES_TYP.isin(['Medical--Commercial','Hospitals and Nursing Homes'])
build_df.loc[mfmask , 'NONRES_TYP'] = 'Medical Facilities'
### Keep only relevant categories
build_df = build_df[build_df.NONRES_TYP.isin(['Grocery','Schools','Eating and Drinking Establishments','Arts Entertainment and Recreation','Religious','Medical Facilities','Transit'])]
build_df = build_df.reset_index()

# Export as CSV file
bike_df.to_csv("../data/csv_shapefiles/bikeways.csv", index=False)
park_df.to_csv("../data/csv_shapefiles/parks.csv", index=False)
build_df.to_csv("../data/csv_shapefiles/buildings.csv", index=False)

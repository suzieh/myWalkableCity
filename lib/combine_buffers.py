#!/usr/bin/env/python3

'''
Combining Buffers of like objects (like connecting trails, overlapping park buffers, etc.)
'''

import argparse
import pandas as pd
import geopandas as gpd
from shapely import wkt
import itertools

filepath = '../data/buffers_800t_1000p_1000b/bikeways_buffers.csv'  # manually enter file names - experimenting with faster geometries
parkfp = '../data/buffers_800t_1000p_1000b/parks_buffers.csv'
buildingfp = '../data/buffers_800t_1000p_1000b/buildings_buffers.csv'

# Helper function : Intersection of GeoSeries
def group_union(mygdf):
    # list format of geometries
    geoms = mygdf['geometry'].tolist()
    # intersections for every combination, if intersecting
    intersection_iter = gpd.GeoDataFrame(gpd.GeoSeries([poly[0].union(poly[1]) for poly in itertools.combinations(geoms, 2) if poly[0].intersects(poly[1])]), columns=['geometry'])
    # (optional) write to file
    # intersection_iter.to_file("data/intersection_iter.shp")
    union_iter = intersection_iter.unary_union
    return union_iter



##### Bikeways #####
# Geopandas dataframe
df = pd.read_csv(filepath, delimiter=",", header=0, dtype=str, lineterminator='\n')
df.SEP_BIKE_TRL = df.SEP_BIKE_TRL.map({'True': True, 'False': False})
df.NONSEP_BIKE_TRL = df.NONSEP_BIKE_TRL.map({'True': True, 'False': False})
df.WALK_TRL = df.WALK_TRL.map({'True': True, 'False': False})
df['geometry'] = df['geometry'].apply(str) # ensure str before conversion
df['geometry'] = df['geometry'].apply(wkt.loads) # reading from "Well Known Text" format
gdf = gpd.GeoDataFrame(df, crs="epsg:26915").set_geometry('geometry') # setting coordinate reference to NAD 83

# Groups - must have like attributes in SEP_BIKE_TRL, NONSEP_BIKE_TRL, WALK_TRL
## separated trail only (144)
sep_gdf = gdf.loc[gdf.SEP_BIKE_TRL & ~gdf.WALK_TRL]
## separated & walking trail (11259)
combo_gdf = gdf.loc[gdf.SEP_BIKE_TRL & gdf.WALK_TRL]
## nonseparated trail only (2331)
non_gdf = gdf.loc[gdf.NONSEP_BIKE_TRL]
## walk only (1289)
walk_gdf = gdf.loc[gdf.WALK_TRL & ~gdf.SEP_BIKE_TRL]

# Output to a combined file with these multi-polygons per group
new_gdf = gdf.iloc[0:4].copy(deep=False)
new_gdf.id = [144,11259,2331,1289]
new_gdf.name = ['separated bike','shared trail','nonseparated bike','walking only trail']
new_gdf.SEP_BIKE_TRL = [True, True, False, False]
new_gdf.NONSEP_BIKE_TRL = [False, False, True, False]
new_gdf.WALK_TRL = [False, True, False, True]
new_gdf.geometry = [group_union(sep_gdf), group_union(combo_gdf), group_union(non_gdf), group_union(walk_gdf)] # takes a long time!!
## writing out to file
new_gdf.to_csv('../data/buffers_800t_1000p_1000b/combined_bikeway_buffers.csv', index=False)



##### Parks #####
# Geopandas dataframe
df = pd.read_csv(parkfp, delimiter=",", header=0, dtype=str, lineterminator='\n')
df['geometry'] = df['geometry'].apply(str) # ensure str before conversion
df['geometry'] = df['geometry'].apply(wkt.loads) # reading from "Well Known Text" format
gdf = gpd.GeoDataFrame(df, crs="epsg:26915").set_geometry('geometry') # setting coordinate reference to NAD 83

# Create one combined geometry
new_gdf = gdf.iloc[0:1].copy(deep=False)
new_gdf.id = 0
new_gdf['name'] = 'parks'
new_gdf['geometry'] = group_union(gdf)
## writing out to file
new_gdf.to_csv('../data/buffers_800t_1000p_1000b/combined_park_buffers.csv', index=False)



##### Buildings #####
# Geopandas dataframe
df = pd.read_csv(buildingfp, delimiter=",", header=0, dtype=str, lineterminator='\n')
df['geometry'] = df['geometry'].apply(str) # ensure str before conversion
df['geometry'] = df['geometry'].apply(wkt.loads) # reading from "Well Known Text" format
gdf = gpd.GeoDataFrame(df, crs="epsg:26915").set_geometry('geometry') # setting coordinate reference to NAD 83

# Seven groups of buildings, combine per group
btypes = ['Schools', 'Medical Facilities', 'Eating and Drinking Establishments', 'Arts Entertainment and Recreation', 'Religious', 'Grocery', 'Transit']

# Create combined geometries per group
new_gdf = gdf.iloc[0:len(btypes)].copy(deep=False)
for i in range(len(btypes)):
    new_gdf.loc[i,'id'] = i
    new_gdf.loc[i, 'name'] = btypes[i]
    new_gdf.loc[i, 'NONRES_TYP'] = btypes[i]
    new_gdf.loc[i, 'geometry'] = group_union(gdf.loc[gdf.NONRES_TYP == btypes[i]])
## writing out to file
new_gdf.to_csv('../data/buffers_800t_1000p_1000b/combined_building_buffers.csv', index=False)






import plotly.express as px
import pyproj
from plotly.offline import plot
mydf = pd.read_csv('../data/buffers_800t_1000p_1000b/combined_bikeway_buffers.csv',delimiter=",", header=0, dtype=str, lineterminator='\n').drop(['SEP_BIKE_TRL','NONSEP_BIKE_TRL','WALK_TRL'], axis=1)
mydf1 = pd.read_csv('../data/buffers_800t_1000p_1000b/combined_park_buffers.csv',delimiter=",", header=0, dtype=str, lineterminator='\n')
mydf2 = pd.read_csv('../data/buffers_800t_1000p_1000b/combined_building_buffers.csv',delimiter=",", header=0, dtype=str, lineterminator='\n').drop('NONRES_TYP', axis=1)
combined = pd.concat([mydf, mydf1, mydf2])
combined['geometry'] = combined['geometry'].apply(str)
combined['geometry'] = combined['geometry'].apply(wkt.loads)
combined = gpd.GeoDataFrame(combined, crs="epsg:26915").set_geometry('geometry')
combined = combined.reset_index()

mycopy = combined.copy(deep=False)
mycopy.to_crs(epsg=4326, inplace=True)

# gpd.GeoSeries(combined['geometry'].apply(str).apply(shapely.wkt.loads)).__geo_interface__

plty = px.choropleth_mapbox(
    geojson = mycopy['geometry'],
    locations = mycopy.index,
    color = ['trail','trail','trail','trail','park','building','building','building','building','building','building','building'],
    color_discrete_sequence = ['blue','green','yellow'],
    opacity = 0.3
).update_layout(
    mapbox={"style": "carto-positron", "center": {"lon": -93, "lat": 45}, "zoom": 8}
)
plot(plty, auto_open=True)





from matplotlib.lines import Line2D
import matplotlib
import matplotlib.pyplot as plt
import contextily as cx
my_colors = ['blue','green','orange']
my_names = ['trails','parks','buildings']

combined['col_grp'] = ['blue','blue','blue','blue','green','yellow','yellow','yellow','yellow','yellow','yellow','yellow']

my_legend = [Line2D([0], [0], color=my_colors[i], lw=4) for i in range(len(my_colors))]

fig, ax = plt.subplots() # change size here if needed?
combined.plot(ax=ax, color=combined['col_grp'], aspect=1, alpha=0.2)
ax.legend(my_legend, my_names)
cx.add_basemap(ax, crs=combined.crs, source=cx.providers.CartoDB.Positron)
plt.title('Twin Cities Areas Meeting Criteria')









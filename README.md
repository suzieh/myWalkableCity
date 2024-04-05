# myWalkableCity

Spaital data visualizes the "walkable cities" within the Twin Cities, MN, USA.

Walkable cities are a city planning concept, where within a walkable distance of their home a person might have access to parks, paths, and necessities such as groceries and medical care. This Dash gives an approximate visualization of which areas are more densely populated with necessities of your choosing.

All data was obtained from the publicly available Minnesota Geospatial Commons.


## Installation

This reposoitory assumes running Python3. Please then also install all requirements:

`pip install -r requirements.txt`


## Deployment

The [MyWalkableCity application](https://mywalkablecity.onrender.com/) is deployed with Render (note on 0.1 CPU plan, can be slow to update given data sizes).


## Description of other Python scripts

Other scripts used in deployment of this application-passion-project can be found in the lib/ directory.

*convert_shp_csv.py*: Converting shapefiles provided by MN Geospatial Commons to CSV format for simpler pandas manipulation.

*resize_shapefile.py*: Remove unneeded records (parks/trails not yet open) to reduce the size of shapefiles. Done prior to uploading to GitHub due to storage limits.

*generate_buffers.py*: Using geopandas to create "buffers" of designated sizes around path, park, and building geometries. Buffers are polygons representing the area around these objects, e.g. a polygon representing the area 800 meters from a bike path.

*combine_buffers.py*: Combine Buffers represented as Polygons into MultiPolygons for speed of rendering. This also combines overlapping buffers of the same type (i.e. same type of trails are combined into one cohesive trail).


# Obtaining publicly available data from Minnesota Geospatial Commons

Visit the [MN Geospatial Commons site](https://gisdata.mn.gov/) for more data / info. You'll find specific links to the 

----------

## Bikeways

I am an avid cyclist, both for commuting and recreation. It was important to me to be in close proximity to designated bike paths as well as walking/running trails in the metro Twin Cities.

I obtained this dataset from the [Metro Trails and Bikeways Collaborative](https://gisdata.mn.gov/dataset/us-mn-state-metrogis-trans-metro-colabtiv-trails-bike), last updated in February 2020.


## Buildings (Non-residential)

[Non-residential building permits](https://gisdata.mn.gov/dataset/us-mn-state-metc-struc-non-res-construction) from the Metro area give us a sense of accessibility of groceries, schools, healthcare, leisure, and more. Last updated in October 2023.


## Parks

To determine proximity to greenspaces, we can evaluate based on [metro area parks](https://gisdata.mn.gov/dataset/us-mn-state-metrogis-bdry-metro-colabtiv-parks). Last updated in February 2020.


## Possible expansions of the program (with MN GeoSpatial Commons)

One could also obtain shapefile for areas one wishes to avoid, such as proximity to noisy and pollutant-heavy highways or airports. MNDOT has a number of shapefiles, would need to adjust the program to negate proximity to these items (subtract these boundaries from the results).

----------

# Changing the size of the bikeways file

Due to data storage limits, I decided to shrink the size of the bikeways shapefile using the pyshp Python package.

Full code included below, run interactively on the python terminal

```
import geopandas as gpd
import pandas as pd
import shapefile

# Note the temporary directory location (shp_trans_metro_colabtiv_trails_bike) was deleted after this was completed.

# Loading original bikeways shapefile as a dataframe for indexing
bike_shp = gpd.read_file("../data/mn_geospatialcommons/shp_trans_metro_colabtiv_trails_bike/MetroCollaborativeTrailsBikeways.shp")
bike_df = pd.DataFrame(bike_shp)
mask = bike_df.TRLSTATUS.isin(['Open'])
mask_indices = mask[mask].index.values
m_i = [int(idx) for idx in mask_indices]


# Reading mode for the original shapefile
e = shapefile.Reader("../data/mn_geospatialcommons/shp_trans_metro_colabtiv_trails_bike/MetroCollaborativeTrailsBikeways.shp")
sr = [e.shapeRecords()[idx] for idx in m_i]
# note: creation of sr takes a while (several minutes)


# Writing out to a new shapefile
with shapefile.Writer(r"../data/mn_geospatialommons/test") as w:
    w.fields = e.fields[m_i]
    for feature in sr:
        w.record(*feature.record)
        w.shape(feature.shape)
```
#!/usr/bin/env/python3

'''
Attempting to resize shapefile from MN Geospatial Commons so we can be under 100MB limit for GitHub.

Usage : One-time usage , run inside of the 'lib' directory, or interactive python : python3 resize_shapefile.py
'''
import geopandas as gpd

# Read in the shapefile for bikes/trails (the only large one)
bike_gdf = gpd.read_file("../data/mn_geospatialcommons/bike_trails_metro_collab_2020/MetroCollaborativeTrailsBikeways.shp")

# Delete unneeded entries & columns in a copy
copy = bike_gdf.copy()
drop_idx = copy[ copy['TRLSTATUS'] != 'Open' ].index  # 7126 of 43149 entries will be dropped
drop_col = ['FED_SYS','NTL_SYS', 'STATE_SYS', 'REG_SYS', 'CTY_SYS', 'LOC_SYS', 'TRBL_SYS',
			'PRVTE_SYS', 'PROT_SYS','SIDESTREET', 'PRD_SPEED', 'RTE_SPEED', 'DIRECTION',
		    'RBTN', 'DIFFRTG', 'LANDOWNER', 'PARL_RD', 'ALTPARLRD', 'YEAR_PRGRM',
		    'ACQSOURCE', 'ACQMETHOD', 'ACQCOMMENT', 'LWCFPROT', 'OTHERPROT', 'RESPRTCMNT',
		    'SRTS_ZONE', 'LIGHTING', 'DATAAUTHOR', 'EDITED_BY', 'EDITED_DT', 'CREATED_BY']
copy.drop(drop_idx, axis=0, inplace=True) # 36023 records remain (from 43149)
copy.drop(drop_col, axis=1, inplace=True) # 34 columns remain (from 65)

# Write out again
copy.to_file("../data/mn_geospatialcommons/bike_trails_metro_collab_2020/MetroCollaborativeTrailsBikeways.shp")
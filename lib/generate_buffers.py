#!/usr/bin/env/python3

'''
Creating Buffers from geometries for buildings (points), trails(linestring, multilinestring), parks (polygon, multipolygon).

Usage: python3 generate_buffers.py -t [trail_buffer_meters] -p [park_buffer_meters] -b [building_buffer_meters]
    optional arguments for output: -o [output_directory] --no_write_out
    optional flag(s) to visualize: --vis_all --vis_ex_buff
'''

import argparse
import sys
import os
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, LineString, MultiLineString, Polygon, MultiPolygon
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import contextily as cx
from shapely.ops import linemerge


def main():
    # Initialize the parser
    parser = argparse.ArgumentParser(description='Generate buffers for the csv_shapefiles data.')
    reqparse = parser.add_argument_group("required arguments")
    reqparse.add_argument('-t','--trail_buff', required=True, default=400, type=int,
        help='Buffer size (meters) for bike/walking trails. [default: 400]')
    reqparse.add_argument('-p','--park_buff', required=True, default=800, type=int,
        help='Buffer size (meters) for parks. [default: 800]')
    reqparse.add_argument('-b','--building_buff', required=True, default=800, type=int,
        help='Buffer size (meters) for buildings. [default: 800]')
    reqparse.add_argument('-i','--input', required=True, default="../data/csv_shapefiles/", type=str,
        help='Directory in which to find CSV shapefiles. [default: ../data/csv_shapefiles/]')
    parser.add_argument('-o','--out', required=False, default='.', type=str,
        help='Directory to write the buffer files, directory must already exist. [default: ../data/]')
    parser.add_argument('--no_write_out',required=False, action='store_true',
        help='Do not write out buffers to file.')
    parser.add_argument('--vis_all', required=False, action='store_true',
        help='Visualize all the geoms (trails, parks, buildings).')
    parser.add_argument('--vis_ex_buff', required=False, action='store_true',
        help='Visualize an example park, building, and bikeway with their buffers.')

    # Verification: if no arguments print help message
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Obtain arguments from command line
    args = parser.parse_args()

    # CSV to GeoPandas dataframes
    bike_gdf = read_csv_to_gpd(os.path.join(args.input, 'bikeways.csv'),'TRAILNAME')
    park_gdf = read_csv_to_gpd(os.path.join(args.input, 'parks.csv'),'PARKNAME')
    build_gdf = read_csv_to_gpd(os.path.join(args.input, 'buildings.csv'),'BLDG_NAME')

    # Create Buffers
    ## note: passing values with [:] so gdfs are unaffected (for visualizations)
    buff_bike = create_buffers(bike_gdf[['id','name','SEP_BIKE_TRL','NONSEP_BIKE_TRL','WALK_TRL','geometry']].copy(), args.trail_buff)
    buff_park = create_buffers(park_gdf[['id','name','geometry']].copy(), args.park_buff)
    buff_build = create_buffers(build_gdf[['id','name','NONRES_TYP','geometry']].copy(), args.building_buff)

    # Visualizations (if requested)
    if args.vis_all:
        visualize([buff_bike,buff_park,buff_build], ["trail","park","building"], ["blue","green","orange"])
    if args.vis_ex_buff:
        ## Geometries (Stone Arch Bridge, West River Road, Guthrie Theatre, Mill Ruins Park)
        west_river = [9321,6521,1473,3497,3697,4116,12228]  # West River Road, Stone Arch Bridge  # 9325,6524,1475,3499,3699,4118,12233
        geom = bike_gdf.loc[[west_river[0]]]  # was [22573,19019,12609*,15185,15442,15960,26171]
        geom['geometry'] = linemerge(MultiLineString([bike_gdf.geometry[i] for i in west_river]))
        geom2 = park_gdf[park_gdf.name.isin(['Mill Ruins Park'])]  # Mill Ruins Park
        geom3 = build_gdf[build_gdf.id.isin(['3450'])]  # Guthrie Theater
        geom_all = pd.concat([geom, geom2, geom3])
        ## Corresponding Buffers
        b = buff_bike.loc[[west_river[0]]]  # West River Road, Stone Arch Bridge
        tmp = gpd.GeoSeries([buff_bike.geometry[i] for i in west_river])
        b['geometry'] = tmp.unary_union  # combine into one geometry
        b2 = buff_park[buff_park.name.isin(['Mill Ruins Park'])]  # Mill Ruins Park
        b3 = buff_build[buff_build.id.isin(['3450'])]  # Guthrie Theater
        buff_all = pd.concat([b, b2, b3])
        ## Pass to vis_example
        vis_example(geom_all, buff_all, True, 'Example Geoms & Buffers')

    # Write out buffers to new file
    ## note minimal information besides buffer geoms in these files since other info already contained in csv_shapefiles
    if args.no_write_out == False:
        # Write out to csv
        buff_bike.to_csv(os.path.join(args.out, 'bikeways_buffers.csv'), index=False)
        buff_park.to_csv(os.path.join(args.out, 'parks_buffers.csv'), index=False)
        buff_build.to_csv(os.path.join(args.out, 'buildings_buffers.csv'), index=False)


def read_csv_to_gpd(filepath, name_col):
    '''
    Read in the csv file, convert to GeoPandas dataframe
    '''
    # Reading in and updating geometry to NAD 83 CRS
    df = pd.read_csv(filepath, delimiter=",", header=0, dtype=str, lineterminator='\n')
    df['geometry'] = df['geometry'].apply(str) # ensure str before conversion
    df['geometry'] = df['geometry'].apply(wkt.loads) # reading from "Well Known Text" format
    gdf = gpd.GeoDataFrame(df, crs="epsg:26915").set_geometry('geometry') # setting coordinate reference to NAD 83
    
    # Make some common names (for visualizations)
    gdf.rename(columns={gdf.columns[0]:'id'}, inplace=True)
    gdf['name'] = gdf[name_col]
    return gdf


def combine_df(df_list):
    '''
    Helper function for visualization : Combine key components of the dataframes
    '''
    main_cols = ['id','name','col_grp','grp_name','geometry']
    main_df = gpd.GeoDataFrame(columns=main_cols)
    for df in df_list:
        df = df[main_cols]
    return gpd.pd.concat(df_list[::-1], ignore_index=True)


def create_buffers(mygdf, radius):
    '''
    Convert the geometries into buffers of the provided size (radius in meters)
    '''
    mygdf.geometry = gpd.GeoSeries(mygdf.geometry).buffer(radius)
    return mygdf


def visualize(buff_list, buff_names, colors):
    '''
    Visualization of all the geometries
    '''
    # combine the dataframes, one color per dataframe to signal a distinct 'type'
    for i in range(len(buff_list)):
        buff_list[i]['col_grp'] = colors[i]
        buff_list[i]['grp_name'] = buff_names[i]
    joined = combine_df(buff_list)
    
    # legend
    custom_legend = [Line2D([0], [0], color=colors[i], lw=4) for i in range(len(colors))]

    # generate plot
    fig, ax = plt.subplots(figsize = (10,10))
    joined.plot(ax=ax, color=joined['col_grp'], aspect=1, alpha=0.4)
    ax.legend(custom_legend, buff_names)
    cx.add_basemap(ax, crs=joined.crs, source=cx.providers.CartoDB.Positron)
    plt.title('Buildings, Trails, Parks in the Twin Cities')
    plt.show()
    return None


def vis_example(geoms, buffs = None, with_buff = False, mytitle = 'Example Geoms & Buffers'):
    '''
    Visualization of just a few designated geoms and buffers
    '''
    # colors (bike, park, building)
    my_colors = ['blue','green','orange']
    
    # legend
    my_legend = [Line2D([0], [0], color=my_colors[i], lw=4) for i in range(len(my_colors))]
    legend_names = ['River Trail & Stone Arch Bridge','Mill Ruins Park','Guthrie Theatre']

    # generate plot
    fig, ax = plt.subplots(figsize = (5,5))
    if (with_buff):
        buffs.plot(ax=ax, color=my_colors, alpha=0.2)
    geoms.plot(ax=ax, color=my_colors, alpha=1, linewidth=3)
    ax.legend(my_legend, legend_names, loc='upper right')
    cx.add_basemap(ax, crs=geoms.crs, source=cx.providers.CartoDB.Positron)
    plt.title(mytitle)
    plt.show()
    return None


if __name__ == '__main__':
    main()

#!/usr/bin/env/python3

'''
Dash for interactive plot, hosted by Render using gunicorn
'''

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
pd.options.mode.chained_assignment = None
import geopandas as gpd
from shapely import wkt
import plotly.express as px
import pyproj


# Stylesheet for Dash
external_stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] # stylesheet for CSS code from codepen


# Bring in the buffers datasets (buffer, trail_type, building_type)
trail = pd.read_csv('data/buffers_800t_1000p_1000b/combined_bikeway_buffers.csv', header=0)
park = pd.read_csv('data/buffers_800t_1000p_1000b/combined_park_buffers.csv', header=0)
building = pd.read_csv('data/buffers_800t_1000p_1000b/combined_building_buffers.csv', header=0)


# Colors & Legend names for plotting
my_colors = ['blue','orange','green']
my_names = ['Trails','Buildings','Parks']


# Helper function : Combining datasets & setting geometry
def combine_df(df_list, t_list, b_list, include_parks=True):
    # Reduce trails dataset - keep true values for the categories
    df_list[0] = df_list[0].loc[df_list[0][t_list].any(axis='columns')] # reduce trails
    # Reduce building dataset
    df_list[1] = df_list[1].loc[df_list[1].NONRES_TYP.isin(b_list)]
    # Add color columns, reduce to these common columns
    main_cols = ['id','name','col_grp','grp_name','geometry']
    for i in range(len(df_list)):
        df_list[i]['col_grp'] = my_colors[i]
        df_list[i]['grp_name'] = my_names[i]
    # Combine same columns
    if include_parks:
        out = pd.concat(df_list, ignore_index=True)
    else:
        out = pd.concat([df_list[0], df_list[1]], ignore_index=True)
    # Geometry format
    out['geometry'] = out['geometry'].apply(str) # ensure str before conversion
    out['geometry'] = out['geometry'].apply(wkt.loads) # reading from "Well Known Text" format
    out = gpd.GeoDataFrame(out, crs="epsg:26915").set_geometry('geometry') # setting coordinate reference to NAD 83
    return out


# Initiate the Dash app & server
app = dash.Dash(__name__, external_stylesheets=external_stylesheet)
server = app.server


# Organize the Dash app
app.layout = html.Div([
    html.H2('My Walkable / Bikeable City'),
    html.Div([

        html.Div([
            html.H3('Choose Elements to View'),
            html.Label('Trails:'),   # trail_list
            dcc.Checklist(
                id='trail_list',
                options=[
                {'label': 'Off-Street Paths', 'value': 'SEP_BIKE_TRL'},
                {'label': 'On-Street Paths', 'value': 'NONSEP_BIKE_TRL'},
                {'label': 'Walking Paths', 'value': 'WALK_TRL'} ],
                value=['SEP_BIKE_TRL','WALK_TRL']
            ),
            html.Br(),

            html.Label('Parks:'),   # park_drop
            dcc.Dropdown(
                id='park_drop',
                options=[{'label': 'Yes', 'value': True},
                {'label': 'No', 'value': False}], # make the label and value identical to the column names
                value=True # default value
            ),
            html.Br(), 
            
            html.Label('Buildings:'),   # building_list
            dcc.Checklist(
                id='building_list', 
                options=[{'label': x, 'value': x} for x in building.NONRES_TYP.unique()],
                value=['Grocery','Eating and Drinking Establishments']
            ),
        ], className="six columns"),
        
        html.Div([
            html.H3('Minneapolis / St. Paul Walkable Areas'),
            dcc.Graph(id='map_graph'),
            html.P('Find "walkable cities" within the Twin Cities! Overlapping areas of blue (trails), green (parks), and orange (structures) are locations walking distance from all these resources. Trails are within 800 meters, parks and buildings within 1000 meters.')
        ], className="six columns", style={"border":"2px black solid",'padding': '10px'})
    
    ], className="row")
], style={'padding': '10px'})


# Create our figure given provided information
@app.callback(
    Output('map_graph', 'figure'),
    Input('trail_list', 'value'),
    Input('park_drop', 'value'),
    Input('building_list', 'value'))

# Plotting and combining datasets
def update_output(trail_l, park_d, building_l):
    # dataframe to be plotted - intersections of the contents we have added via dropdown/checklists
    combined = combine_df([trail, building, park], trail_l, building_l, park_d)
    combined = combined.reset_index()
    combined.to_crs(epsg=4326, inplace=True)


    # plotly choropleth graph
    plty = px.choropleth_mapbox(
        geojson = combined['geometry'],
        locations = combined.index,
        color = combined['grp_name'],
        color_discrete_sequence = my_colors,
        opacity = 0.2
    ).update_layout(
        mapbox = {"style": "carto-positron", "center": {"lon": -93.2, "lat": 44.95}, "zoom": 8},
        hovermode = False
    ).update_traces(marker_line_width=0)
    
    # OLD : generate figure with matplotlib (slow on Dash)
    # my_legend = [Line2D([0], [0], color=my_colors[i], lw=4) for i in range(len(my_colors))]
    # fig, ax = plt.subplots()
    # combined.plot(ax=ax, color=combined['col_grp'], aspect=1, alpha=0.2)
    # ax.legend(my_legend, my_names)
    # cx.add_basemap(ax, crs=combined.crs, source=cx.providers.CartoDB.Positron)
    # plt.title('Twin Cities Areas Meeting Criteria')

    # return the figure
    return plty


# Run the server
if __name__ == '__main__':
    app.run_server(debug=False)

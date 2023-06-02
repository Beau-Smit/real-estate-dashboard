# Can use sqlite3 to mimic a remote database on disk
# https://docs.python.org/3.8/library/sqlite3.html

import re
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from snowflake.snowpark import Session
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import map_functions as maps
import walk_score

st.set_page_config(layout="wide")

st.title("Property Dashboard")

# https://towardsdatascience.com/how-to-connect-streamlit-to-snowflake-b93256d80a40


# Establish Snowflake session
@st.cache_resource()
def create_session():
    # client_session_keep_alive = true
    return Session.builder.configs(st.secrets["snowflake"]).create()

session = create_session()

# Load data table
@st.cache_data
def load_data(table_name):
    # table = session.table(table_name)
    table = session.sql(f"select * from {table_name}").collect()
    df = pd.DataFrame(table)
    return df

@st.cache_data
def get_property_coordinates(address):
    # get geographic coordinates
    geolocator = Nominatim(user_agent="beau.h.smit@gmail.com")
    location = geolocator.geocode(address)
    LAT, LON = location.latitude, location.longitude

    return LAT, LON

@st.cache_data
def get_points_nearby(LAT, LON, map_items):

    if len(map_items) == 0:
        return pd.DataFrame()
    
    table_name = 'REAL_ESTATE.LOCATIONS.POINTS'
    query_filter = str(map_items).strip('][')
    table = session.sql(f"select * from {table_name} where SOURCE in ({query_filter})").collect()
    df_location = pd.DataFrame(table)

    # exclude locations far from property
    lat_min = LAT - 0.02
    lat_max = LAT + 0.02
    lon_min = LON - 0.03
    lon_max = LON + 0.03

    # limit the markers on the map
    df_location_map = df_location.loc[
        df_location.SOURCE.isin(
            # TODO: need bar names, not business names
            map_items
        )
        & (df_location.LATITUDE.between(lat_min, lat_max))
        & (df_location.LONGITUDE.between(lon_min, lon_max)),
        :,
    ]

    return df_location_map


@st.cache_data
def get_area_data(LAT, LON):

    # TODO: config
    table_name = 'REAL_ESTATE.LOCATIONS.SHAPES'
    table = session.sql(f"select * from {table_name}").collect()
    df_shape_data = pd.DataFrame(table)

    property_coordinates = gpd.GeoDataFrame(
        {"geometry": [Point(LON, LAT)]}, crs="EPSG:4326"
    )
    
    df_shape_data['GEOMETRY'] = gpd.GeoSeries.from_wkt(df_shape_data['GEOMETRY'])
    geo_df_shape_data = gpd.GeoDataFrame(df_shape_data, geometry='GEOMETRY')

    # what is the zoning?
    zoning = gpd.sjoin(
        property_coordinates,
        geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "zoning"]
    )["LABEL"][0]

    # which ward is it in?
    ward = gpd.sjoin(
        property_coordinates,
        geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "ward"]
    )["LABEL"][0]

    # which neighborhood is it in?
    neighborhood = gpd.sjoin(
        property_coordinates,
        geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "neighborhood"]
    )["LABEL"][0]

    # which school district is it in?
    hs = gpd.sjoin(
        property_coordinates,
        geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "high_schools"]
    )["LABEL"][0]

    # is this property in ADU area?
    adu_ind = (
        gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "ADU"]
        ).shape[0]
        > 0
    )

    # is this property in a mobility zone?
    mobility_ind = (
        gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "mobility_areas"]
        ).shape[0]
        > 0
    )

    # is this property in an enterprise zone?
    enterprise_ind = (
        gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "enterprise_zone"]
        ).shape[0]
        > 0
    )

    return zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind

@st.cache_resource
def build_map(LAT, LON, df_location_map):

    # TODO: move to config
    # I think it is only using these icons: https://fontawesome.com/v4/icons/
    # color choices: ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue',
    # 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
    source_dict = {
        "liquor": {"color": "orange", "icon": "glass"},
        "divvy": {"color": "blue", "icon": "bicycle"},
        "murals": {"color": "pink", "icon": "paint-brush"},
        "EV_chargers": {"color": "darkgreen", "icon": "bolt"},
        "landmarks": {"color": "gray", "icon": "bank"},
        "L": {"color": "darkblue", "icon": "subway"},
        "grocery": {"color": "green", "icon": "shopping-cart "},
        "park_art": {"color": "lightred", "icon": "tree"},
        "farmers_market": {"color": "lightgreen", "icon": "leaf"},
        "hospitals": {"color": "red", "icon": "h-square"},
        "metra": {"color": "purple", "icon": "train"},
    }

    # Create a Map instance for Chicago
    m = folium.Map(location=[LAT, LON], zoom_start=16)
    
    # add marker for the property of interest
    maps.add_map_marker(
        m, lat=LAT, lon=LON, name="property", color="black", icon="home"
    ).add_to(m)

    # add circles for distance reference around property
    maps.add_map_circle(
        m, lat=LAT, lon=LON, radius=800
    )  # 800 meters = 0.5 miles
    maps.add_map_circle(
        m, lat=LAT, lon=LON, radius=1600
    )  # 800 meters = 1 miles

    feature_group = folium.FeatureGroup("Locations")

    for _, row in df_location_map.iterrows():
        feature_group.add_child(
            maps.add_map_marker(
                m,
                lat=row["LATITUDE"],
                lon=row["LONGITUDE"],
                name=row["LABEL"],
                color=source_dict[row["SOURCE"]]["color"],
                icon=source_dict[row["SOURCE"]]["icon"],
            )
        )

    # Change the map style
    # m.add_tile_layer(tiles='Stamen Toner', name='Stamen Toner')

    m.add_child(feature_group)

    return m

if 'address' not in st.session_state:
    st.session_state['address'] = ''
if 'map_items' not in st.session_state:
    st.session_state['map_items'] = []

address = st.text_input("Enter Address: ")

if address:
    st.session_state['address'] = address


if st.session_state['address'] != '':

    # https://docs.streamlit.io/library/api-reference/layout/st.sidebar
    with st.sidebar:
        
        st.header('Include in Map:')

        all_map_items = [
            'L', 
            'metra', 
            'divvy', 
            'hospitals', 
            'grocery', 
            'landmarks', 
            'murals', 
            'park_art', 
            'liquor', 
            'EV_chargers', 
            # 'licenses', 
            # 'current_licenses', 
            # 'permits', 
            ]
        
        map_items = []

        # https://docs.streamlit.io/library/api-reference/widgets/st.checkbox
        for item in all_map_items:
            if st.checkbox(item):
                map_items.append(item)
    
    # geocode the address
    LAT, LON = get_property_coordinates(address)

    zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind = get_area_data(LAT, LON)

    # limit the markers on the map
    # TODO: could we hold the data in memory? then just filter
    # or is the cache already doing that. need to profile
    df_location_map = get_points_nearby(LAT, LON, map_items)

    # make walk score request
    # walk, transit, bike = walk_score.get_walk_score_from_address(address, st.secrets["walkscore"]["walk-score-key"])
    walk, transit, bike = walk_score.get_walk_score_from_coord(LAT, LON, st.secrets["walkscore"]["walk-score-key"])

    m = build_map(LAT, LON, df_location_map)

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label = "walk score",
        value = walk,
    )
    col2.metric(
        label = "transit score",
        value = transit,
    )
    col3.metric(
        label = "bike score",
        value = bike,
    )

    st.divider()

    # create two columns for charts
    fig_col1, fig_col2 = st.columns(2)

    with fig_col1:
        
        st.header("What's nearby?")
        fig = st_folium(m, width=725)

        st.text("Circles represent 12 and 25 minute walk approximately.")
        
        st.text("Download the map for better performance. Especially if there are many map markers.")
        btn = st.download_button(
            label = "Download",
            data = m._repr_html_(),
            file_name = f"{re.sub('[^a-zA-Z0-9]', '_', address)}.html",
            )
    
    with fig_col2:
        st.header("Property Details")

        col1, col2 = st.columns(2)
        col1.metric(
            label="Neighborhood",
            value=neighborhood,
        )
        col2.metric(
            label="Ward",
            value=ward,
        )

        col1, col2 = st.columns(2)
        col1.metric(
            label="Zoning",
            value=zoning,
        )
        col2.metric(
            label="ADU Area",
            value=adu_ind,
        )

        col1, col2 = st.columns(2)
        col1.metric(
            label="Mobility Area",
            value=mobility_ind,
        )
        col2.metric(
            label="Enterprise Zone",
            value=enterprise_ind,
        )

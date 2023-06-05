# Can use sqlite3 to mimic a remote database on disk
# https://docs.python.org/3.8/library/sqlite3.html

import os, re
import json
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

# config for map icons
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, "r") as f:
    config = json.loads(f.read())

st.set_page_config(layout="wide")

st.title("Chicago Property Dashboard")


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
def get_points_nearby(LAT, LON):
    
    table = session.sql(f"select * from {config['geocoordinates_table']}").collect()
    df_location = pd.DataFrame(table)

    # exclude locations far from property
    lat_min = LAT - 0.02
    lat_max = LAT + 0.02
    lon_min = LON - 0.03
    lon_max = LON + 0.03

    # limit the markers on the map
    df_location_map = df_location.loc[
        (df_location.LATITUDE.between(lat_min, lat_max))
        & (df_location.LONGITUDE.between(lon_min, lon_max)),
        :,
    ]

    return df_location_map


@st.cache_data
def get_area_data(LAT, LON):

    table = session.sql(f"select * from {config['shapes_table']}").collect()
    df_shape_data = pd.DataFrame(table)

    property_coordinates = gpd.GeoDataFrame(
        {"geometry": [Point(LON, LAT)]}, crs="EPSG:4326"
    )
    
    df_shape_data['GEOMETRY'] = gpd.GeoSeries.from_wkt(df_shape_data['GEOMETRY'])
    geo_df_shape_data = gpd.GeoDataFrame(df_shape_data, geometry='GEOMETRY')

    # what is the zoning?
    try:
        zoning = gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "zoning"]
        )["LABEL"][0]
    except KeyError:
        zoning = "unknown"

    # which ward is it in?
    try:
        ward = gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "ward"]
        )["LABEL"][0]
    except KeyError:
        ward = "unknown"

    # which neighborhood is it in?
    try:
        neighborhood = gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "neighborhood"]
        )["LABEL"][0]
    except KeyError:
        neighborhood = "unknown"

    # which school district is it in?
    try:
        hs = gpd.sjoin(
            property_coordinates,
            geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "high_schools"]
        )["LABEL"][0]
    except KeyError:
        hs = "unknown"

    # is this property in ADU area?
    try:
        adu_ind = (
            gpd.sjoin(
                property_coordinates,
                geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "ADU"]
            ).shape[0]
            > 0
        )
    except KeyError:
        adu_ind = "unknown"

    # is this property in a mobility zone?
    try:
        mobility_ind = (
            gpd.sjoin(
                property_coordinates,
                geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "mobility_areas"]
            ).shape[0]
            > 0
        )
    except KeyError:
        mobility_ind = "unknown"

    # is this property in an enterprise zone?
    try:
        enterprise_ind = (
            gpd.sjoin(
                property_coordinates,
                geo_df_shape_data.loc[geo_df_shape_data.SOURCE == "enterprise_zone"]
            ).shape[0]
            > 0
        )
    except KeyError:
        enterprise_ind = "unknown"

    return zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind

@st.cache_resource
def build_map(LAT, LON, df_location_map, selected_map_items):

    # icons: https://fontawesome.com/v4/icons/
    # color choices: ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue',
    # 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
    
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
        # if record is for one of the checked boxes, create a map marker
        if row["SOURCE"] in selected_map_items:
            feature_group.add_child(
                maps.add_map_marker(
                    m,
                    lat=row["LATITUDE"],
                    lon=row["LONGITUDE"],
                    name=row["LABEL"],
                    color=config["icon_mapping"][row["SOURCE"]]["color"],
                    icon=config["icon_mapping"][row["SOURCE"]]["icon"],
                )
            )

    # Change the map style
    # m.add_tile_layer(tiles='Stamen Toner', name='Stamen Toner')

    m.add_child(feature_group)

    return m

if 'address' not in st.session_state:
    st.session_state['address'] = ''

address = st.text_input("Enter Address: ")

if address:
    st.session_state['address'] = address

if st.session_state['address'] != '':
    
    # geocode the address
    try:
        LAT, LON = get_property_coordinates(address)
    except:
        st.error('Error: could not geocode this address. Please try another address.')
        st.error('Defaulting to Sears Tower.')
        LAT, LON = 41.878863944829405, -87.63591030536361

    zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind = get_area_data(LAT, LON)

    # limit the markers on the map
    df_location_map = get_points_nearby(LAT, LON)

    # https://docs.streamlit.io/library/api-reference/layout/st.sidebar
    with st.sidebar:
        
        st.header('Include in Map:')

        all_map_items = df_location_map.SOURCE.unique().tolist()
        selected_map_items = []

        # https://docs.streamlit.io/library/api-reference/widgets/st.checkbox
        for item in all_map_items:
            if st.checkbox(item):
                selected_map_items.append(item)
        
        if len(all_map_items) == 0:
            st.write("No data for this area...")

    # make walk score request
    # walk, transit, bike = walk_score.get_walk_score_from_address(address, st.secrets["walkscore"]["walk-score-key"])
    try:
        walk, desc, transit, bike = walk_score.get_walk_score_from_coord(LAT, LON, st.secrets["walkscore"]["walk-score-key"])
    except:
        walk, desc, transit, bike = "unknown", "unknown", "unknown"

    m = build_map(LAT, LON, df_location_map, selected_map_items)

    # create two columns for charts
    fig_col1, fig_col2 = st.columns(2)

    with fig_col1:
        
        fig = st_folium(m, width=725)

        fig_col1.markdown("""
            Circles represent 12 and 25 minute walk approximately. Note that 
            not all data will be appear on the map, only the points nearby.
            """)
        
        fig_col1.markdown("""
            Download the map for better performance. Especially if there are many 
            map markers.""")
        
        btn = fig_col1.download_button(
            label = "Download",
            data = m._repr_html_(),
            file_name = f"{re.sub('[^a-zA-Z0-9]', '_', address)}.html",
            )
    
    with fig_col2:

        fig_col2.header("Property Details")

        fig_col2.divider()

        fig_col2.markdown(
            "[![walk_score](https://cdn.walk.sc/images/api-logo.png)](https://www.redfin.com/how-walk-score-works) " +
            f"[{walk}](https://www.redfin.com/how-walk-score-works) ({desc}) " + 
            f"[![question_mark](https://cdn.walk.sc/images/api-more-info.gif)](https://www.redfin.com/how-walk-score-works)"
            )
        
        col1, col2 = st.columns(2)

        col1.metric(
            label = "Bike Score",
            value = bike,
        )
        col2.metric(
            label = "transit score",
            value = transit,
        )

        col1.divider()
        col2.divider()

        col1, col2 = st.columns(2)
        col1.metric(
            label="Neighborhood",
            value=neighborhood,
        )
        col2.metric(
            label="Ward",
            value=ward,
        )

        col1.divider()
        col2.divider()

        col1.metric(
            label="Zoning",
            value=zoning,
        )
        col2.metric(
            label="ADU Area",
            value=adu_ind,
        )

        col1.divider()
        col2.divider()

        col1.metric(
            label="Mobility Area",
            value=mobility_ind,
        )
        col2.metric(
            label="Enterprise Zone",
            value=enterprise_ind,
        )

st.divider()
st.markdown("Data provided by Chicago Data Portal, Walk Score API, Nominatim geocoder, Google Maps")
st.markdown("Built with Streamlit, Snowflake, Folium")
st.markdown("Dashboard created by Beau Smit")
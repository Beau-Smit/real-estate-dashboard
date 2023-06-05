import os
import json
import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
import geopy.distance
from geopy.geocoders import Nominatim
from shapely.geometry import Point, Polygon
from snowflake.snowpark import Session


# config for map icons
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, "r") as f:
    config = json.loads(f.read())


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


@st.cache_resource
def add_map_marker(lat, lon, name="NA", color="blue", icon="map-marker"):
    marker = folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color=color, icon=icon, prefix="fa"),
    )
    return marker


@st.cache_resource
def add_map_circle(lat, lon, radius=800):
    # radius parameter in meters
    circle = folium.Circle(
        location=[lat, lon],
        radius=radius,  # 800 meters = 0.5 miles
        color="red",
        fill=True,
        fill_color="red",
    )
    return circle


def get_closest(coords_1_lat, coords_1_lon, coords_2_lat, coords_2_lon):
    shortest_distance_lst = []
    for coord_1 in zip(coords_1_lat, coords_1_lon):
        shortest_distance = 10  # arbitrarily chosen
        for coord_2 in zip(coords_2_lat, coords_2_lon):
            dist = geopy.distance.geodesic(coord_1, coord_2).miles
            if dist < shortest_distance:
                shortest_distance = dist
        shortest_distance_lst.append(shortest_distance)
    return pd.Series(shortest_distance_lst)


def count_points_within_range(
    coords_1_lat, coords_1_lon, coords_2_lat, coords_2_lon, within_dist=0.5
):
    # walking distance in miles
    count_lst = []
    for coord_1 in zip(coords_1_lat, coords_1_lon):
        count = 0
        for coord_2 in zip(coords_2_lat, coords_2_lon):
            dist = geopy.distance.geodesic(coord_1, coord_2).miles
            if dist < within_dist:
                count += 1
        count_lst.append(count)
    return pd.Series(count_lst)


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
    add_map_marker(
        lat=LAT, lon=LON, name="property", color="black", icon="home"
    ).add_to(m)

    # add circles for distance reference around property
    add_map_circle(
        lat=LAT, lon=LON, radius=800
    ).add_to(m)  # 800 meters = 0.5 miles
    add_map_circle(
        lat=LAT, lon=LON, radius=1600
    ) .add_to(m) # 800 meters = 1 miles

    feature_group = folium.FeatureGroup("Locations")

    for _, row in df_location_map.iterrows():
        # if record is for one of the checked boxes, create a map marker
        if row["SOURCE"] in selected_map_items:
            feature_group.add_child(
                add_map_marker(
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
# Can use sqlite3 to mimic a remote database on disk
# https://docs.python.org/3.8/library/sqlite3.html

import streamlit as st
import snowflake.connector
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from snowflake.snowpark import Session
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim

table_name = "REAL_ESTATE.LOCATIONS.POINTS"

st.title("Property Dashboard")
st.header("What's nearby?")


# https://towardsdatascience.com/how-to-connect-streamlit-to-snowflake-b93256d80a40


# Establish Snowflake session
@st.cache_resource
def create_session():
    return Session.builder.configs(st.secrets.snowflake).create()


session = create_session()
st.success("Connected to Snowflake!")


# Load data table
@st.cache_data
def load_data(table_name):
    table = session.table(table_name)

    return table.collect()


def add_map_marker(m, lat, lon, name="NA", color="blue", icon="map-marker"):
    marker = folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color=color, icon=icon, prefix="fa"),
    )
    # icon list: https://getbootstrap.com/docs/3.3/components/
    return marker


address = st.text_input("Enter Address: ")

if address:
    # get geographic coordinates
    geolocator = Nominatim(user_agent="beau.h.smit@gmail.com")
    location = geolocator.geocode(address)
    LAT, LON = location.latitude, location.longitude

    property_coordinates = gpd.GeoDataFrame(
        {"geometry": [Point(LON, LAT)]}, crs="EPSG:4326"
    )

    # Create a Map instance for Chicago
    m = folium.Map(location=[LAT, LON], zoom_start=16)

    # add marker for the property of interest
    add_map_marker(
        m, lat=LAT, lon=LON, name="property", color="black", icon="house-chimney"
    ).add_to(m)

    # Loop through each row in the dataframe
    # for idx, row in df.iterrows():
    #     add_map_marker(m, row.Latitude, row.Longitude)


else:
    LAT, LON = 41.88357954212235, -87.63152062949634

    property_coordinates = gpd.GeoDataFrame(
        {"geometry": [Point(LON, LAT)]}, crs="EPSG:4326"
    )

    # Create a Map instance for Chicago
    m = folium.Map(location=[LAT, LON], zoom_start=16)

st.text("Click and drag map")
st_data = st_folium(m, width=725)

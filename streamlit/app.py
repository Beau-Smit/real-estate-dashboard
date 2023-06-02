# Can use sqlite3 to mimic a remote database on disk
# https://docs.python.org/3.8/library/sqlite3.html

import streamlit as st
import geopandas as gpd
from shapely.geometry import Point, Polygon
from snowflake.snowpark.session import Session
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
import map_functions as maps

table_name = "REAL_ESTATE.LOCATIONS.POINTS"

st.title("Property Dashboard")
st.header("What's nearby?")


# https://towardsdatascience.com/how-to-connect-streamlit-to-snowflake-b93256d80a40


# Establish Snowflake session
@st.cache_resource
def create_session():
    return Session.builder.configs(st.secrets.connections.snowpark).create()


session = create_session()
st.success("Connected to Snowflake!")


# Load data table
# @st.cache_data
def load_data(table_name):
    table = session.table(table_name)

    return table.to_pandas()

# @st.cache_data
def get_property_coordinates(address):
    # get geographic coordinates
    geolocator = Nominatim(user_agent="beau.h.smit@gmail.com")
    location = geolocator.geocode(address)
    LAT, LON = location.latitude, location.longitude

    return LAT, LON

# @st.cache_data
def get_points_nearby(LAT, LON):
    # df_location = session.sql("select * from REAL_ESTATE.LOCATIONS.POINTS limit 50").collect()
    df_location = load_data("REAL_ESTATE.LOCATIONS.POINTS")
    # df_location.show()

    # exclude locations far from property
    lat_min = LAT - 0.03
    lat_max = LAT + 0.03
    lon_min = LON - 0.04
    lon_max = LON + 0.04

    # limit the markers on the map
    df_location_map = df_location.loc[
        df_location.SOURCE.isin(
            [
                # TODO: controls which points are on map
                # TODO: need bar names, not business names
                # "liquor",
                # "divvy",
                "murals",
                # "EV_chargers",
                "landmarks",
                "L",
                "grocery",
                "park_art",
                "farmers_market",
                "hospitals",
                "metra",
            ]
        )
        & (df_location.LATITUDE.between(lat_min, lat_max))
        & (df_location.LONGITUDE.between(lon_min, lon_max)),
        :,
    ]

    return df_location_map


# @st.cache_data
def get_area_data(LAT, LON):
    # df_location = session.sql("select * from REAL_ESTATE.LOCATIONS.POINTS limit 50").collect()
    df_shape_data = load_data("REAL_ESTATE.LOCATIONS.SHAPES")
    st.dataframe(df_shape_data)
    # df_location.show()

    property_coordinates = gpd.GeoDataFrame(
        {"geometry": [Point(LON, LAT)]}, crs="EPSG:4326"
    )

    # GeoDataFrame.set_geometry
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

# @st.cache_resource
# @st.cache_resource(experimental_allow_widgets=True)
def build_map(LAT, LON, df_location_map):

    # TODO: move to config
    source_dict = {
        "liquor": {"color": "orange", "icon": "martini-glass"},
        "divvy": {"color": "blue", "icon": "bicycle"},
        "murals": {"color": "pink", "icon": "palette"},
        "EV_chargers": {"color": "darkgreen", "icon": "bolt"},
        "landmarks": {"color": "gray", "icon": "landmark"},
        "L": {"color": "darkblue", "icon": "train-subway"},
        "grocery": {"color": "green", "icon": "cart-shopping"},
        "park_art": {"color": "lightred", "icon": "bench-tree"},
        "farmers_market": {"color": "lightgreen", "icon": "seedling"},
        "hospitals": {"color": "red", "icon": "plus-sign"},
        "metra": {"color": "red", "icon": "plus-sign"},
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
    # map.save(outfile = "test.html")
    m.add_child(feature_group)

    return m

if 'address' not in st.session_state:
    st.session_state['address'] = ''

address = st.text_input("Enter Address: ")

if address:
    st.session_state['address'] = address

if st.session_state['address'] == '':

    # default map center is downtown Chicago
    LAT, LON = 41.88357954212235, -87.63152062949634

    # Create a Map instance for Chicago
    m = folium.Map(location=[LAT, LON], zoom_start=16)

else:
    # geocode the address
    LAT, LON = get_property_coordinates(address)
    st.write('1')
    zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind = get_area_data(LAT, LON)
    st.write('2')
    st.write(zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind)
    st.write('3')
    # limit the markers on the map
    df_location_map = get_points_nearby(LAT, LON)
    st.write('4')
    m = build_map(LAT, LON, df_location_map)

    st.text("Circles represent 12 and 25 minute walk approximately.")

st_data = st_folium(m, width=725)

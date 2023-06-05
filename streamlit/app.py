# Can use sqlite3 to mimic a remote database on disk
# https://docs.python.org/3.8/library/sqlite3.html

import streamlit as st
st.set_page_config(layout="wide")

import re
from streamlit.components.v1 import html
import pandas as pd
from streamlit_folium import st_folium
import walk_score
import map_functions


st.title("Chicago Property Dashboard")


if 'address' not in st.session_state:
    st.session_state['address'] = ''

address = st.text_input("Enter Address: ")

if address:
    st.session_state['address'] = address

if st.session_state['address'] != '':
    
    # geocode the address
    try:
        LAT, LON = map_functions.get_property_coordinates(address)
    except:
        st.error('Error: could not geocode this address. Please try another address.')
        st.error('Defaulting to Sears Tower.')
        LAT, LON = 41.878863944829405, -87.63591030536361

    zoning, ward, neighborhood, hs, adu_ind, mobility_ind, enterprise_ind = map_functions.get_area_data(LAT, LON)

    # limit the markers on the map
    df_location_map = map_functions.get_points_nearby(LAT, LON)

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

    m = map_functions.build_map(LAT, LON, df_location_map, selected_map_items)

    # create two columns for charts
    fig_col1, fig_col2 = st.columns([.6, .4])

    with fig_col1:
        
        # TODO: use return_values to improve app performance
        fig = st_folium(m, width=750)

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
        col1, col2 = st.columns(2)
        col1.metric(
            label="Neighborhood",
            value=neighborhood,
        )
        col2.metric(
            label="Ward",
            value=ward,
        )

        widget_html = walk_score.get_walk_score_widget(st.session_state['address'])
        html(widget_html, height=615)
        # col1, col2 = st.columns(2)

        col1.metric(
            label="Zoning",
            value=zoning,
        )
        col2.metric(
            label="ADU Area",
            value=adu_ind,
        )

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
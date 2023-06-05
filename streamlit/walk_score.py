import urllib.parse
import requests
import streamlit as st


# TODO: format the credits for Walk Score:
# https://www.walkscore.com/professional/branding-requirements.php

@st.cache_data
def get_walk_score_from_coord(lat, lon, wskey):
    api_url = f"https://api.walkscore.com/score?format=json&lat={lat}&lon={lon}&transit=1&bike=1&wsapikey={wskey}"
    response = requests.get(api_url)
    r = response.json()
    walk_score = r["walkscore"]
    walk_score_desc = r["description"]
    transit_score = r["transit"]["score"]
    bike_score = r["bike"]["score"]
    return walk_score, walk_score_desc, transit_score, bike_score

@st.cache_data
def get_walk_score_from_address(address, wskey):
    address_url = urllib.parse.quote(address)
    api_url = f"https://api.walkscore.com/score?format=json&address={address_url}&lat=47.6085&lon=-122.3295&transit=1&bike=1&wsapikey={wskey}"
    response = requests.get(api_url)
    r = response.json()
    walk_score = r["walkscore"]
    walk_score_desc = r["description"]
    transit_score = r["transit"]["score"]
    bike_score = r["bike"]["score"]
    return walk_score, walk_score_desc, transit_score, bike_score

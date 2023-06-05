import urllib.parse
import requests
import streamlit as st


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

@st.cache_data
def get_walk_score_widget(address):
    html_str = """
        <script type='text/javascript'>
        var ws_wsid = 'g1b877420ed61469586d83ab050f564b3';
        """
    html_str += f"var ws_address = '{address}';"
    html_str += """
        var ws_format = 'tall';
        var ws_width = '500';
        var ws_height = '615';
        </script><style type='text/css'>#ws-walkscore-tile{position:relative;text-align:left}#ws-walkscore-tile *{float:none;}</style><div id='ws-walkscore-tile'></div><script type='text/javascript' src='http://www.walkscore.com/tile/show-walkscore-tile.php'></script>
        """
    return html_str
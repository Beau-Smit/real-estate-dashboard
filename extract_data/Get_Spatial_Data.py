import os
import pandas as pd
import json
from utils import get_SODA_data
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

pd.set_option("mode.chained_assignment", None)

# read the config file
with open("extract_source_config.json", "r") as f:
    config = json.loads(f.read())

cleaned_path = os.path.join(config["root_path"], "data", "processed")
shape_files_path = os.path.join(config["root_path"], "data", "raw", "shape_files")


#### L Stations
df_L = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/8pix-ypme.json"
)

df_L["label"] = df_L["station_descriptive_name"]

# extract latitude and longitude
df_L["latitude"] = df_L.location.apply(lambda x: x["latitude"]).astype(float)
df_L["longitude"] = df_L.location.apply(lambda x: x["longitude"]).astype(float)


#### Metra Stations
# I had to create this file manually, so there's no "source"
df_metra = pd.read_csv(os.path.join(config['root_path'], "data", "raw", "Metra_Stations.csv"))
df_metra["label"] = df_metra["station_name"]


#### Divvy Stations
df_divvy = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/bbyy-e7gq.json"
)

df_divvy["label"] = df_divvy["station_name"]


#### Grocery Stores
df_grocery = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/3e26-zek2.json"
)

# remove records with no coordinate data
df_grocery = df_grocery.loc[df_grocery.location.notnull()]

df_grocery["label"] = df_grocery["store_name"]

# extract latitude and longitude
df_grocery["latitude"] = df_grocery.location.apply(
    lambda x: x["coordinates"][1]
).astype(float)
df_grocery["longitude"] = df_grocery.location.apply(
    lambda x: x["coordinates"][0]
).astype(float)


#### Hospitals
df_hospitals = gpd.read_file(os.path.join(shape_files_path, "Hospitals.zip"))
df_hospitals["label"] = df_hospitals["LABEL"]

# extract latitude and longitude
df_hospitals["longitude"] = df_hospitals.geometry.to_crs(4326).geometry.x
df_hospitals["latitude"] = df_hospitals.geometry.to_crs(4326).geometry.y


#### Current Business Licenses
df_current_licenses = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/uupf-x98q.json"
)

# remove records with no coordinate data
df_current_licenses = df_current_licenses.loc[
    df_current_licenses.latitude.notnull() & df_current_licenses.longitude.notnull()
]


#### Restaurants
df_restaurants = df_current_licenses.loc[
    df_current_licenses.license_description == "Retail Food Establishment"
]

df_restaurants["label"] = df_restaurants["doing_business_as_name"]


#### Liquor Business Licenses
df_liquor = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/nrmj-3kcf.json"
)

# remove records with no coordinate data
df_liquor = df_liquor.loc[df_liquor.latitude.notnull() & df_liquor.longitude.notnull()]

df_liquor["label"] = df_liquor["doing_business_as_name"]


#### Bars
df_bars = df_liquor.loc[
    df_liquor.license_description.isin(config["bar_license_descriptions"])
]


#### Liquor Stores
df_liquor_store = df_liquor.loc[
    df_liquor.license_description.isin(config["liquor_store_license_descriptions"])
]


#### Landmarks
df_landmarks = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/tdab-kixi.json"
)

df_landmarks["label"] = df_landmarks["landmark_name"]


#### Public Park Art
df_park_art = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/sj6t-9cju.json"
)

df_park_art["label"] = df_park_art["art"]


#### Murals
df_murals = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/we8h-apcf.json"
)

df_murals["label"] = df_murals["artwork_title"]


#### Electric Vehicle Chargers
df_EV_chargers = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/iq3c-68ew.json",
    custom_filter="&city=Chicago",
)

df_EV_chargers["label"] = df_EV_chargers["ev_network"]


#### Farmer's Markets
df_farmers_market = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/atzs-u7pv.json"
)

df_farmers_market["label"] = df_farmers_market["day"]


#### Business Licenses
# df_licenses = get_SODA_data(
#     api_endpoint="https://data.cityofchicago.org/resource/r5kz-chrr.json"
# )

# # remove records with no coordinate data
# df_licenses = df_licenses.loc[
#     df_licenses.latitude.notnull() & df_licenses.longitude.notnull()
# ].reset_index(drop=True)

# df_licenses["label"] = df_licenses["doing_business_as_name"]

# df_licenses.latitude = df_licenses.latitude.astype(float)
# df_licenses.longitude = df_licenses.longitude.astype(float)


#### Building Permits
# df_permits = get_SODA_data(
#     api_endpoint="https://data.cityofchicago.org/resource/building-permits.json"
# )

# # remove records with no coordinate data
# df_permits = df_permits.loc[
#     df_permits.latitude.notnull() & df_permits.longitude.notnull()
# ]

# df_permits["label"] = df_permits["permit_type"]



#### Mobility Areas
df_community_areas = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/igwz-8jzy.json"
)

df_community_areas["label"] = df_community_areas["community"]

# subset to mobility areas
df_mobility_areas = df_community_areas.loc[
    df_community_areas.community.isin(config["mobility_areas"])
]

# create geometry variable for the shapes
df_mobility_areas["geometry"] = df_mobility_areas["the_geom"].apply(
    lambda x: Polygon(x["coordinates"][0][0])
)
gdf_mobility_areas = gpd.GeoDataFrame(
    data=df_mobility_areas, crs="EPSG:4326", geometry="geometry"
)


#### ADU Areas
df_ADU = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/ttjb-ayff.json"
)

df_ADU["label"] = df_ADU["area"]

# create geometry variable for the shapes
df_ADU["geometry"] = df_ADU["the_geom"].apply(lambda x: Polygon(x["coordinates"][0][0]))
gdf_ADU = gpd.GeoDataFrame(data=df_ADU, crs="EPSG:4326", geometry="geometry")

# without a .zip shapefile, we have to convert into a geoseries and project the points
# df_ADU = gpd.read_file(os.path.join(SHAPE_FILES, "Additional_Dwelling_Unit_Areas.tsv"))
# df_ADU['geometry'] = gpd.GeoSeries.from_wkt(df_ADU['the_geom'])
# df_ADU['geometry'].crs = "EPSG:4326"


#### Zoning
df_zoning = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/dj47-wfun.json"
)

df_zoning["label"] = df_zoning["zone_class"]

df_zoning["geometry"] = df_zoning["the_geom"].apply(
    lambda x: Polygon(x["coordinates"][0][0])
)
gdf_zoning = gpd.GeoDataFrame(data=df_zoning, crs="EPSG:4326", geometry="geometry")


#### Bike Routes
df_bike_routes = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/hvv9-38ut.json"
)

df_bike_routes["label"] = df_bike_routes["st_name"]

df_bike_routes["geometry"] = df_bike_routes["the_geom"].apply(
    lambda x: LineString(x["coordinates"][0])
)
gdf_bike_routes = gpd.GeoDataFrame(
    data=df_bike_routes, crs="EPSG:4326", geometry="geometry"
)


#### Wards
df_wards = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/k9yb-bpqx.json"
)

df_wards["label"] = df_wards["ward"]

df_wards["geometry"] = df_wards["the_geom"].apply(
    lambda x: Polygon(x["coordinates"][0][0])
)
gdf_wards = gpd.GeoDataFrame(data=df_wards, crs="EPSG:4326", geometry="geometry")


#### Neighborhoods
df_neighborhoods = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/y6yq-dbs2.json"
)

df_neighborhoods["label"] = df_neighborhoods["pri_neigh"]

df_neighborhoods["geometry"] = df_neighborhoods["the_geom"].apply(
    lambda x: Polygon(x["coordinates"][0][0])
)
gdf_neighborhoods = gpd.GeoDataFrame(
    data=df_neighborhoods, crs="EPSG:4326", geometry="geometry"
)


#### Enterprise Zones
df_enterprise_zones = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/bwpt-y235.json"
)

df_enterprise_zones["label"] = df_enterprise_zones["name"]

df_enterprise_zones["geometry"] = df_enterprise_zones["the_geom"].apply(
    lambda x: Polygon(x["coordinates"][0][0])
)
gdf_enterprise_zones = gpd.GeoDataFrame(
    data=df_enterprise_zones, crs="EPSG:4326", geometry="geometry"
)


#### Public High Schools
df_hs = get_SODA_data(
    api_endpoint="https://data.cityofchicago.org/resource/juf9-y87b.json"
)

df_hs["label"] = df_hs["school_nm"]

df_hs["geometry"] = df_hs["the_geom"].apply(lambda x: Polygon(x["coordinates"][0][0]))
gdf_hs = gpd.GeoDataFrame(data=df_hs, crs="EPSG:4326", geometry="geometry")


# # Combine all data sources with geo-coordinate data
sources_point_data = {
    "L Stations": df_L,
    "Metra Stations": df_metra,
    "Divvy Stations": df_divvy,
    "Grocery Stores": df_grocery,
    "Hospitals": df_hospitals,
    "Restaurants": df_restaurants,
    "Bars": df_bars,
    "Landmarks": df_landmarks,
    "Park Art": df_park_art,
    "Murals": df_murals,
    "EV Chargers": df_EV_chargers,
    "Farmers Markets": df_farmers_market
    # "licenses": df_licenses,
    # "current_licenses": df_current_licenses,
    # "permits": df_permits,
}

df_location_combined = pd.DataFrame(
    columns=["source", "label", "latitude", "longitude"]
)

for name, df in sources_point_data.items():
    df_location = df[["label", "latitude", "longitude"]]
    df_location["source"] = name
    df_location_combined = pd.concat([df_location_combined, df_location])

df_location_combined.reset_index(drop=True, inplace=True)

# fix data types
df_location_combined.latitude = df_location_combined.latitude.astype("float")
df_location_combined.longitude = df_location_combined.longitude.astype("float")


# # Combine all data sources with shape data
sources_shape_data = {
    "mobility_areas": gdf_mobility_areas,
    "ADU": gdf_ADU,
    "zoning": gdf_zoning,
    "bike_routes": df_bike_routes,
    "ward": gdf_wards,
    "neighborhood": gdf_neighborhoods,
    "enterprise_zone": df_enterprise_zones,
    "high_schools": gdf_hs,
}

df_shape_data_combined = pd.DataFrame(columns=["source", "label", "geometry"])

for name, df in sources_shape_data.items():
    df_shape_data = df[["label", "geometry"]]
    df_shape_data["source"] = name
    df_shape_data_combined = pd.concat([df_shape_data_combined, df_shape_data])


df_shape_data_combined.reset_index(drop=True, inplace=True)


# # Write out combined data
# make column names upper case
df_location_combined.columns = [col.upper() for col in df_location_combined.columns]
df_shape_data_combined.columns = [col.upper() for col in df_shape_data_combined.columns]

df_location_combined.to_pickle(
    os.path.join(cleaned_path, "whats_nearby_location_data.pkl")
)
df_shape_data_combined.to_pickle(
    os.path.join(cleaned_path, "whats_nearby_shape_data.pkl")
)

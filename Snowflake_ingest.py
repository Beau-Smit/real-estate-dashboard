import os
import snowflake.connector
import toml
import pandas as pd
import geopandas as gpd
from snowflake.snowpark import Session

table_name = "real_estate.locations.points_of_interest"
ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"
SHAPE_FILES = os.path.join(ROOT, "data", "raw", "shape_files")
RAW = os.path.join(ROOT, "data", "raw")
CLEANED = os.path.join(ROOT, "data", "processed")

connection_parameters = toml.load(
    os.path.join(ROOT, "streamlit", ".streamlit", "secrets.toml")
)


def create_session():
    return Session.builder.configs(connection_parameters["snowflake"]).create()


session = create_session()

# load location data
df_location_combined = pd.read_pickle(
    os.path.join(CLEANED, "whats_nearby_location_data.pkl")
)

# load shape data
df_shape_data_combined = pd.read_pickle(
    os.path.join(CLEANED, "whats_nearby_shape_data.pkl")
)
df_shape_data_combined.GEOMETRY = df_shape_data_combined.GEOMETRY.astype(str)


session.sql(
    """
    CREATE OR REPLACE TABLE POINTS (
        SOURCE VARCHAR
        ,LABEL VARCHAR
        ,LATITUDE NUMBER(13, 10)
        ,LONGITUDE NUMBER(13, 10)
        ,STATION_NAME VARCHAR
        )
    """
).collect()

session.sql(
    """
    CREATE OR REPLACE TABLE SHAPES (
        SOURCE VARCHAR
        ,LABEL VARCHAR
        ,GEOMETRY VARCHAR
        )
    """
).collect()


# write data to Snowflake
session.write_pandas(
    df=df_location_combined,
    table_name="POINTS",
    database="REAL_ESTATE",
    schema="LOCATIONS",
)

session.write_pandas(
    df=df_shape_data_combined,
    table_name="SHAPES",
    database="REAL_ESTATE",
    schema="LOCATIONS",
)

session.close()

"""
Takes cleaned data and loads it into Snowflake using Snowpark.
"""

import os
import json
import toml
import pandas as pd
from snowflake.snowpark import Session

# read the config files
with open("extract_source_config.json", "r") as f:
    config = json.loads(f.read())

connection_parameters = toml.load(
    os.path.join(config['root_path'], "src", "streamlit", ".streamlit", "secrets.toml")
)

cleaned_path = os.path.join(config['root_path'], "data", "processed")


# create a Snowpark session with the secrets toml file
def create_session():
    return Session.builder.configs(connection_parameters["snowflake"]).create()


session = create_session()

print("Reading location data.")

# load location data
df_location_combined = pd.read_pickle(
    os.path.join(cleaned_path, "whats_nearby_location_data.pkl")
)

session.sql(
    """
    CREATE OR REPLACE TABLE POINTS (
        SOURCE VARCHAR
        ,LABEL VARCHAR
        ,LATITUDE NUMBER(13, 10)
        ,LONGITUDE NUMBER(13, 10)
        )
    """
).collect()

print("Writing location data to Snowflake.")

session.write_pandas(
    df=df_location_combined,
    table_name="POINTS",
    database="REAL_ESTATE",
    schema="LOCATIONS",
)

print("Reading shape data.")

# load shape data
df_shape_data_combined = pd.read_pickle(
    os.path.join(cleaned_path, "whats_nearby_shape_data.pkl")
)
df_shape_data_combined.GEOMETRY = df_shape_data_combined.GEOMETRY.astype(str)

session.sql(
    """
    CREATE OR REPLACE TABLE SHAPES (
        SOURCE VARCHAR
        ,LABEL VARCHAR
        ,GEOMETRY VARCHAR
        )
    """
).collect()

print("Writing shape data to Snowflake.")

session.write_pandas(
    df=df_shape_data_combined,
    table_name="SHAPES",
    database="REAL_ESTATE",
    schema="LOCATIONS",
)

session.close()

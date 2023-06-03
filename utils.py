import os
import pandas as pd
import requests
import yaml

ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"
SHAPE_FILES = os.path.join(ROOT, "data", "raw", "shape_files")
CLEANED = os.path.join(ROOT, "data", "processed")

# get application token
with open(os.path.join(ROOT, "credentials.yml"), mode="r") as file:
    apptoken = yaml.safe_load(file)["SODA-token"]


# sql methods for API: https://dev.socrata.com/docs/queries/
def get_SODA_data(api_endpoint, custom_filter=""):
    headers = {"X-App-Token": apptoken}
    data = requests.get(
        f"{api_endpoint}?$limit=1000000{custom_filter}", headers=headers
    ).json()
    df = pd.DataFrame.from_records(data)
    return df

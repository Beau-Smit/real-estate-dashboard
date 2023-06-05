import os
import json
import yaml
import pandas as pd
import requests

root_path = "C:/Users/Beau/Documents/GitHub/RealEstate"

with open("extract_source_config.json", "r") as f:
    config = json.loads(f.read())

# get application token
with open(os.path.join(root_path, "credentials.yml"), mode="r") as file:
    apptoken = yaml.safe_load(file)["SODA-token"]


# sql methods for API: https://dev.socrata.com/docs/queries/
def get_SODA_data(api_endpoint, custom_filter=""):
    headers = {"X-App-Token": apptoken}
    data = requests.get(
        f"{api_endpoint}?$limit=1000000{custom_filter}", headers=headers
    ).json()
    df = pd.DataFrame.from_records(data)
    return df

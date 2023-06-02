import pandas as pd
import os

ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"
ZILLOW_DATA = os.path.join(ROOT, "data", "raw", "Zillow_multifamily_sold_in_2022")

# read all the input files
df = pd.DataFrame()
for filename in os.listdir(ZILLOW_DATA):
    full_path = os.path.join(ZILLOW_DATA, filename)
    df = df.append(pd.read_csv(full_path))

df.reset_index(drop=True, inplace=True)

# drop columns that are completely empty
for col in df.columns:
    if df[col].notnull().sum() == 0:
        df.drop(col, axis=1, inplace=True)

# only keep records with both bedrooms and bathrooms data
df = df.loc[df.Bedrooms.notnull() & df.Bathrooms.notnull()]

df.to_pickle(
    os.path.join(ROOT, "data", "serialized", "Zillow_multifamily_sold_in_2022.pkl")
)

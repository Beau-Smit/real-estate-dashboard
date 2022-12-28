import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from bokeh.plotting import figure, show

ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"

df_home = pd.read_csv(f"{ROOT}/data/raw/Zip_zhvi_sm_sa_month_home_values.csv")
df_rent = pd.read_csv(f"{ROOT}/data/raw/Zip_zori_sm_sa_month_rentals_index.csv")

df_chi_home = df_home.loc[df_home.City == 'Chicago']
df_chi_rent = df_rent.loc[df_rent.City == 'Chicago']

# home value data starts 1/31/2000
# rent data starts 3/31/2015
df_chi_home_recent = df_chi_home.loc[:,'2015-03-31':]
df_chi_rent_recent = df_chi_rent.loc[:,'3/31/2015':]

df_chi_home_recent.columns = pd.to_datetime(df_chi_home_recent.columns).date
df_chi_rent_recent.columns = pd.to_datetime(df_chi_rent_recent.columns).date

df_chi_home_zip = pd.concat([df_chi_home[['RegionName']], df_chi_home_recent], axis=1).set_index("RegionName")
df_chi_rent_zip = pd.concat([df_chi_rent[['RegionName']], df_chi_rent_recent], axis=1).set_index("RegionName")

df_chi_ratio = (df_chi_home_zip/df_chi_rent_zip).reset_index()

# get rid of zips with home values too high
# df_chi_home_zip_idx = (df_chi_home_zip.iloc[:, -1] < 500000) & (df_chi_home_zip.iloc[:, -1] > 300000)
# df_chi_ratio = df_chi_ratio.set_index('RegionName').loc[df_chi_home_zip_idx]

# get rid of zipcodes with lots of missing data
# missing_idx = df_chi_ratio.isna().sum(axis=1)<50
# df_chi_ratio = df_chi_ratio.loc[missing_idx, :]

df_long = pd.melt(df_chi_ratio.reset_index(), id_vars=['RegionName'], value_vars=df_chi_ratio.columns, var_name='Date')
df_long.Date = pd.to_datetime(df_long.Date)
df_long['zipcode'] = df_long.RegionName.astype(str)

sns.lineplot(data=df_long, x="Date", y="value", hue="zipcode")
plt.grid()
plt.show()

df_chi_ratio.columns = df_chi_ratio.columns.astype(str)
home_value_add_on = df_chi_home[['RegionName', '2022-10-31']].set_index('RegionName')
home_value_add_on.columns = ['home_values_2022']
combined = pd.concat([df_chi_ratio.set_index('RegionName'), home_value_add_on], axis=1)

print(combined[['2022-10-31', 'home_values_2022']].sort_values('2022-10-31'))
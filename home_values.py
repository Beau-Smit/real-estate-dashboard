import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from bokeh.plotting import figure, show

ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"

df = pd.read_csv(
    f"{ROOT}/data/raw/Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
)
df_chi = df.loc[df.City == "Chicago"]
date_col_names = set(
    [match[0] for match in df.columns.str.findall(r"\d+-\d+-\d+").values if match != []]
)
df_long = pd.melt(
    df_chi, id_vars=["RegionName"], value_vars=date_col_names, var_name="Date"
)
df_long.Date = pd.to_datetime(df_long.Date)

with open(f"{ROOT}/data/raw/Chicago_neighborhoods.txt", "r") as f:
    contents = f.read()
selected_regions = contents.split()

# sns.lineplot(data=df_long.loc[df_long.RegionName.isin(selected_regions)], x="Date", y="value", hue="RegionName")
# plt.grid()
# plt.show()

# df_chi['10yr_diff'] = df_chi['2022-10-31'] - df_chi['2012-10-31']
# df_chi['5yr_diff'] = df_chi['2022-10-31'] - df_chi['2017-10-31']
# df_chi['2yr_diff'] = df_chi['2022-10-31'] - df_chi['2020-10-31']
# print(df_chi.loc[df_chi['2022-10-31'] < 600000, ['RegionName', '2yr_diff', '2022-10-31']].sort_values('2yr_diff', ascending=False)[:15])

import pandas as pd
import os
import matplotlib.pyplot as plt

ROOT = "C:/Users/Beau/Documents/GitHub/RealEstate"

df = pd.read_csv(f"{ROOT}/Housing_Data/Building_Permits.csv")

print(df.TOTAL_FEE.mean())

# format dates
df.APPLICATION_START_DATE = pd.to_datetime(df.APPLICATION_START_DATE)
df.ISSUE_DATE = pd.to_datetime(df.ISSUE_DATE)

# subset to permits issued since 2010
idx = df.ISSUE_DATE > pd.to_datetime("1/1/2019")
df = df.loc[idx]

# 'PERMIT - WRECKING/DEMOLITION'
# 'PERMIT - EASY PERMIT PROCESS'
# 'PERMIT - SIGNS'
# 'PERMIT - RENOVATION/ALTERATION'
# 'PERMIT - ELECTRIC WIRING'
# 'PERMIT - NEW CONSTRUCTION'
# 'PERMIT - ELEVATOR EQUIPMENT'
# 'PERMIT - REINSTATE REVOKED PMT'
# 'PERMIT - SCAFFOLDING'
permits_of_interest = ["PERMIT - NEW CONSTRUCTION"]
idx = df.PERMIT_TYPE.isin(permits_of_interest)
df = df.loc[idx]

plt.scatter(df.LONGITUDE, df.LATITUDE, alpha=0.3, s=0.2, c=df.TOTAL_FEE)
plt.show()

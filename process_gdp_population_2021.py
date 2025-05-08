import pandas as pd
import os

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Step a) Load CSV files with na_values set
df_gdp = pd.read_csv("gdp_per_capita_2021.csv", na_values=["None"])
df_pop = pd.read_csv("population_2021.csv", na_values=["None"])

# Step b) Rename columns to use underscores instead of spaces
df_gdp.columns = [col.replace(" ", "_") for col in df_gdp.columns]
df_pop.columns = [col.replace(" ", "_") for col in df_pop.columns]

# Confirm required columns exist after renaming
assert 'Country' in df_gdp.columns and 'GDP_per_capita_PPP' in df_gdp.columns, "Missing columns in df_gdp"
assert 'Country' in df_pop.columns and 'Population' in df_pop.columns, "Missing columns in df_pop"

# Step c) Convert GDP and Population columns to numeric
df_gdp['GDP_per_capita_PPP'] = pd.to_numeric(df_gdp['GDP_per_capita_PPP'], errors='coerce')
df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')

# Step d) Save before sort
df_gdp.head().to_csv("output/gdp_before_sort.csv", index=False)
df_pop.head().to_csv("output/pop_before_sort.csv", index=False)

# Sort and save after sort
df_gdp_sorted = df_gdp.sort_values(by="Country")
df_pop_sorted = df_pop.sort_values(by="Country")

df_gdp_sorted.head().to_csv("output/gdp_after_sort.csv", index=False)
df_pop_sorted.head().to_csv("output/pop_after_sort.csv", index=False)

# Step e) Describe and save
df_gdp.describe().to_csv("output/gdp_describe.csv")
df_pop.describe().to_csv("output/pop_describe.csv")

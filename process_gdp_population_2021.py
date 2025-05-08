import pandas as pd
import os

# Step a) Load CSV files with na_values set
df_gdp = pd.read_csv("output/gdp_per_capita_2021.csv", na_values=["None"])
df_pop = pd.read_csv("output/population_2021.csv", na_values=["None"])

# Step b) Rename columns to use underscores instead of spaces
df_gdp.columns = [col.replace(" ", "_") for col in df_gdp.columns]
df_pop.columns = [col.replace(" ", "_") for col in df_pop.columns]

# ✅ Confirm shapes and columns
print("\n--- DataFrame Shapes and Columns ---")
print(f"GDP shape: {df_gdp.shape}")
print(f"GDP columns: {list(df_gdp.columns)}\n")

print(f"Population shape: {df_pop.shape}")
print(f"Population columns: {list(df_pop.columns)}\n")

# Confirm required columns exist after renaming
assert 'Country' in df_gdp.columns and 'GDP_per_capita_PPP' in df_gdp.columns, "Missing columns in df_gdp"
assert 'Country' in df_pop.columns and 'Population' in df_pop.columns, "Missing columns in df_pop"

# Step c) Convert GDP and Population columns to numeric
df_gdp['GDP_per_capita_PPP'] = pd.to_numeric(df_gdp['GDP_per_capita_PPP'], errors='coerce')
df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')

# Step d) Save and print before sort
print("\n--- GDP Data (Before Sort) ---")
print(df_gdp.head())
df_gdp.head().to_csv("output/gdp_before_sort.csv", index=False)

print("\n--- Population Data (Before Sort) ---")
print(df_pop.head())
df_pop.head().to_csv("output/pop_before_sort.csv", index=False)

# Sort and save after sort
df_gdp_sorted = df_gdp.sort_values(by="Country")
df_pop_sorted = df_pop.sort_values(by="Country")

print("\n--- GDP Data (After Sort) ---")
print(df_gdp_sorted.head())
df_gdp_sorted.head().to_csv("output/gdp_after_sort.csv", index=False)

print("\n--- Population Data (After Sort) ---")
print(df_pop_sorted.head())
df_pop_sorted.head().to_csv("output/pop_after_sort.csv", index=False)

# Step e) Describe and print
print("\n--- GDP Describe ---")
print(df_gdp.describe())
df_gdp.describe().to_csv("output/gdp_describe.csv")

print("\n--- Population Describe ---")
print(df_pop.describe())
df_pop.describe().to_csv("output/pop_describe.csv")

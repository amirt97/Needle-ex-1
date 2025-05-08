import pandas as pd
import numpy as np
import os

# === Setup ===
output_dir = "../output"

# === Utility: Normalize Country Name ===
def normalize_country(name):
    name = name.strip()
    if name.lower().startswith("the "):
        name = name[4:]
    return name.title()


# === Step 4.2: Clean df_gdp ===

# a) Load and clean GDP data
df_gdp = pd.read_csv("../gdp_per_capita_2021.csv", na_values=["None"])
df_gdp.columns = [col.replace(" ", "_") for col in df_gdp.columns]

df_gdp['GDP_per_capita_PPP'] = (
    df_gdp['GDP_per_capita_PPP']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_gdp['GDP_per_capita_PPP'] = pd.to_numeric(df_gdp['GDP_per_capita_PPP'], errors='coerce')

# b) Drop missing GDP values and save
missing_gdp = df_gdp[df_gdp['GDP_per_capita_PPP'].isna()]
missing_gdp.to_csv(f"{output_dir}/dropped_gdp.csv", index=False)
df_gdp = df_gdp.dropna(subset=['GDP_per_capita_PPP'])
print(f"Dropped GDP rows: {len(missing_gdp)}")

# c) Tukey outlier detection (GDP)
q1 = df_gdp['GDP_per_capita_PPP'].quantile(0.25)
q3 = df_gdp['GDP_per_capita_PPP'].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
gdp_outliers = df_gdp[(df_gdp['GDP_per_capita_PPP'] < lower_bound) | (df_gdp['GDP_per_capita_PPP'] > upper_bound)]
print(f"GDP outliers detected (Tukey method): {len(gdp_outliers)}")

# d) Remove duplicate country entries (keep first)
if df_gdp.duplicated(subset='Country').any():
    print("Duplicate countries found in GDP. Keeping first occurrence.")
    df_gdp = df_gdp.drop_duplicates(subset='Country', keep='first')

# e) Normalize country names
df_gdp['Country'] = df_gdp['Country'].apply(normalize_country)

# f) Set Country as index
df_gdp.set_index('Country', inplace=True)

# Save cleaned GDP
df_gdp.to_csv(f"{output_dir}/cleaned_gdp.csv")
print("Cleaned GDP saved.")


# === Step 4.3: Clean df_pop ===

# a) Load and clean Population data
df_pop = pd.read_csv("../population_2021.csv", na_values=["None"])
df_pop.columns = [col.replace(" ", "_") for col in df_pop.columns]

df_pop['Population'] = (
    df_pop['Population']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')

# b) Drop missing values and save
missing_pop = df_pop[df_pop['Population'].isna()]
missing_pop.to_csv(f"{output_dir}/dropped_pop.csv", index=False)
print(f"Dropped Population rows: {len(missing_pop)}")
df_pop = df_pop.dropna(subset=['Population'])

# c) Detect outliers on log10(Population)
df_pop['log10_Pop'] = np.log10(df_pop['Population'])
q1_log = df_pop['log10_Pop'].quantile(0.25)
q3_log = df_pop['log10_Pop'].quantile(0.75)
iqr_log = q3_log - q1_log
lower_log = q1_log - 1.5 * iqr_log
upper_log = q3_log + 1.5 * iqr_log

pop_outliers = df_pop[(df_pop['log10_Pop'] < lower_log) | (df_pop['log10_Pop'] > upper_log)]
print(f"Population outliers detected (Tukey on log10): {len(pop_outliers)}")

# d) Remove duplicates and normalize names
if df_pop.duplicated(subset='Country').any():
    print("Duplicate countries found in Population. Keeping first occurrence.")
    df_pop = df_pop.drop_duplicates(subset='Country', keep='first')

df_pop['Country'] = df_pop['Country'].apply(normalize_country)

# e) Set Country as index
df_pop.set_index('Country', inplace=True)
df_pop.drop(columns=['log10_Pop'], inplace=True)  # remove helper column

# Save cleaned Population
df_pop.to_csv(f"{output_dir}/cleaned_pop.csv")
print("Cleaned Population saved.")

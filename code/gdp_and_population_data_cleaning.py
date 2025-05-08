import pandas as pd
import numpy as np
import os

# Load GDP file (use cleaned or original file as needed)
df_gdp = pd.read_csv("../gdp_per_capita_2021.csv", na_values=["None"])

# Step 4.2a – Clean GDP values
df_gdp.columns = [col.replace(" ", "_") for col in df_gdp.columns]
df_gdp['GDP_per_capita_PPP'] = (
    df_gdp['GDP_per_capita_PPP']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_gdp['GDP_per_capita_PPP'] = pd.to_numeric(df_gdp['GDP_per_capita_PPP'], errors='coerce')

# Step 4.2b – Drop missing and save
missing_mask = df_gdp['GDP_per_capita_PPP'].isna()
df_dropped = df_gdp[missing_mask]
df_dropped.to_csv("../output/dropped_gdp.csv", index=False)
df_gdp = df_gdp[~missing_mask]

print(f"\nDropped rows due to missing GDP: {len(df_dropped)}")

# Step 4.2c – Identify outliers using Tukey method
q1 = df_gdp['GDP_per_capita_PPP'].quantile(0.25)
q3 = df_gdp['GDP_per_capita_PPP'].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = df_gdp[(df_gdp['GDP_per_capita_PPP'] < lower_bound) | (df_gdp['GDP_per_capita_PPP'] > upper_bound)]
print(f"Outliers in GDP data (Tukey method): {len(outliers)}")

# Step 4.2d – Check for duplicates
duplicates = df_gdp[df_gdp.duplicated(subset='Country', keep=False)]
if not duplicates.empty:
    print(f"\nFound duplicate countries:\n{duplicates['Country'].value_counts()}")
    df_gdp = df_gdp.drop_duplicates(subset='Country', keep='first')
    print("Duplicates dropped, keeping the first occurrence.")
else:
    print("No duplicate country entries found.")

# Step 4.2e – Apply country name mapping to match demographics
gdp_country_name_map = {
    "Cape Verde": "Cabo Verde",
    "Czechia": "Czech Republic (Czechia)",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Curacao": "Curaçao",
    "Democratic Republic of Congo": "DR Congo",
    "Micronesia (country)": "Micronesia",
    "Reunion": "Réunion",
    "Sao Tome and Principe": "Sao Tome & Principe",
    "St. Vincent and the Grenadines": "St. Vincent & Grenadines",
    "Palestine": "State of Palestine",
    "U.S. Virgin Islands": "U.S. Virgin Islands",
    "Timor-Leste": "Timor-Leste"
    # All others already match
}

df_gdp['Country'] = df_gdp['Country'].replace(gdp_country_name_map)

# Step 4.2f – Set Country as index
df_gdp.set_index('Country', inplace=True)

# Save cleaned file
df_gdp.to_csv("../output/cleaned_gdp.csv")
print("\nGDP cleaning complete. Cleaned data saved to output/cleaned_gdp.csv.")


# Setup
output_dir = "../output"

# Load population file
df_pop = pd.read_csv("../population_2021.csv", na_values=["None"])
df_pop.columns = [col.replace(" ", "_") for col in df_pop.columns]

# Clean numeric values
df_pop['Population'] = (
    df_pop['Population']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')

# Drop missing and save
missing_pop = df_pop[df_pop['Population'].isna()]
missing_pop.to_csv(f"{output_dir}/dropped_pop.csv", index=False)
print(f"Dropped Population rows: {len(missing_pop)}")
df_pop = df_pop.dropna(subset=['Population'])

# Detect outliers using log10 + Tukey method
df_pop['log10_Pop'] = np.log10(df_pop['Population'])
q1_log = df_pop['log10_Pop'].quantile(0.25)
q3_log = df_pop['log10_Pop'].quantile(0.75)
iqr_log = q3_log - q1_log
lower_log = q1_log - 1.5 * iqr_log
upper_log = q3_log + 1.5 * iqr_log

pop_outliers = df_pop[(df_pop['log10_Pop'] < lower_log) | (df_pop['log10_Pop'] > upper_log)]
print(f"Population outliers detected (Tukey on log10): {len(pop_outliers)}")

# Drop duplicates
duplicates = df_pop[df_pop.duplicated(subset='Country', keep=False)]
if not duplicates.empty:
    print(f"\nFound duplicate countries:\n{duplicates['Country'].value_counts()}")
    df_pop = df_pop.drop_duplicates(subset='Country', keep='first')
    print("Duplicates dropped, keeping the first occurrence.")
else:
    print("No duplicate country entries found.")

# Country name mapping to match demographics
pop_country_name_map = {
    "Cape Verde": "Cabo Verde",
    "Czechia": "Czech Republic (Czechia)",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Curacao": "Curaçao",
    "Democratic Republic of Congo": "DR Congo",
    "Micronesia (country)": "Micronesia",
    "Reunion": "Réunion",
    "Sao Tome and Principe": "Sao Tome & Principe",
    "St. Vincent and the Grenadines": "St. Vincent & Grenadines",
    "Palestine": "State of Palestine",
    "U.S. Virgin Islands": "U.S. Virgin Islands",
    "Timor-Leste": "Timor-Leste"
    # All others already match
}

# Apply mapping
df_pop['Country'] = df_pop['Country'].replace(pop_country_name_map)

# Set index and clean up
df_pop.set_index('Country', inplace=True)
df_pop.drop(columns=['log10_Pop'], inplace=True)

# Save cleaned file
df_pop.to_csv(f"{output_dir}/cleaned_pop.csv")
print("Cleaned Population saved to output/cleaned_pop.csv.")

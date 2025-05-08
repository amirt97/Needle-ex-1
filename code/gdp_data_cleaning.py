import pandas as pd
import numpy as np
import os

# Setup
output_dir = "../output"
os.makedirs(output_dir, exist_ok=True)

# === GDP CLEANING ===

# Load GDP file
df_gdp = pd.read_csv("../gdp_per_capita_2021.csv", na_values=["None"])
df_gdp.columns = [col.replace(" ", "_") for col in df_gdp.columns]

# Clean GDP values
df_gdp['GDP_per_capita_PPP'] = (
    df_gdp['GDP_per_capita_PPP']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_gdp['GDP_per_capita_PPP'] = pd.to_numeric(df_gdp['GDP_per_capita_PPP'], errors='coerce')

# Drop missing
missing_mask = df_gdp['GDP_per_capita_PPP'].isna()
df_dropped = df_gdp[missing_mask]
df_dropped.to_csv(f"{output_dir}/dropped_gdp.csv", index=False)
df_gdp = df_gdp[~missing_mask]
print(f"\nDropped rows due to missing GDP: {len(df_dropped)}")

# Outlier detection (Tukey)
q1 = df_gdp['GDP_per_capita_PPP'].quantile(0.25)
q3 = df_gdp['GDP_per_capita_PPP'].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
outliers = df_gdp[(df_gdp['GDP_per_capita_PPP'] < lower_bound) | (df_gdp['GDP_per_capita_PPP'] > upper_bound)]
print(f"Outliers in GDP data (Tukey method): {len(outliers)}")

# Remove duplicates
duplicates = df_gdp[df_gdp.duplicated(subset='Country', keep=False)]
if not duplicates.empty:
    print(f"\nFound duplicate countries:\n{duplicates['Country'].value_counts()}")
    df_gdp = df_gdp.drop_duplicates(subset='Country', keep='first')
    print("Duplicates dropped, keeping the first occurrence.")
else:
    print("No duplicate country entries found.")

# Country name mapping
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
    "United States Virgin Islands": "U.S. Virgin Islands",
    "East Timor": "Timor-Leste"
}

df_gdp['Country'] = df_gdp['Country'].replace(gdp_country_name_map)
df_gdp.set_index('Country', inplace=True)
df_gdp.to_csv(f"{output_dir}/cleaned_gdp.csv")
print("GDP cleaning complete. Cleaned data saved to output/cleaned_gdp.csv.")


# === POPULATION CLEANING ===

# Load population file
df_pop = pd.read_csv("../population_2021.csv", na_values=["None"])
df_pop.columns = [col.replace(" ", "_") for col in df_pop.columns]

# Clean population values
df_pop['Population'] = (
    df_pop['Population']
    .astype(str)
    .str.replace(",", "")
    .str.replace(r"[^\d.]", "", regex=True)
)
df_pop['Population'] = pd.to_numeric(df_pop['Population'], errors='coerce')

# Drop missing
missing_pop = df_pop[df_pop['Population'].isna()]
missing_pop.to_csv(f"{output_dir}/dropped_pop.csv", index=False)
print(f"\nDropped Population rows: {len(missing_pop)}")
df_pop = df_pop.dropna(subset=['Population'])

# Detect outliers (log10 + Tukey)
df_pop['log10_Pop'] = np.log10(df_pop['Population'])
q1_log = df_pop['log10_Pop'].quantile(0.25)
q3_log = df_pop['log10_Pop'].quantile(0.75)
iqr_log = q3_log - q1_log
lower_log = q1_log - 1.5 * iqr_log
upper_log = q3_log + 1.5 * iqr_log
pop_outliers = df_pop[(df_pop['log10_Pop'] < lower_log) | (df_pop['log10_Pop'] > upper_log)]
print(f"Population outliers detected (Tukey on log10): {len(pop_outliers)}")

# Remove duplicates
duplicates = df_pop[df_pop.duplicated(subset='Country', keep=False)]
if not duplicates.empty:
    print(f"\nFound duplicate countries:\n{duplicates['Country'].value_counts()}")
    df_pop = df_pop.drop_duplicates(subset='Country', keep='first')
    print("Duplicates dropped, keeping the first occurrence.")
else:
    print("No duplicate country entries found.")

# Country name mapping
pop_country_name_map = {
    "Cape Verde": "Cabo Verde",
    "Czechia": "Czech Republic (Czechia)",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Curacao": "Curaçao",
    "Democratic Republic of Congo": "DR Congo",
    "Micronesia (country)": "Micronesia",
    "Reunion": "Réunion",
    "Sao Tome and Principe": "Sao Tome & Principe",
    "Saint Vincent and the Grenadines": "St. Vincent & Grenadines",
    "Palestine": "State of Palestine",
    "United States Virgin Islands": "U.S. Virgin Islands",
    "East Timor": "Timor-Leste"
}

df_pop['Country'] = df_pop['Country'].replace(pop_country_name_map)
df_pop.set_index('Country', inplace=True)
df_pop.drop(columns=['log10_Pop'], inplace=True)
df_pop.to_csv(f"{output_dir}/cleaned_pop.csv")
print("Population cleaning complete. Cleaned data saved to output/cleaned_pop.csv.")

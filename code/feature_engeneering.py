"""
Feature Engineering Script

This script performs the following:
- Merges GDP, population, and demographics data
- Creates a TotalGDP feature: GDP per capita × Population
- Applies log10 transformation to GDP per capita and population
- Applies z-score normalization and saves the final feature matrix
- Generates required documentation and summary statistics

Run with:
    python feature_engineering.py
"""

import pandas as pd
from pathlib import Path
import numpy as np

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "output"
OUTFILE = DATA_DIR / "merged_with_total_gdp.csv"
X_PATH = DATA_DIR / "X.npy"
LOST_COUNTRIES_PATH = DATA_DIR / "lost_countries.csv"
OUT_STATS_PATH = DATA_DIR / "scaled_statistics.csv"
OUT_CRAWLED_SAMPLE = DATA_DIR / "crawled_sample.csv"
OUT_DEMO_STATS = DATA_DIR / "demographics_descriptive_stats.csv"
OUT_VERIFICATION = DATA_DIR / "verification_check.csv"

# -----------------------------------------------------------------------------
# Load Data
# -----------------------------------------------------------------------------
df_demo = pd.read_csv(DATA_DIR / "demographics_data.csv")
df_gdp = pd.read_csv(DATA_DIR / "cleaned_gdp.csv")
df_pop = pd.read_csv(DATA_DIR / "cleaned_pop.csv")

# Standardize column names and index
df_demo.columns = [col.strip() for col in df_demo.columns]
df_gdp.columns = [col.strip() for col in df_gdp.columns]
df_pop.columns = [col.strip() for col in df_pop.columns]

df_gdp.rename(columns={df_gdp.columns[-1]: "GDPperCapitaPPP"}, inplace=True)
df_pop.rename(columns={df_pop.columns[-1]: "Population"}, inplace=True)

for df in [df_demo, df_gdp, df_pop]:
    df.set_index("Country" if "Country" in df.columns else "country", inplace=True)
    df.index = df.index.str.strip()

# -----------------------------------------------------------------------------
# 5.4 Data Integration (inner join)
# -----------------------------------------------------------------------------
countries_before = set(df_demo.index) | set(df_gdp.index) | set(df_pop.index)
df_merged = df_demo.join(df_gdp, how="inner").join(df_pop, how="inner")
countries_after = set(df_merged.index)

# Save lost countries
df_lost = sorted(countries_before - countries_after)
pd.Series(df_lost, name="LostCountry").to_csv(LOST_COUNTRIES_PATH, index=False)

# -----------------------------------------------------------------------------
# Handle Missing Values
# -----------------------------------------------------------------------------
print("\n=== Missing Values Report ===")
missing_report = df_merged.isnull().sum()
missing_report = missing_report[missing_report > 0]
print(missing_report)

# Print the actual countries with missing values
for col in missing_report.index:
    missing_countries = df_merged[df_merged[col].isnull()].index.tolist()
    print(f"\nCountries missing '{col}' ({len(missing_countries)}):")
    for c in missing_countries:
        print(f" - {c}")


# Fill missing values in numeric columns
for col in df_merged.select_dtypes(include=["number"]).columns:
    if df_merged[col].isnull().any():
        df_merged[col].fillna(df_merged[col].mean(), inplace=True)

# Drop rows with missing values in categorical columns
non_numeric_cols = df_merged.select_dtypes(exclude=["number"]).columns
df_merged.dropna(subset=non_numeric_cols, inplace=True)

# -----------------------------------------------------------------------------
# 5.1 New Feature: Total GDP
# -----------------------------------------------------------------------------
df_merged = df_merged[df_merged["GDPperCapitaPPP"] > 0]
df_merged = df_merged[df_merged["Population"] > 0]
df_merged["TotalGDP"] = df_merged["GDPperCapitaPPP"] * df_merged["Population"]

# -----------------------------------------------------------------------------
# 5.2 Log Transforms
# -----------------------------------------------------------------------------
df_merged["LogGDPperCapita"] = np.log10(df_merged["GDPperCapitaPPP"].abs())
df_merged["LogPopulation"] = np.log10(df_merged["Population"].abs())

# -----------------------------------------------------------------------------
# 5.3 Scaling (Z-score Normalization)
# -----------------------------------------------------------------------------
def zscore(series):
    return (series - series.mean()) / series.std()

df_merged["life_expectancy_both_scaled"] = zscore(df_merged["life_expectancy_both"])
df_merged["LogGDPperCapita_scaled"] = zscore(df_merged["LogGDPperCapita"])
df_merged["LogPopulation_scaled"] = zscore(df_merged["LogPopulation"])

# -----------------------------------------------------------------------------
# Save Results
# -----------------------------------------------------------------------------
df_merged.to_csv(OUTFILE)

X = df_merged[[
    "life_expectancy_both_scaled",
    "LogGDPperCapita_scaled",
    "LogPopulation_scaled"
]].sort_index()

print("\n=== Preview of final X feature matrix ===")
print(X.head())
print(f"Shape: {X.shape}\n")

np.save(X_PATH, X.to_numpy())

print(f"Final merged data saved to: {OUTFILE.relative_to(PROJECT_ROOT)}")
print(f"Lost countries saved to: {LOST_COUNTRIES_PATH.relative_to(PROJECT_ROOT)}")
print(f"Feature matrix saved to: {X_PATH.relative_to(PROJECT_ROOT)}")

# -----------------------------------------------------------------------------
# 5.5 Deliverables — Documentation Section
# -----------------------------------------------------------------------------

# (1) Scaled feature statistics
scaled_columns = [
    "life_expectancy_both_scaled",
    "LogGDPperCapita_scaled",
    "LogPopulation_scaled"
]
scaled_stats = df_merged[scaled_columns].agg(["mean", "median", "std", "min", "max"]).T
scaled_stats.to_csv(OUT_STATS_PATH)

# (2) First 10 countries alphabetically
print("Number of countries in final dataset:", df_merged.shape[0])
print("First 10 countries (alphabetically):", sorted(df_merged.index)[:10])

# (3) Crawled demographics stats
demo_numeric = df_demo.select_dtypes(include=[np.number])
demo_stats = demo_numeric.agg(["mean", "median", "std", "min", "max"]).T
demo_stats.to_csv(OUT_DEMO_STATS)

# (4) Sample of crawled data
df_demo.head().to_csv(OUT_CRAWLED_SAMPLE, index=False)

# (5) Verification: presence of required fields
fields_to_verify = [
    "life_expectancy_both",
    "life_expectancy_female",
    "life_expectancy_male",
    "urban_population_percent",
    "urban_population_absolute",
    "population_density_km2"
]
verification_results = df_demo[fields_to_verify].notnull().sum().to_frame(name="Non-Null Count")
verification_results["Total Rows"] = df_demo.shape[0]
verification_results["Percent Filled"] = (verification_results["Non-Null Count"] / df_demo.shape[0]) * 100
verification_results.to_csv(OUT_VERIFICATION)

print("Documentation deliverables created.")

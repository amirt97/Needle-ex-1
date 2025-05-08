"""
Demographics Data Analysis and Cleaning

This script:
- Loads the demographic dataset
- Cleans invalid/missing values
- Normalizes country names (with manual corrections)
- Saves cleaning summary
- Produces summary statistics and correlation

Run with:
    python demographics_analysis.py
"""

from pathlib import Path
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
CODE_DIR = Path(__file__).resolve().parent
DATA_FILE = CODE_DIR.parent / "output" / "demographics_data.csv"
NAME_MISMATCH_FILE = CODE_DIR.parent / "output" / "name_mismatches.csv"
SUMMARY_STATS_FILE = CODE_DIR.parent / "output" / "summary_statistics.csv"
CLEANING_SUMMARY_FILE = CODE_DIR.parent / "output" / "cleaning_summary.txt"

# -----------------------------------------------------------------------------
# Load and convert
# -----------------------------------------------------------------------------
df = pd.read_csv(DATA_FILE)
df['country_original'] = df['country']

# Clean country names with title case but preserve known special cases
def smart_title(name: str) -> str:
    exceptions = {
        "Côte d'Ivoire": "Côte d'Ivoire",
        "DR Congo": "DR Congo",
        "U.S. Virgin Islands": "U.S. Virgin Islands",
        "Timor-Leste": "Timor-Leste",
        "Guinea-Bissau": "Guinea-Bissau",
        "State of Palestine": "State of Palestine",
        "Czech Republic (Czechia)": "Czech Republic (Czechia)",
        "Bosnia and Herzegovina": "Bosnia and Herzegovina",
        "Antigua and Barbuda": "Antigua and Barbuda",
        "Trinidad and Tobago": "Trinidad and Tobago",
    }
    cleaned = name.strip()
    if cleaned.lower().startswith("the "):
        cleaned = cleaned[4:]
    return exceptions.get(cleaned, cleaned.title())

df['country'] = df['country'].apply(smart_title)

# Save name mismatches
name_mismatches = df[df['country'] != df['country_original']][['country_original', 'country']]
name_mismatches.to_csv(NAME_MISMATCH_FILE, index=False)

# Set index for merging later
df.set_index('country', inplace=True)

# Convert numeric columns
numeric_fields = [
    "life_expectancy_both",
    "life_expectancy_female",
    "life_expectancy_male",
    "urban_population_percent",
    "urban_population_absolute",
    "population_density_km2",
]

df[numeric_fields] = df[numeric_fields].apply(pd.to_numeric, errors='coerce')

# -----------------------------------------------------------------------------
# Cleaning Logic
# -----------------------------------------------------------------------------
rows_before = df.shape[0]

# Remove missing/invalid life expectancy values (both)
df = df[df['life_expectancy_both'].between(40, 100)]
df = df[df['life_expectancy_both'].notna()]

rows_after_valid_life_exp = df.shape[0]

# -----------------------------------------------------------------------------
# Summary Statistics
# -----------------------------------------------------------------------------
summary = df[numeric_fields].agg(['mean', 'std', 'min', 'max', 'median']).T
summary['missing_values'] = df[numeric_fields].isnull().sum()

print("=== DataFrame Info ===")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}\n")

print("=== Summary Statistics ===")
print(summary)
summary.to_csv(SUMMARY_STATS_FILE)

# -----------------------------------------------------------------------------
# Pearson Correlation
# -----------------------------------------------------------------------------
print("\n=== Pearson Correlation ===")
if 'life_expectancy_both' in df.columns and 'population_density_km2' in df.columns:
    corr = df['life_expectancy_both'].corr(df['population_density_km2'])
    print(f"Pearson correlation between life_expectancy_both and population_density_km2: {corr:.4f}")
else:
    print("Required columns not found for correlation analysis.")

# -----------------------------------------------------------------------------
# Save cleaning summary
# -----------------------------------------------------------------------------
with open(CLEANING_SUMMARY_FILE, 'w') as f:
    f.write("Demographics Dataset Cleaning Summary\n")
    f.write("=====================================\n\n")
    f.write(f"Original row count: {rows_before}\n")
    f.write(f"Rows after removing invalid life expectancy: {rows_after_valid_life_exp}\n\n")
    f.write("Issues & Actions:\n")
    f.write("- Invalid life expectancy values (<40 or >100) → removed rows\n")
    f.write("- Missing life expectancy values → removed rows\n")
    f.write("- Country names normalized using smart_title() with manual exceptions\n")
    f.write("- Name mismatches logged in name_mismatches.csv\n")

print("\n✅ Cleaning summary written to cleaning_summary.txt")

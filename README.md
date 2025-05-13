# Dataset Cleaning and Feature Engineering for International Demographic and Economic Data

This repository contains scripts for cleaning and preparing data from GDP, Population, and Demographic datasets for further analysis and modeling.

## Project Structure

- `process_gdp_poplation_2021.py`: Initial exploration of raw GDP and Population datasets
- `population_and_gdp_data_cleaning.py`: Cleans and harmonizes GDP and Population datasets
- `demographics_crawler.py`: Crawls or loads external demographics data
- `demographics_analysis.py`: Cleans and normalizes the demographics dataset
- `feature_engeneering.py`: Merges datasets and performs final feature engineering for analysis and modeling

## Required Data Files

Place the following input files in the main project folder:

- `gdp_per_capita_2021.csv`
- `population_2021.csv`
- `output/demographics_data.csv` (produced after running `demographics_analysis.py`)

## Order of Operation

1. **Preview the raw data**
python process_gdp_poplation_2021.py

markdown
Copy
Edit
This produces summary files of the raw data (`output/` folder).

2. **Clean GDP and Population datasets**
python population_and_gdp_data_cleaning.py

markdown
Copy
Edit
- Cleans commas and non-numeric characters
- Removes missing values
- Detects outliers (Tukey method for GDP; log10 + Tukey for Population)
- Removes duplicates
- Maps country names to match the Demographics dataset to avoid country loss during merge

3. **(If needed) Crawl or update Demographics data**
python demographics_crawler.py

markdown
Copy
Edit

4. **Clean Demographics dataset**
python demographics_analysis.py

pgsql
Copy
Edit
- Cleans invalid life expectancy values (<40 or >100 years)
- Removes rows with missing life expectancy
- Normalizes country names using `smart_title()` + manual exceptions
- Logs any country name mismatches to `output/name_mismatches.csv`

5. **Perform Feature Engineering**
python feature_engeneering.py

markdown
Copy
Edit
- Merges cleaned GDP, Population, and Demographics datasets
- Prepares final dataset for analysis or modeling

## Outputs

Cleaned files and engineered dataset are stored in:
output/cleaned_gdp.csv
output/dropped_gdp.csv
output/cleaned_pop.csv
output/dropped_pop.csv
output/demographics_data.csv
output/X.npy

pgsql
Copy
Edit

## Notes

- Country name mapping between GDP/Population and Demographics was applied to ensure full alignment for merging.
- The pipeline must be run in the exact order shown above to avoid missing intermediate files.

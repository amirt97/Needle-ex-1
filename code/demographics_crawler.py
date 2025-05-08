# demographics_crawler.py
"""Crawl Worldometers demographics pages and build a clean CSV.

This script scrapes life expectancy, urban population, and population density data
from each country listed on Worldometers' demographics section.

Outputs are written **one level above this script** in a sibling *output/* folder, i.e.:

    Needle‑ex‑1/output/
        ├─ demographics_data.csv
        ├─ demographics_before_sort.csv
        └─ demographics_after_sort.csv

Run with:
    python demographics_crawler.py
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Paths & configuration
# -----------------------------------------------------------------------------
CODE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = CODE_DIR.parent
OUTPUT_DIR: Path = PROJECT_ROOT / "output"

BASE_URL: str = "https://www.worldometers.info"
START_URL: str = urljoin(BASE_URL, "/demographics/")
HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}
TIMEOUT: int = 30
RETRY_SLEEP: float = 2.0
MAX_RETRIES: int = 3

# -----------------------------------------------------------------------------
# Field keys to extract
# -----------------------------------------------------------------------------
NUMERIC_COLUMNS = [
    "life_expectancy_both",
    "life_expectancy_female",
    "life_expectancy_male",
    "urban_population_percent",
    "urban_population_absolute",
    "population_density_km2",
]


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def ensure_output_dir() -> None:
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def request_with_retry(url: str) -> requests.Response:
    """Request URL with retry logic for transient failures."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            if "checking your browser" in resp.text.lower():
                raise RuntimeError("Cloudflare challenge – retrying")
            return resp
        except (requests.HTTPError, RuntimeError) as exc:
            if attempt == MAX_RETRIES:
                raise
            print(f"Retry {attempt}/{MAX_RETRIES} for {url}: {exc}")
            time.sleep(RETRY_SLEEP)
    raise RuntimeError("Exceeded max retries")


def fetch_html(url: str) -> BeautifulSoup:
    """Fetch HTML and parse with BeautifulSoup."""
    return BeautifulSoup(request_with_retry(url).text, "html.parser")


# -----------------------------------------------------------------------------
# Country link extraction (for full script mode)
# -----------------------------------------------------------------------------

def extract_country_links(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    """Extract country links from the main demographics page."""
    links: List[Tuple[str, str]] = []
    seen: set[str] = set()

    # First try to find links in the "Demographics of Countries" section
    section = soup.find(["h2", "h3"], string=re.compile("Demographics of Countries", re.I))
    if section:
        # Try to find a list (ul) following the section header
        ul = section.find_next("ul")
        if ul:
            for a in ul.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/demographics/"):
                    abs_url = urljoin(BASE_URL, href)
                    country_name = a.get_text(strip=True)
                    if abs_url not in seen:
                        seen.add(abs_url)
                        links.append((country_name, abs_url))

    # If no links found yet, try an alternative approach
    if not links:
        # Look for any div that might contain the country listing
        for div in soup.find_all("div"):
            if "Demographics of Countries" in div.get_text():
                for a in div.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("/demographics/") and "/world/" not in href:
                        abs_url = urljoin(BASE_URL, href)
                        country_name = a.get_text(strip=True)
                        if abs_url not in seen:
                            seen.add(abs_url)
                            links.append((country_name, abs_url))

    # If still no links, try a broader approach
    if not links:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/demographics/") and "/world/" not in href:
                # Filter out non-country links
                if re.search(r"/demographics/[a-z\-]+(-demographics)?/?$", href):
                    abs_url = urljoin(BASE_URL, href)
                    country_name = a.get_text(strip=True)
                    if not country_name:  # If link text is empty, extract from URL
                        slug = href.strip("/").split("/")[-1]
                        if slug.endswith("-demographics"):
                            slug = slug[:-len("-demographics")]
                        country_name = slug.replace("-", " ").title()

                    if abs_url not in seen:
                        seen.add(abs_url)
                        links.append((country_name, abs_url))

    return links


# -----------------------------------------------------------------------------
# Data extraction logic (handles new HTML layout)
# -----------------------------------------------------------------------------

def extract_country_data(name: str, url: str) -> Dict[str, Any]:
    """Extract demographic data from a country page."""
    soup = fetch_html(url)
    record: Dict[str, Any] = {"country": name}

    # ── Life Expectancy blocks ───────────────────────────────────────────────
    for block in soup.find_all("div", class_="p-4"):
        label_el = block.find_previous("div", class_=re.compile("text-xl", re.I))
        value_el = block.find("div", class_="text-2xl")
        if not label_el or not value_el:
            continue
        label = label_el.get_text(strip=True).lower()
        value = value_el.get_text(strip=True).replace(",", "")
        if "both sexes" in label:
            record["life_expectancy_both"] = value
        elif "females" in label:
            record["life_expectancy_female"] = value
        elif "males" in label:
            record["life_expectancy_male"] = value

    # --- Urban Population ---------------------------------------------------
    # Look for the urban population paragraph directly
    urban_heading = soup.find(["h2", "h3"], id="urb") or soup.find(["h2", "h3"],
                                                                   string=re.compile("Urban Population", re.I))

    if urban_heading:
        # Find the paragraph following the urban population heading
        urban_para = urban_heading.find_next("p")
        if urban_para:
            # Extract the data using the specific pattern
            urban_text = urban_para.get_text(strip=True)
            percent_match = re.search(r"(\d+\.\d+)%", urban_text)
            if percent_match:
                record["urban_population_percent"] = percent_match.group(1)

            absolute_match = re.search(r"\(([\d,]+)\s*people", urban_text)
            if absolute_match:
                record["urban_population_absolute"] = absolute_match.group(1).replace(",", "")

    # If not found by HTML structure, try regex on the full page text
    if "urban_population_percent" not in record or "urban_population_absolute" not in record:
        page_text = soup.get_text("\n")
        # Pattern to match "Currently, XX.X% of the population is urban (XX,XXX,XXX people in YYYY)"
        m_urban = re.search(
            r"Currently[^\n]*?([\d.]+)%[^\n]*?\(([\d,\s]+)\s*people",
            page_text,
            flags=re.IGNORECASE,
        )
        if m_urban:
            record["urban_population_percent"] = m_urban.group(1)
            record["urban_population_absolute"] = re.sub(r"[\s,]", "", m_urban.group(2))

    # --- Population Density -------------------------------------------------
    # Try to find population density in structured sections
    density_heading = soup.find(["h2", "h3"], string=re.compile("Population Density", re.I))
    if density_heading:
        density_para = density_heading.find_next("p")
        if density_para:
            density_text = density_para.get_text(strip=True)
            density_match = re.search(r"(\d+\.?\d*)\s*people per km", density_text)
            if density_match:
                record["population_density_km2"] = density_match.group(1)

    # If not found, try regex on full page text
    if "population_density_km2" not in record:
        page_text = soup.get_text("\n")
        m_density = re.search(
            r"population density[^\n]*?is\s*([\d.]+)\s*people per km",
            page_text,
            flags=re.IGNORECASE,
        )
        if m_density:
            record["population_density_km2"] = m_density.group(1)

    # fill missing keys
    for key in NUMERIC_COLUMNS:
        record.setdefault(key, None)

    return record


# -----------------------------------------------------------------------------
# DataFrame utilities
# -----------------------------------------------------------------------------

def convert_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Convert string fields to appropriate numeric types."""
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def save_head(df: pd.DataFrame, fname: str, label: str) -> None:
    """Save the first 10 rows to CSV and print to console."""
    df.head(10).to_csv(OUTPUT_DIR / fname, index=False)
    print(f"\n=== FIRST 10 ROWS ({label}) ===")
    print(df.head(10))


# -----------------------------------------------------------------------------
# Main function - crawl all countries
# -----------------------------------------------------------------------------

def main() -> None:
    """Main function to crawl all countries and extract data."""
    ensure_output_dir()

    print("Fetching country list...")
    soup = fetch_html(START_URL)
    countries = extract_country_links(soup)

    print(f"Found {len(countries)} countries. Starting extraction...")

    if not countries:
        raise RuntimeError("No country links found. Website structure may have changed.")

    records: List[Dict[str, Any]] = []

    for i, (country_name, country_url) in enumerate(countries, 1):
        try:
            print(f"[{i}/{len(countries)}] Processing {country_name}...", end=" ")
            country_data = extract_country_data(country_name, country_url)
            records.append(country_data)
            print("✓")
            # Be nice to the server
            time.sleep(0.5)
        except Exception as e:
            print(f"✗ Error: {e}")

    # Create DataFrame and convert numeric fields
    df_demographics = pd.DataFrame(records)
    df_demographics = convert_numeric_fields(df_demographics)

    # Save full dataset
    df_demographics.to_csv(OUTPUT_DIR / "demographics_data.csv", index=False)

    # Save and display first 10 rows (before sorting)
    save_head(df_demographics, "demographics_before_sort.csv", "Before Sort")

    # Sort by country and save first 10 rows
    df_sorted = df_demographics.sort_values("country")
    save_head(df_sorted, "demographics_after_sort.csv", "After Sort")

    print(f"\nFiles written to: {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()



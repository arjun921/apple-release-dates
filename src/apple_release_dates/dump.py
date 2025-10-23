"""Apple product data fetching from Wikipedia.

This module scrapes Apple product release dates and information from Wikipedia and saves
it as JSON and CSV files in the data/ directory.

Usage:
    python -m apple_release_dates.dump

Output files:
    data/apple_products.json - Product data in JSON format
    data/apple_products.csv - Product data in CSV format with preferred columns ordered first
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import pandas as pd
import sys
import re
from pathlib import Path
from datetime import datetime


def is_future_date(date_text: str) -> bool:
    """Check if a date string represents a future date."""
    try:
        date = datetime.strptime(date_text, "%B %d, %Y")
        return date > datetime.now()
    except ValueError:
        return False


def is_date_string(text: str) -> bool:
    """Check if a string appears to be a date."""
    if not text:
        return False
    date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
    return bool(re.search(date_pattern, text))


def fix_mixed_fields(product_data: dict) -> dict:
    """Fix fields that might have been mixed up (e.g. dates in Model field)."""
    # Look for dates in wrong fields
    for field in ["Model", "Family"]:
        if field in product_data and is_date_string(product_data[field]):
            # If Released is empty or not a date, and we found a date in another field
            if "Released" not in product_data or not is_date_string(
                product_data["Released"]
            ):
                # Move the date to Released
                product_data["Released"] = normalize_field(
                    product_data[field], "Released"
                )
                # Clear the original field
                product_data[field] = ""

    # Clean up any remaining fields
    for field in ["Released", "Model", "Family", "Discontinued"]:
        if field in product_data:
            product_data[field] = normalize_field(product_data[field], field)

    # Add status flags for future release dates
    if "Released" in product_data and is_date_string(product_data["Released"]):
        is_future = is_future_date(product_data["Released"])
        product_data["Future release"] = str(is_future).lower()

    return product_data


def fetch_wikipedia_page(url: str, timeout: int = 10) -> str:
    """Fetch page text from the given URL using a session with retries and a User-Agent.

    Raises requests.HTTPError on non-2xx responses.
    """
    session = requests.Session()

    # Set a sensible User-Agent to avoid being blocked by Wikipedia
    session.headers.update(
        {
            "User-Agent": "apple-release-dates-bot/1.0 (+https://github.com/arjun921/apple-release-dates)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    # Retries for transient network or server errors
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def normalize_field(text: str, field_type: str) -> str:
    """Normalize field values based on their type."""
    if not text:
        return ""

    text = text.strip()

    if field_type == "Released":
        # Look for date patterns
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
        match = re.search(date_pattern, text)
        if match:
            return match.group(0)
    elif field_type == "Model":
        # Clean up common issues in model names
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        text = text.replace(" . ", ".")  # Fix dot spacing

        # Remove any date patterns from model names
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
        text = re.sub(date_pattern, "", text).strip()
    elif field_type == "Family":
        # Normalize family names
        text = text.replace(".", "")  # Remove dots
        text = text.strip()  # Remove extra whitespace
        # Remove any date patterns from family field
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
        text = re.sub(date_pattern, "", text).strip()
    elif field_type == "Discontinued":
        # Clean up discontinued dates
        text = text.replace("present", "current")
        text = text.replace("Present", "current")
        text = text.replace("Current", "current")

    return text


def parse_table(table_soup) -> list[dict]:
    """Parse a Wikipedia table into list of row dictionaries."""
    print("\nProcessing new table...")

    # First pass: Get headers and determine max column count
    headers = []
    max_cols = 0

    # Try to find headers first
    header_row = table_soup.find("tr")
    if header_row:
        for header in header_row.find_all(["th", "td"]):
            header_text = header.get_text().strip().replace("\n", " ")
            if header_text:  # Only add non-empty headers
                # Normalize common header variations
                if "release" in header_text.lower():
                    header_text = "Released"
                elif "model" in header_text.lower() or "product" in header_text.lower():
                    header_text = "Model"
                elif "family" in header_text.lower() or "type" in header_text.lower():
                    header_text = "Family"
                elif (
                    "discontinued" in header_text.lower()
                    or "status" in header_text.lower()
                ):
                    header_text = "Discontinued"
                headers.append(header_text)
            else:
                headers.append(f"Column_{len(headers) + 1}")
        print(f"Found headers: {headers}")

    # Skip tables that don't look like product tables
    if not headers or not any(
        h in ["Released", "Model", "Family", "Discontinued"] for h in headers
    ):
        print("Skipping table - no valid headers found")
        return []

    rows = []
    current_release_date = None

    # Process data rows
    for row in table_soup.find_all("tr")[1:]:  # Skip header row
        cells = row.find_all(["td", "th"])

        # Skip completely empty rows
        if not cells or not any(cell.get_text(strip=True) for cell in cells):
            continue

        # Get text from each cell
        cell_data = []
        for cell in cells:
            # Check if this cell spans multiple rows
            rowspan = int(cell.get("rowspan", 1))
            cell_text = cell.get_text(strip=True)

            # If this is a date and spans multiple rows, it's a release date
            if rowspan > 1 and is_date_string(cell_text):
                current_release_date = cell_text
                continue

            cell_data.append(cell_text)

        # If first cell contains a date but no rowspan, it might be a release date
        if cell_data and is_date_string(cell_data[0]):
            current_release_date = cell_data[0]
            continue

        # Need at least model and family to create a product
        if len(cell_data) < 2:
            continue

        product_data = {
            "Released": current_release_date or "",
            "Model": cell_data[0] if len(cell_data) > 0 else "",
            "Family": cell_data[1] if len(cell_data) > 1 else "",
            "Discontinued": cell_data[2] if len(cell_data) > 2 else "current",
        }

        # Look for source link in the model cell
        first_cell = cells[0] if cells else None
        if first_cell:
            link = first_cell.find("a", href=True)
            if link and "href" in link.attrs:
                product_data["Source link"] = "https://en.wikipedia.org" + link["href"]

        # Fix any mixed up fields
        product_data = fix_mixed_fields(product_data)

        # Only add product if we have a model name or proper release date
        if (
            product_data.get("Model") and not is_date_string(product_data["Model"])
        ) or (
            product_data.get("Released") and is_date_string(product_data["Released"])
        ):
            rows.append(product_data)

    return rows


def scrape_wiki_page(url: str) -> list[dict]:
    """Scrape tables from a Wikipedia page."""
    html = fetch_wikipedia_page(url)
    soup = BeautifulSoup(html, "html.parser")

    all_data = []
    for table in soup.find_all("table", class_="wikitable"):
        rows = parse_table(table)
        all_data.extend(rows)

    return all_data


def dump_data(data: list[dict], output_dir: Path) -> None:
    """Save data as JSON and CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter out any entries that don't look like proper product data
    filtered_data = []
    for item in data:
        if "Model" in item and item["Model"] and "Source link" in item:
            # Normalize data
            for field in ["Released", "Model", "Family", "Discontinued"]:
                if field in item:
                    item[field] = normalize_field(item[field], field)

            # Ensure Future release flag exists
            if "Released" in item and is_date_string(item["Released"]):
                is_future = is_future_date(item["Released"])
                item["Future release"] = str(is_future).lower()

            filtered_data.append(item)

    # Save as JSON
    json_path = output_dir / "apple_products.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(filtered_data)} products to {json_path}")

    # Save as CSV using pandas for better handling
    csv_path = output_dir / "apple_products.csv"
    df = pd.DataFrame(filtered_data)

    # Prefer important columns first
    preferred_cols = [
        "Released",
        "Model",
        "Family",
        "Discontinued",
        "Future release",  # Add future release column
        "Source link",
    ]
    cols = [col for col in preferred_cols if col in df.columns]
    cols.extend([col for col in df.columns if col not in preferred_cols])

    df = df[cols]
    # Remove completely empty rows
    df = df.dropna(how="all")
    # Sort by release date
    df["Released"] = pd.to_datetime(df["Released"], format="%B %d, %Y", errors="coerce")
    df = df.sort_values("Released", ascending=True)
    df["Released"] = df["Released"].dt.strftime("%B %d, %Y")
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")


def main() -> int:
    """Main entry point for dumping Apple product data."""
    # Only scrape the single "List of Apple products" page as requested by the user.
    urls = [
        "https://en.wikipedia.org/wiki/List_of_Apple_products",
    ]

    try:
        # Try to find the repository root by looking for key files/folders
        module_dir = Path(__file__).resolve().parent
        repo_root = None

        # Look up to 4 levels up for the repository root
        for parent in [module_dir, *module_dir.parents[:4]]:
            if (parent / "pyproject.toml").exists() and (parent / "data").exists():
                repo_root = parent
                break

        if not repo_root:
            # Fallback to current working directory if repository root not found
            repo_root = Path.cwd()
            print(
                f"Warning: Using current directory as root: {repo_root}",
                file=sys.stderr,
            )

        output_dir = repo_root / "data"
        print(f"Using output directory: {output_dir}", file=sys.stderr)

        all_data = []
        for url in urls:
            print(f"Fetching {url}...", file=sys.stderr)
            try:
                page_data = scrape_wiki_page(url)
                all_data.extend(page_data)
                print(f"Found {len(page_data)} products", file=sys.stderr)
            except Exception as e:
                print(f"Error scraping {url}: {e}", file=sys.stderr)
                continue

        if not all_data:
            print("No data was collected!", file=sys.stderr)
            return 1

        dump_data(all_data, output_dir)
        print(f"Total products collected: {len(all_data)}", file=sys.stderr)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

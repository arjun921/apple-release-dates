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
from pathlib import Path


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


def parse_table(table_soup) -> list[dict]:
    """Parse a Wikipedia table into list of row dictionaries."""
    headers = []
    for header in table_soup.find_all("th"):
        # Clean and normalize header text
        header_text = header.get_text().strip()
        header_text = header_text.replace("\n", " ")
        headers.append(header_text)

    if not headers and table_soup.find("tr"):
        # Try first row cells if no th found
        headers = [
            cell.get_text(strip=True)
            for cell in table_soup.find("tr").find_all(["td", "th"])
        ]

    if not headers:
        return []  # Skip tables with no headers

    rows = []
    for row in table_soup.find_all("tr")[1:]:  # Skip header row
        cells = row.find_all(["td", "th"])
        if len(cells) >= len(headers):  # Only process rows with enough cells
            product_data = {}
            for header, cell in zip(headers, cells):
                # Clean and normalize cell text
                cell_text = cell.get_text().strip()
                cell_text = cell_text.replace("\n", " ")
                product_data[header] = cell_text

                # Add source link for Model cells
                if header == "Model" or header == "Product":
                    link_tag = cell.find("a", href=True)
                    if link_tag and "href" in link_tag.attrs:
                        product_data["Source link"] = (
                            "https://en.wikipedia.org" + link_tag["href"]
                        )

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

    # Save as JSON
    json_path = output_dir / "apple_products.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} products to {json_path}")

    # Save as CSV using pandas for better handling
    csv_path = output_dir / "apple_products.csv"
    df = pd.DataFrame(data)

    # Prefer important columns first
    preferred_cols = [
        "Model",
        "Product",
        "Family",
        "Released",
        "Discontinued",
        "Source link",
    ]
    cols = [col for col in preferred_cols if col in df.columns]
    cols.extend([col for col in df.columns if col not in preferred_cols])

    df = df[cols]
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")


def main() -> int:
    """Main entry point for dumping Apple product data."""
    urls = [
        "https://en.wikipedia.org/wiki/Timeline_of_Apple_Inc._products",
    ]

    try:
        output_dir = Path(__file__).resolve().parents[3] / "data"

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

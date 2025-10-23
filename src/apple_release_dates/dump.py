#!/usr/bin/env python3
"""Script to dump Apple product data from Wikipedia."""
from apple_release_dates.dump import main

if __name__ == "__main__":
    raise SystemExit(main())
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


def extract_products_from_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    products = []

    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        # Some tables may not have header row structured the same way - guard against that
        header_cells = rows[0].find_all(["th", "td"])
        headers = [th.get_text(strip=True) for th in header_cells]

        current_rowspans = {
            header: {"value": None, "remaining": 0} for header in headers
        }

        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue

            product_data = {}
            col_index = 0

            for header in headers:
                if current_rowspans[header]["remaining"] > 0:
                    product_data[header] = current_rowspans[header]["value"]
                    current_rowspans[header]["remaining"] -= 1
                else:
                    if col_index < len(cells):
                        cell = cells[col_index]
                        value = cell.get_text(strip=True)

                        if "rowspan" in cell.attrs:
                            current_rowspans[header] = {
                                "value": value,
                                "remaining": int(cell.attrs["rowspan"]) - 1,
                            }
                        else:
                            current_rowspans[header] = {"value": value, "remaining": 0}

                        product_data[header] = value

                        if header == "Model":
                            link_tag = cell.find("a", href=True)
                            product_data["Source link"] = (
                                "https://en.wikipedia.org" + link_tag["href"]
                                if link_tag
                                else None
                            )

                        col_index += 1
                    else:
                        product_data[header] = current_rowspans[header]["value"]

            # Fill missing headers with empty string
            for header in headers:
                if header not in product_data or product_data[header] is None:
                    product_data[header] = current_rowspans.get(header, {}).get(
                        "value", ""
                    )

            # Fallback: try to get family link when Model link is missing
            if "Model" in product_data and not product_data.get("Source link"):
                try:
                    family_index = headers.index("Family")
                    if family_index < len(cells):
                        family_link_tag = cells[family_index].find("a", href=True)
                        product_data["Source link"] = (
                            "https://en.wikipedia.org" + family_link_tag["href"]
                            if family_link_tag
                            else None
                        )
                except ValueError:
                    # No Family column
                    pass

            products.append(product_data)

    return products


def save_products(
    products: list,
    json_path: str = "data/apple_products.json",
    csv_path: str = "data/apple_products.csv",
):
    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"Successfully extracted {len(products)} products to {json_path}")

    # Write CSV in a safe way - only include columns that exist
    if products:
        df = pd.DataFrame(products)
        preferred = ["Released", "Model", "Family", "Discontinued", "Source link"]
        cols = [c for c in preferred if c in df.columns]
        # If none of the preferred columns exist, just write whatever we have
        if not cols:
            cols = df.columns.tolist()

        df = df[cols]
        df.columns = df.columns.str.lower()
        df.to_csv(csv_path, index=False)
        print(f"Successfully exported to {csv_path}")
    else:
        print("No products to write to CSV")


def main(argv=None):
    argv = argv or sys.argv[1:]
    url = "https://en.wikipedia.org/wiki/List_of_Apple_products"

    try:
        html = fetch_wikipedia_page(url)
    except requests.HTTPError as e:
        print(f"HTTP error while fetching {url}: {e}")
        return 2
    except requests.RequestException as e:
        print(f"Network error while fetching {url}: {e}")
        return 3

    products = extract_products_from_html(html)
    save_products(products)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

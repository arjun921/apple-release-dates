import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

# URL of the Wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_Apple_products"

# Send a GET request to fetch the page content
response = requests.get(url)
response.raise_for_status()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Initialize a list to store product information
products = []

# Find all tables on the page
tables = soup.find_all("table", {"class": "wikitable"})

# Process each table
for table in tables:
    rows = table.find_all("tr")

    # Extract headers
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    # Initialize a dictionary to track rowspans for each column
    current_rowspans = {header: {"value": None, "remaining": 0} for header in headers}

    # Process each row, skipping the header
    for row in rows[1:]:
        cells = row.find_all("td")
        if not cells:
            continue  # Skip empty rows

        # Initialize a dictionary for the current row's data
        product_data = {}
        col_index = 0  # Track column position in the row

        for header in headers:
            # Handle rowspan propagation
            if current_rowspans[header]["remaining"] > 0:
                product_data[header] = current_rowspans[header]["value"]
                current_rowspans[header]["remaining"] -= 1
            else:
                # Assign value from the current cell
                if col_index < len(cells):
                    cell = cells[col_index]
                    value = cell.get_text(strip=True)

                    # Handle new rowspan
                    if "rowspan" in cell.attrs:
                        current_rowspans[header] = {
                            "value": value,
                            "remaining": int(cell.attrs["rowspan"]) - 1,
                        }
                    else:
                        current_rowspans[header] = {"value": value, "remaining": 0}

                    product_data[header] = value

                    # Extract and store the source link for the "Model" column
                    if header == "Model":
                        link_tag = cell.find("a", href=True)
                        product_data["Source link"] = (
                            "https://en.wikipedia.org" + link_tag["href"]
                            if link_tag
                            else None
                        )

                    col_index += 1
                else:
                    # If no cell exists, use the previous rowspan value
                    product_data[header] = current_rowspans[header]["value"]

        # Propagate remaining rowspans into the current row
        for header in headers:
            if header not in product_data or not product_data[header]:
                product_data[header] = current_rowspans.get(header, {}).get("value", "")

        # Fallback to the Family link if Source link is missing
        if "Model" in product_data and not product_data.get("Source link"):
            family_index = headers.index("Family")
            if family_index < len(cells):
                family_link_tag = cells[family_index].find("a", href=True)
                product_data["Source link"] = (
                    "https://en.wikipedia.org" + family_link_tag["href"]
                    if family_link_tag
                    else None
                )

        # Append the product to the list
        products.append(product_data)

# Write to JSON
output_file = "data/apple_products.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=4)

print(f"Successfully extracted {len(products)} products to {output_file}")

# Write to CSV
output_csv = "data/apple_products.csv"

df = pd.DataFrame(products)

# Reorder the columns for CSV
columns_order = ["Released", "Model", "Family", "Discontinued", "Source link"]
df = df[columns_order]

df.columns = df.columns.str.lower()

df.to_csv(output_csv, index=False)
print(f"Successfully exported to {output_csv}")

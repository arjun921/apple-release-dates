import pandas as pd
from pathlib import Path

from helpers import generate_categories, generate_tags, make_path_safe

# Read the CSV
df = pd.read_csv("data/apple_products.csv")

# Print original column names for debugging
print("Original columns:", df.columns.tolist())

# Convert column names to lowercase and standardize format
df.columns = df.columns.str.lower().str.replace(" ", "_")

# Print converted column names for debugging
print("Converted columns:", df.columns.tolist())

# Add date conversion with explicit error handling
try:
    df["released"] = pd.to_datetime(df["released"], format="%B %d, %Y")
except KeyError as e:
    print(f"Error: Column not found: {e}")
    print("Available columns:", df.columns.tolist())
    raise
except Exception as e:
    print(f"Error converting date: {e}")
    raise


def generate_page(data):
    categories = generate_categories(data)
    tags = generate_tags(data)
    date = data.released.strftime("%Y-%m-%d %H:%M:%S")
    title = data.model
    # escape " in title
    title = title.replace('"', '\\"')
    page_format = f"""+++
ShowToc = false
categories = {categories}
date = {date}
title = "{title}"
tags = {tags}
summary = " "

+++

The {data.model} was released on {data.released}.

Source: `{data.get('source_link', 'Not available')}`


"""
    return page_format


df.dropna(subset=["model"], inplace=True)

parent_map = {
    # key: replaced with value
    "Accessories": "Accessories",
    "Apple I": "Computers and Accessories",
    "iPhone": "iPhone",
    "iPod": "iPod",
    "AirPort": "AirPort",
    "Display": "Displays",
    "iMac": "Mac/iMac",
    "Mac II": "Mac/Mac II",
    "Mac Mini": "Mac/Mac Mini",
    "Mac Pro": "Mac/Mac Pro",
    "Mac Studio": "Mac/Mac Studio",
    "MacBook": "Mac/MacBook",
    "MacBook Air": "Mac/MacBook Air",
    "MacBook Pro": "Mac/MacBook Pro",
}

for index, row in df.iterrows():
    destination = Path("content/posts")
    family = str(row.family)
    model = str(row.model)
    # make model urlsafe
    print(model)
    model = make_path_safe(model)

    print(model)

    for parent in parent_map.keys():
        if parent in family:
            family = parent_map[parent]

    destination = destination / family
    # create the directory if it doesn't exist
    destination.mkdir(parents=True, exist_ok=True)
    # add one more column to the row
    row["destination"] = destination
    page = generate_page(row)
    # remove special characters from the model

    with open(destination / f"{model}.md", "w") as f:
        f.write(page)

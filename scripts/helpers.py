import re
import pandas as pd


def generate_tags(data):
    tags = []
    tags.append(data.family)
    # tags.append(data.model)
    tags.append(data.released.strftime("%Y"))
    return tags


def generate_categories(data):
    categories = []
    family = str(data.family) if pd.notna(data.family) else "Uncategorized"
    categories.append(family)
    # categories.append(data.model)
    categories.append(data.released.strftime("%Y"))
    if pd.notna(data.family) and "accessories" in str(data.family).lower():
        categories.append("Accessories")

    for folder in data.destination.parts:
        if folder in ["content", "posts"]:
            continue
        categories.append(folder)
    return categories


def make_path_safe(string):
    # Replace any character that is not alphanumeric, space, hyphen, or underscore with an underscore
    return re.sub(r"[^\w\s\-\(\)\"]", "_", string).strip()

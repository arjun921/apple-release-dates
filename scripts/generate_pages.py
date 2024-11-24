import pandas as pd
from pathlib import Path

df = pd.read_csv('data/apple_products.csv')

# set date to datetime
df['released'] = pd.to_datetime(df['released'], format="mixed")

def generate_page(data):
    
    categories=[data.family]

    date = data.released.strftime('%Y-%m-%d %H:%M:%S')
    title = data.model
    # escape " in title
    title = title.replace('"', '\\"')
    # tags = ['iPad Pro 12.9 Inch', '2020', 'iPad Pro']
    tags = []
    tags.extend(categories)

    body = f"The {data.model} was released on {data.released}."

    page_format = f"""+++
ShowToc = false
categories = {categories}
date = {date}
title = "{title}"
tags = {tags}

+++

{body}

Source: `{data.get('source link', 'Not available')}`


"""
    return page_format

df.dropna(subset=['model'], inplace=True)

parent_map = {
    "Accessories": "Accessories",
    "Apple I": "Computers and Accessories",
    "iPhone": "iPhone",
    "iPod": "iPod",
    "AirPort": "AirPort",
    "Display": "Displays"
}

for index, row in df.iterrows():
    destination = Path('content/posts')
    family = str(row.family)
    model = str(row.model)
    # replace all special characters in model
    model = ''.join(e for e in model if e.isalnum())

    for parent in parent_map.keys():
        if parent in family:
            family = parent_map[parent]

    # if ' ' in family:
    #     split_family = family.split(' ')
    #     for family_partial in split_family:
    #         destination = destination / family_partial

    # else:

    destination = destination / family
    # create the directory if it doesn't exist
    destination.mkdir(parents=True, exist_ok=True)
    page = generate_page(row)
    # remove special characters from the model
    
    with open(destination / f'{model}.md', 'w') as f:
        f.write(page)
# Apple Release Dates

![Weekly Pipeline](https://github.com/arjun921/apple-release-dates/actions/workflows/weekly-update.yml/badge.svg)
[![Netlify Status](https://api.netlify.com/api/v1/badges/89da98e3-1c46-4909-aec1-48d7d90d4f99/deploy-status)](https://app.netlify.com/sites/jovial-beaver-6d753f/deploys)

This repository contains a list of Apple product release dates. The data is stored in a JSON file and is updated weekly using GitHub Actions.

## Data
The data is stored in a JSON file named `data/apple_products.json`. The JSON file contains the following fields:

```
{
    "Released": "September 20, 2024",
    "Model": "Apple Watch Series 10",
    "Source link": "https://en.wikipedia.org/wiki/Apple_Watch",
    "Family": "Apple Watch",
    "Discontinued": "current"
}
```

There's also a `data/apple_products.csv` file that contains the same data in CSV format.

# Usage
You can use this package to fetch Apple product data in two ways:

1. As a command line tool:
```bash
# Install the package
pip install .

# Fetch the latest data
dump-apple
```

2. As a Python library:
```python
from apple_release_dates.dump import main
main()
```

The data will be saved to `data/apple_products.json` and `data/apple_products.csv`.

# Scripts
The `scripts` folder contains additional tools:
- `generate_pages.py`: Converts the CSV file to posts on the website
- `dump_apple.py`: Simplified entry point for the data fetcher

# Website
The webpage is based on Hugo and hosted on Netlify.

# Contributing
If you have any suggestions or would like to contribute, feel free to open an issue or a pull request!

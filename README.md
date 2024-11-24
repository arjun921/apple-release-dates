# Apple Release Dates

![Weekly Pipeline](https://github.com/arjun921/apple-release-dates/actions/workflows/weekly-update.yml/badge.svg)

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

# Scripts
The `scripts` folder contains Python scripts to scrape the release dates from Wikipedia and update the JSON file.
It also has a script that converts the CSV file to a post on the website. 

# Website
The webpage is based on Hugo and hosted on Netlify.

# Contributing
If you have any suggestions or would like to contribute, feel free to open an issue or a pull request!

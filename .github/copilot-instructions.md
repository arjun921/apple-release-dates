# Copilot Instructions for AI Coding Agents

## Project Overview
- **Purpose:** Collect, process, and publish Apple product release dates using Python scripts and Hugo static site generator.
- **Data Sources:** Main data is fetched from Wikipedia and stored in `data/apple_products.json` and `data/apple_products.csv`.
- **Website:** Content is generated for a Hugo site (see `content/`), deployed via Netlify.

## Key Components
- **Data Fetching:**
  - `src/apple_release_dates/dump.py`: Scrapes Wikipedia for product data, saves to JSON/CSV.
  - `scripts/dump_apple.py`: CLI entry point for data dump (calls `main()` from above).
- **Content Generation:**
  - `scripts/generate_pages.py`: Converts CSV data to Markdown posts for Hugo. Uses helpers in `scripts/helpers.py`.
  - `scripts/helpers.py`: Contains utility functions for tags, categories, and safe filenames.
- **Configuration:**
  - `pyproject.toml`: Python package metadata, dependencies, and CLI script registration.
  - `netlify.toml`: Netlify deployment settings.
  - `config.yml`, `configTaxo.yml`: Hugo site configuration.

## Developer Workflows
- **Build/Install:**
  - Install dependencies: `pip install .` (requires Python >=3.12)
- **Data Update:**
  - Run data fetch: `python -m apple_release_dates.dump` or `dump-apple` (CLI)
- **Content Generation:**
  - Generate posts: `python scripts/generate_pages.py`
- **Testing:**
  - No formal test suite detected; validate changes by running scripts and inspecting output files.
- **Deployment:**
  - Automated weekly update via GitHub Actions (`.github/workflows/weekly-update.yml`).
  - Netlify auto-deploys site on content changes.

## Patterns & Conventions
- **Data Model:**
  - Product fields: `Released`, `Model`, `Source link`, `Family`, `Discontinued`.
  - CSV/JSON columns must match these fields for downstream scripts.
- **Markdown Generation:**
  - Posts are created in `content/posts/<Family>/<Model>.md`.
  - Use helpers for tags/categories to ensure consistency.
- **Error Handling:**
  - Data fetch uses retries and custom User-Agent to avoid Wikipedia blocks.
- **Extensibility:**
  - Add new product families by updating `parent_map` in `generate_pages.py`.

## Integration Points
- **External:**
  - Wikipedia (data source)
  - Netlify (hosting)
  - GitHub Actions (automation)
- **Internal:**
  - Scripts communicate via shared data files (`data/`), not direct imports.

## Examples
- To fetch and update product data:
  ```bash
  dump-apple
  ```
- To generate new Hugo posts:
  ```bash
  python scripts/generate_pages.py
  ```

---
If any section is unclear or missing, please provide feedback for further refinement.

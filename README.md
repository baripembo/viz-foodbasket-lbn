# Lebanon Food Basket Price Visualization

An interactive chart showing week-over-week and year-over-year price changes for 60 food commodities tracked by Lebanon's Ministry of Economy and Trade.

## Data source

Weekly food basket reports published by the [Ministry of Economy and Trade — Price Policy Technical Office](https://www.economy.gov.lb/en/services/center-for-pricing-policies/mini---basket-weekly-).

Place the translated Excel report (e.g. `weekly-basket-report-16-03-2026-EN.xlsx`) in the `data/` directory before running.

## Local development

```bash
# Install dependencies
uv sync

# Generate data from the Excel file
uv run python generate_data.py

# Serve the dashboard locally
python3 -m http.server 8000
# Open http://localhost:8000
```

> A local server is required — the chart fetches `data/foodbasket.json` at runtime and browsers block local file requests.

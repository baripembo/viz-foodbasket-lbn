import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

EXCEL_FILE = Path("data/weekly-basket-report-23-03-2026-EN.xlsx")
OUTPUT_FILE = Path("data/foodbasket.json")


def clean(val):
    return None if pd.isna(val) else val


def pct_change(a, b):
    return round((a - b) / b * 100, 2) if a and b else None


def parse_report_date(path: Path) -> datetime:
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", path.stem)
    if not m:
        raise ValueError(f"Cannot parse date from filename: {path.name}")
    return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))


def main():
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Supermarkets",
        header=11,
        engine="openpyxl",
    )

    cols = list(df.columns)
    rename = {
        cols[0]: "category_name",
        cols[1]: "code",
        cols[2]: "name_en",
        cols[3]: "unit",
        cols[4]: "price_mar2025",
        cols[5]: "price_current",
        cols[6]: "yoy_pct",
        cols[7]: "price_prev_week",
        cols[8]: "wow_pct",
    }
    df = df.rename(columns=rename)

    items = []
    current_cat_code = None
    current_cat_name_en = None

    for _, row in df.iterrows():
        code = row.get("code")
        if pd.isna(code):
            continue

        code = str(code).strip()

        # Product row: letters + space + digits (e.g. "V 1", "Fr 1", "Misc 1")
        if not re.match(r"^[A-Za-z]+\s+\d+$", code):
            current_cat_code = code
            current_cat_name_en = str(row.get("category_name", "")).strip()
            continue

        price_current = clean(row.get("price_current"))
        price_prev_week = clean(row.get("price_prev_week"))
        price_mar2025 = clean(row.get("price_mar2025"))

        items.append({
            "code": code,
            "name_en": str(row.get("name_en", "")).strip(),
            "category_code": current_cat_code,
            "category_en": current_cat_name_en,
            "price_current": price_current,
            "price_prev_week": price_prev_week,
            "price_mar2025": price_mar2025,
            "wow_pct": pct_change(price_current, price_prev_week),
            "yoy_pct": pct_change(price_current, price_mar2025),
            "unit": str(row.get("unit", "")).strip(),
        })

    items.sort(key=lambda x: (x["wow_pct"] is None, -(x["wow_pct"] or 0)))

    report_date = parse_report_date(EXCEL_FILE)
    prev_date = report_date - timedelta(weeks=1)

    output = {
        "meta": {
            "title": "Lebanon: Week-over-Week Price Change by Commodity",
            "subtitle": "Supermarkets",
            "date_current": report_date.strftime("%-d %b %Y"),
            "date_previous": prev_date.strftime("%-d %b %Y"),
            "source": "Lebanon Ministry of Economy and Trade \u2013 Price Policy Technical Office",
            "generated": datetime.today().strftime("%Y-%m-%d"),
        },
        "items": items,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Written {len(items)} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

CSV_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/ministry_smeb_item_priced.csv")
OUTPUT_FILE = Path("data/foodbasket.json")

CATEGORY_MAP = {
    "Apples":        ("Fr",   "Fruits"),
    "Banana":        ("Fr",   "Fruits"),
    "Oranges":       ("Fr",   "Fruits"),
    "Cabbage":       ("V",    "Vegetables"),
    "Carrots":       ("V",    "Vegetables"),
    "Cucumber":      ("V",    "Vegetables"),
    "Onion":         ("V",    "Vegetables"),
    "Parsley":       ("V",    "Vegetables"),
    "Potatoes":      ("V",    "Vegetables"),
    "Tomato":        ("V",    "Vegetables"),
    "Zucchini":      ("V",    "Vegetables"),
    "Chickpeas":     ("G",    "Grains & Pulses"),
    "Lentils":       ("G",    "Grains & Pulses"),
    "Rice":          ("G",    "Grains & Pulses"),
    "White Beans":   ("G",    "Grains & Pulses"),
    "Fresh Chicken": ("M",    "Meat"),
    "Eggs":          ("D",    "Eggs & Dairy"),
    "Powdered Milk": ("D",    "Eggs & Dairy"),
    "Sunflower Oil": ("O",    "Fats & Oils"),
    "Tahini":        ("O",    "Fats & Oils"),
    "Salt":          ("Misc", "Miscellaneous"),
    "Sugar":         ("Misc", "Miscellaneous"),
    "Tea":           ("Misc", "Miscellaneous"),
    "Tomato Paste":  ("Misc", "Miscellaneous"),
    "Sardine":       ("C",    "Canned Goods"),
}


def pct_change(a, b):
    return round((a - b) / b * 100, 2) if a and b else None


def fmt_unit(quantity, unit):
    qty = float(quantity)
    qty_str = str(int(qty)) if qty == int(qty) else str(qty)
    return f"{qty_str} {unit}"


def fmt_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%-d %b %Y")


def main():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    dates = sorted(set(r["Reporting_Month"] for r in rows))
    date_current = dates[-1]
    date_prev_week = dates[-2]

    current_dt = datetime.strptime(date_current, "%Y-%m-%d")
    target_yoy = current_dt.replace(year=current_dt.year - 1)
    date_yoy = min(dates, key=lambda d: abs(datetime.strptime(d, "%Y-%m-%d") - target_yoy))

    # price_lbp_l_kg: per-kg/L normalised price — consistent unit for WoW/YoY
    prices = {}
    item_meta = {}
    for r in rows:
        item = r["mnsty_item"]
        date = r["Reporting_Month"]
        prices.setdefault(item, {})[date] = float(r["price_lbp_l_kg"])
        if item not in item_meta:
            item_meta[item] = {
                "smeb_item": r["smeb_item"],
                "basket": r["baskett"],
                "unit": fmt_unit(r["quantity"], r["unit"]),
            }

    items = []
    for name, (cat_code, cat_en) in CATEGORY_MAP.items():
        if name not in prices:
            continue
        p = prices[name]
        price_current = p.get(date_current)
        if price_current is None:
            continue
        price_prev = p.get(date_prev_week)
        price_yoy = p.get(date_yoy)
        meta = item_meta[name]
        items.append({
            "code": name,
            "name_en": name,
            "category_code": cat_code,
            "category_en": cat_en,
            "basket": meta["basket"],
            "smeb_item": meta["smeb_item"],
            "price_current": price_current,
            "price_prev_week": price_prev,
            "price_yoy": price_yoy,
            "wow_pct": pct_change(price_current, price_prev),
            "yoy_pct": pct_change(price_current, price_yoy),
            "unit": meta["unit"],
        })

    items.sort(key=lambda x: (x["wow_pct"] is None, -(x["wow_pct"] or 0)))

    # Build weekly basket totals for time series using pre-computed basket costs
    # MEB total = all items (both "Food MEB" and "Food SMEB")
    # SMEB total = only "Food SMEB" items
    weekly_meb = {}
    weekly_smeb = {}
    for r in rows:
        date = r["Reporting_Month"]
        cost = float(r["ministry_smeb_price_lbp"])
        weekly_meb[date] = weekly_meb.get(date, 0) + cost
        if r["baskett"] == "Food SMEB":
            weekly_smeb[date] = weekly_smeb.get(date, 0) + cost

    timeseries = [
        {"date": d, "meb": round(weekly_meb[d]), "smeb": round(weekly_smeb.get(d, 0))}
        for d in sorted(weekly_meb)
    ]

    output = {
        "meta": {
            "subtitle": "Ministry of Economy MEB/SMEB basket",
            "date_current": fmt_date(date_current),
            "date_previous": fmt_date(date_prev_week),
            "date_yoy": fmt_date(date_yoy),
            "source": "Lebanon Ministry of Economy and Trade \u2013 Price Policy Technical Office",
            "generated": datetime.today().strftime("%Y-%m-%d"),
        },
        "items": items,
        "timeseries": timeseries,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Written {len(items)} items → {OUTPUT_FILE}")
    print(f"  Current:   {date_current}")
    print(f"  Prev week: {date_prev_week}")
    print(f"  YoY ref:   {date_yoy}")


if __name__ == "__main__":
    main()

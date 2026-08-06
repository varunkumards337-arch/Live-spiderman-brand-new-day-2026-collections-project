"""
scripts/scrape_daily.py
------------------------
Runs once per day (triggered automatically by GitHub Actions — see
.github/workflows/daily-scrape.yml). Pulls the current cumulative box
office totals for Spider-Man: Brand New Day from Box Office Mojo and
appends ONE new row to data/scraped_daily.csv.

Over time this builds a genuine day-by-day time series of the film's
running total — entirely self-collected, no manual work needed after
the one-time GitHub Actions setup.
"""

import csv
import os
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://www.boxofficemojo.com/release/rl2299756545/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "scraped_daily.csv")


def clean_money(text: str):
    if not text:
        return None
    digits = re.sub(r"[^\d.]", "", text)
    return float(digits) if digits else None


def scrape_today():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    row = {
        "date_collected": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "domestic_cume_usd": None,
        "international_cume_usd": None,
        "worldwide_cume_usd": None,
    }

    money_spans = soup.select("div.mojo-performance-summary-table span.money")
    keys = ["domestic_cume_usd", "international_cume_usd", "worldwide_cume_usd"]
    for key, span in zip(keys, money_spans):
        row[key] = clean_money(span.get_text())

    return row


def append_row(row: dict):
    file_exists = os.path.isfile(DATA_PATH)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    # Don't add a duplicate row if we already collected today's data
    if file_exists:
        with open(DATA_PATH, newline="", encoding="utf-8") as f:
            existing_dates = {r["date_collected"] for r in csv.DictReader(f)}
        if row["date_collected"] in existing_dates:
            print(f"[SKIP] Already have data for {row['date_collected']}")
            return False

    with open(DATA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"[OK] Added row for {row['date_collected']}: {row}")
    return True


if __name__ == "__main__":
    try:
        today_row = scrape_today()
        append_row(today_row)
    except Exception as e:
        print(f"[ERROR] Scrape failed: {e}")
        # Don't crash the whole Action for a scrape hiccup (site layout
        # changes are common) — just log it, next day's run will retry.

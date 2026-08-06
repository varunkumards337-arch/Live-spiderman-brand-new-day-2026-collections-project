"""
scripts/analysis.py
--------------------
Regenerates all charts in visuals/ from the data in data/.
Run automatically by GitHub Actions after every daily scrape, so the
charts in the repo always reflect the latest collected data.

Run manually:
    python scripts/analysis.py
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # no display needed — just save PNG files
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
VIS_DIR = os.path.join(BASE, "visuals")
os.makedirs(VIS_DIR, exist_ok=True)


def chart_daywise_domestic():
    path = os.path.join(DATA_DIR, "domestic_daywise.csv")
    daywise = pd.read_csv(path)
    daily = daywise[daywise["day_label"] != "Weekend 3-Day Total (Actuals)"]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(daily["day_label"], daily["gross_usd_millions"], color="#c0392b")
    plt.title("Spider-Man: Brand New Day — Domestic Day-wise Collections (Opening)")
    plt.ylabel("Gross (USD Millions)")
    plt.xticks(rotation=25, ha="right")
    for b in bars:
        plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 2,
                  f"${b.get_height():.1f}M", ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "01_domestic_daywise.png"), dpi=150)
    plt.close()


def chart_international_markets():
    path = os.path.join(DATA_DIR, "international_markets.csv")
    intl = pd.read_csv(path)

    plt.figure(figsize=(7, 7))
    plt.pie(intl["gross_usd_millions"], labels=intl["market"], autopct="%1.1f%%", startangle=90)
    plt.title("International Opening Weekend — Market Share (66 markets)")
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "02_international_markets.png"), dpi=150)
    plt.close()


def chart_domestic_vs_international():
    path = os.path.join(DATA_DIR, "global_summary.csv")
    summary = pd.read_csv(path)
    dom = summary.loc[summary["metric"] == "Domestic Opening Weekend (3-day, final actuals)", "value_usd_millions"].iloc[0]
    intl_total = summary.loc[summary["metric"] == "International Opening Weekend (66 markets)", "value_usd_millions"].iloc[0]

    plt.figure(figsize=(6, 6))
    plt.pie([dom, intl_total], labels=["Domestic", "International"],
            autopct="%1.1f%%", colors=["#e74c3c", "#34495e"], startangle=90)
    plt.title("Global Opening Weekend Split: Domestic vs International")
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "03_domestic_vs_international.png"), dpi=150)
    plt.close()


def chart_running_total():
    """
    Plots the cumulative worldwide total over time, built entirely from
    data collected day-by-day by scrape_daily.py. Skips gracefully if
    the scraper hasn't collected enough data points yet.
    """
    path = os.path.join(DATA_DIR, "scraped_daily.csv")
    if not os.path.isfile(path):
        print("[SKIP] scraped_daily.csv not found yet — scraper hasn't run.")
        return

    daily = pd.read_csv(path)
    if len(daily) < 2:
        print("[SKIP] Not enough scraped data points yet for a trend chart.")
        return

    daily["date_collected"] = pd.to_datetime(daily["date_collected"])
    daily = daily.sort_values("date_collected")

    plt.figure(figsize=(9, 5))
    plt.plot(daily["date_collected"], daily["worldwide_cume_usd"] / 1e6,
              marker="o", color="#e74c3c", linewidth=2)
    plt.title("Spider-Man: Brand New Day — Running Worldwide Total (Self-Collected)")
    plt.ylabel("Cumulative Gross (USD Millions)")
    plt.xlabel("Date")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "04_running_worldwide_total.png"), dpi=150)
    plt.close()
    print("[OK] Running total chart updated.")


if __name__ == "__main__":
    chart_daywise_domestic()
    chart_international_markets()
    chart_domestic_vs_international()
    chart_running_total()
    print(f"Charts saved to: {VIS_DIR}")

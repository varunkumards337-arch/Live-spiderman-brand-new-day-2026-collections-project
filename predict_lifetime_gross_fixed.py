"""
predict_lifetime_gross.py
-----------------------------------
The ML/forecasting component of the project.

Two models, used depending on how much self-collected data exists yet:

1. BASELINE MODEL (works immediately, using opening-weekend data only):
   A linear regression trained on 5 comparable Marvel/Spider-Man films —
   domestic opening weekend (X) -> domestic lifetime total (Y) — then
   used to predict Brand New Day's lifetime domestic gross from its
   $360M opening. This is the standard "multiplier method" used by real
   box-office analysts, implemented as a proper regression fit instead
   of a hand-picked average.

2. DECAY MODEL (activates once scraped_daily.csv has 5+ days of data):
   Box office daily grosses shrink roughly geometrically over a run
   (day_gross ≈ g0 * r^t). We fit r via log-linear regression on the
   day-over-day new-gross values, then sum the resulting geometric
   series to project the total lifetime worldwide gross. This model
   gets more accurate every single day as GitHub Actions collects more
   real data — it's designed to improve itself over time.

Run manually:
    python predict_lifetime_gross.py

Outputs:
    predictions.csv
    05_lifetime_gross_prediction.png
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE
VIS_DIR = BASE
os.makedirs(VIS_DIR, exist_ok=True)

BND_OPENING_WEEKEND_DOMESTIC = 360.0  # $M, from global_summary.csv
BND_OPENING_WEEKEND_WORLDWIDE = 932.0  # $M


def baseline_multiplier_model():
    """Linear regression: opening weekend -> lifetime domestic total,
    trained on comparable films, applied to Brand New Day's opening."""
    comps = pd.read_csv(os.path.join(DATA_DIR, "comparable_films.csv"))

    X = comps[["domestic_opening_weekend_usd_millions"]].values
    y = comps["domestic_lifetime_total_usd_millions"].values

    model = LinearRegression()
    model.fit(X, y)

    predicted_domestic_lifetime = model.predict([[BND_OPENING_WEEKEND_DOMESTIC]])[0]
    r_squared = model.score(X, y)

    return {
        "model": "baseline_linear_regression",
        "predicted_domestic_lifetime_usd_millions": round(predicted_domestic_lifetime, 1),
        "r_squared": round(r_squared, 3),
        "training_films": len(comps),
    }


def decay_model():
    """Log-linear regression on daily new-gross values from the
    self-collected scraper data, extrapolated as a geometric series
    to estimate total lifetime worldwide gross. Returns None until
    there's enough scraped data to fit a meaningful trend."""
    path = os.path.join(DATA_DIR, "scraped_daily.csv")
    if not os.path.isfile(path):
        return None

    daily = pd.read_csv(path)
    if len(daily) < 5:
        return None

    daily["date_collected"] = pd.to_datetime(daily["date_collected"])
    daily = daily.sort_values("date_collected").reset_index(drop=True)
    daily["daily_new_gross"] = daily["worldwide_cume_usd"].diff()
    daily = daily.dropna(subset=["daily_new_gross"])
    daily = daily[daily["daily_new_gross"] > 0]

    if len(daily) < 4:
        return None

    t = np.arange(len(daily)).reshape(-1, 1)
    log_gross = np.log(daily["daily_new_gross"].values)

    model = LinearRegression()
    model.fit(t, log_gross)
    r = np.exp(model.coef_[0])  # daily decay ratio
    last_daily_gross = daily["daily_new_gross"].iloc[-1]
    current_cume = daily["worldwide_cume_usd"].iloc[-1]

    if r >= 1:
        # No decay detected yet (too early / still growing) — can't extrapolate safely
        return None

    remaining_tail = (last_daily_gross * r) / (1 - r)
    predicted_lifetime_worldwide = (current_cume + remaining_tail) / 1e6

    return {
        "model": "decay_log_linear_regression",
        "decay_ratio_per_day": round(float(r), 4),
        "predicted_worldwide_lifetime_usd_millions": round(predicted_lifetime_worldwide, 1),
        "data_points_used": len(daily),
    }


def save_predictions(baseline: dict, decay):
    rows = [{
        "prediction_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "model": baseline["model"],
        "prediction_usd_millions": baseline["predicted_domestic_lifetime_usd_millions"],
        "metric": "domestic_lifetime_total",
        "confidence_note": f"R^2={baseline['r_squared']} on {baseline['training_films']} comparable films",
    }]
    if decay:
        rows.append({
            "prediction_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "model": decay["model"],
            "prediction_usd_millions": decay["predicted_worldwide_lifetime_usd_millions"],
            "metric": "worldwide_lifetime_total",
            "confidence_note": f"decay_ratio={decay['decay_ratio_per_day']}, n={decay['data_points_used']} days",
        })

    out_path = os.path.join(DATA_DIR, "predictions.csv")
    df = pd.DataFrame(rows)
    # Append to history so you can see predictions get more accurate over time
    if os.path.isfile(out_path):
        df.to_csv(out_path, mode="a", header=False, index=False)
    else:
        df.to_csv(out_path, index=False)
    return rows


def chart_prediction(baseline: dict, decay):
    labels = ["Opening Weekend\n(actual)", "Baseline Model\n(comparable films)"]
    values = [BND_OPENING_WEEKEND_DOMESTIC, baseline["predicted_domestic_lifetime_usd_millions"]]
    colors = ["#7f8c8d", "#c0392b"]

    if decay:
        labels.append("Decay Model\n(self-collected data)")
        values.append(decay["predicted_worldwide_lifetime_usd_millions"])
        colors.append("#2980b9")

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=colors)
    plt.title("Spider-Man: Brand New Day — Lifetime Gross Prediction")
    plt.ylabel("USD Millions")
    for b in bars:
        plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 10,
                  f"${b.get_height():,.0f}M", ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_DIR, "05_lifetime_gross_prediction.png"), dpi=150)
    plt.close()


if __name__ == "__main__":
    baseline = baseline_multiplier_model()
    decay = decay_model()

    print("\n===== PREDICTION RESULTS =====")
    print(f"Baseline model (comparable-film regression): "
          f"${baseline['predicted_domestic_lifetime_usd_millions']}M projected domestic lifetime "
          f"(R²={baseline['r_squared']})")
    if decay:
        print(f"Decay model (self-collected data): "
              f"${decay['predicted_worldwide_lifetime_usd_millions']}M projected worldwide lifetime "
              f"(daily decay ratio={decay['decay_ratio_per_day']}, n={decay['data_points_used']} days)")
    else:
        print("Decay model: not enough scraped_daily.csv data yet (needs 5+ days). "
              "This will activate automatically as the daily scraper collects more data.")
    print("================================\n")

    save_predictions(baseline, decay)
    chart_prediction(baseline, decay)
    print(f"Saved: {os.path.join(DATA_DIR, 'predictions.csv')}")
    print(f"Saved: {os.path.join(VIS_DIR, '05_lifetime_gross_prediction.png')}")

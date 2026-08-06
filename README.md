u# Spider-Man: Brand New Day — Self-Updating Box Office Tracker & Predictor

An end-to-end data science project that tracks and **forecasts** the box
office run of **Spider-Man: Brand New Day** (Sony/Marvel, released July 31,
2026 — the biggest domestic opening weekend in box office history at $360M).

This isn't a static Kaggle-CSV project. It has three layers, each a
standard data science skill:

| Layer | What it does | Skill area |
|---|---|---|
| `scripts/scrape_daily.py` + GitHub Actions | Collects fresh box office data every single day, automatically | Data Engineering |
| `scripts/analysis.py` | Cleans data, builds charts, surfaces insights | Exploratory Data Analysis |
| `scripts/predict_lifetime_gross.py` | Two regression models forecasting the film's lifetime gross | Machine Learning |

## The ML component

**1. Baseline model (works immediately):** a `scikit-learn` `LinearRegression`
trained on five comparable Marvel/Spider-Man films — domestic opening
weekend → domestic lifetime total — then used to project Brand New Day's
lifetime domestic gross from its $360M opening. This is the standard
box-office "multiplier method," implemented as an actual fitted regression
instead of a hand-picked average.

**2. Decay model (self-improving):** once the daily scraper has collected 5+
days of real data, a second model kicks in automatically. Box office grosses
shrink roughly geometrically day over day; the script fits the decay rate
via log-linear regression on the collected daily figures, then sums the
resulting geometric series to project total lifetime worldwide gross. This
model gets **more accurate every day** as GitHub Actions gathers more real
data — the prediction genuinely improves itself over the film's run.

Every prediction run is appended to `data/predictions.csv`, so you can
literally watch the model's forecast converge on the real number over time.

## How the automation works

```
.github/workflows/daily-scrape.yml   <- GitHub's scheduler triggers this daily
            |
            v
scripts/scrape_daily.py              <- pulls today's totals from Box Office Mojo
            |
            v
data/scraped_daily.csv               <- one new row appended each day
            |
            v
scripts/analysis.py                  <- regenerates EDA charts
            |
            v
scripts/predict_lifetime_gross.py    <- regenerates the ML forecast
            |
            v
visuals/*.png + data/predictions.csv <- auto-committed back to the repo
```

## Project structure

```
spiderman-ml-project/
├── .github/workflows/
│   └── daily-scrape.yml            # the automation — runs daily on GitHub's servers
├── data/
│   ├── domestic_daywise.csv        # opening weekend day-by-day domestic gross (seed)
│   ├── international_markets.csv   # top international markets breakdown (seed)
│   ├── global_summary.csv          # headline totals + historical comparisons (seed)
│   ├── comparable_films.csv        # training data for the baseline regression model
│   ├── scraped_daily.csv           # grows by one row every day (auto-generated)
│   └── predictions.csv             # history of every model run (auto-generated)
├── scripts/
│   ├── scrape_daily.py             # daily data collector
│   ├── analysis.py                 # EDA + chart generation
│   └── predict_lifetime_gross.py   # the ML forecasting models
├── visuals/                         # auto-refreshed PNG charts
├── requirements.txt
└── README.md
```

## Data sources

- **Seed data**: opening-weekend numbers compiled from Variety, Deadline,
  and Rotten Tomatoes reporting (Aug 1-3, 2026).
- **Comparable films data**: publicly reported domestic opening/lifetime
  totals for Endgame, No Way Home, Infinity War, Far From Home, Homecoming.
- **Live data** (`scraped_daily.csv`): collected automatically, once a day,
  from [Box Office Mojo](https://www.boxofficemojo.com).

## Setup (only needed once)

1. Push this repo to GitHub.
2. **Settings -> Actions -> General -> Workflow permissions ->** select
   **"Read and write permissions"** (lets the automation commit data back).
3. **Actions tab -> "Daily Box Office Update" -> "Run workflow"** to trigger
   the first run manually instead of waiting for the daily schedule.

## Run locally (optional)

```bash
pip install -r requirements.txt
python scripts/scrape_daily.py            # collect today's numbers
python scripts/analysis.py                # regenerate EDA charts
python scripts/predict_lifetime_gross.py  # regenerate ML forecast
```

## Key findings (opening weekend, from seed data)

- **$360M** domestic opening — the biggest in box office history, surpassing
  *Avengers: Endgame*'s $357.1M (2019).
- **$932M** global opening weekend — second only to *Avengers: Endgame*'s
  $1.223B.
- **China** was the top international market at $121M.
- Friday -> Sunday day-over-day decline was roughly **50%**.
- Baseline regression model projects a **~$913M domestic lifetime total**
  (R² = 0.91 on comparable-film training data) — this updates as the decay
  model activates with more collected data.

## Roadmap

- [ ] Let the daily automation run for 4+ weeks so the decay model activates
- [ ] Compare baseline vs. decay model accuracy once the film's run ends
- [ ] Add a Streamlit dashboard reading live from `predictions.csv`
- [ ] Extend the comparable-films training set for a more robust baseline

## Tech stack

Python · pandas · scikit-learn · NumPy · BeautifulSoup4 · requests ·
matplotlib · GitHub Actions

# Japan Car Import Advisory

**End-to-end data + ML product** that helps Kenyan buyers decide whether importing a used car from Japan is cheaper than buying the same model locally.

Built to demonstrate practical skills across **web scraping, ETL, domain costing, machine learning, and full-stack API delivery**.

## Live demo

> **Not hosted yet.** After you deploy (steps below), put the public URL here, e.g.  
> **Live demo:** https://japan-car-import-advisory.onrender.com

### Deploy on Render (free)

1. Go to [https://render.com](https://render.com) → **New** → **Blueprint**
2. Connect GitHub and select `JoyKyalogit/-japan-car-import-advisory` (or rename the repo first)
3. Render reads `render.yaml` and builds the Docker image with the bundled demo database (~1,700 Japan listings + ~1,600 Kenya price groups)
4. When the service is **Live**, open the `.onrender.com` URL and paste it into this README section

Local-only preview (no public URL):

```bash
uv run python scripts/run_server.py
```

Open http://127.0.0.1:8003

---

## Problem

Used cars in Kenya are often expensive. Buyers can import from Japan, but the true landed cost is hard to estimate: purchase price, shipping, KRA taxes, port charges, clearing, and NTSA fees. This project turns that into a clear **import vs local** comparison.

---

## What it does

| Capability | Detail |
|------------|--------|
| **Japan market data** | Live scrapers (primary: BE FORWARD) for used-car listings |
| **Kenya market data** | Real local prices from Cheki, Jiji, and Autochek |
| **ETL pipeline** | Clean, normalize, and store listings (2018+ vehicles) |
| **Import cost engine** | KRA duty/excise/VAT/RDL/IDF + port, clearing, registration |
| **Savings analysis** | Compare full landed cost vs Kenya market price |
| **Price prediction** | XGBoost model estimates Japan prices from vehicle features |
| **Interactive web app** | FastAPI + HTML/CSS/JS dashboard for compare, predict, market, savings |

---

## Skills demonstrated

- **Data engineering** — multi-source scrapers, retries/rate-limit handling, CSV + SQLite persistence  
- **ETL / data quality** — cleaning, year filters, model-name normalization for cross-market matching  
- **Domain modeling** — Kenya import cost rules encoded as testable calculators  
- **Machine learning** — feature pipeline + XGBoost regression for price prediction  
- **Backend APIs** — FastAPI REST endpoints, Pydantic schemas, SQLAlchemy models  
- **Frontend** — interactive UI with charts and filter-driven exploration  
- **Software practice** — `uv` project tooling, pytest, env-based configuration  

---

## Architecture

```text
Japan sites (BE FORWARD, …) ──► Scrapers ──► ETL / Cleaner ──► SQLite
Kenya sites (Cheki, Jiji, Autochek) ─────────────▲                │
                                                 │                ▼
                              Import Cost Calculator ◄── Listings + Local prices
                                                 │
                              XGBoost Price Model ┘
                                                 │
                                          FastAPI + Web UI
```

**Typical flow**

1. Scrape Japan listings and Kenya local prices  
2. Clean and load into the database  
3. Train / refresh the price model  
4. Serve comparisons and predictions through the web app  

---

## Tech stack

| Layer | Tools |
|-------|--------|
| Language | Python 3.11+ |
| Packaging | uv |
| API | FastAPI, Uvicorn, Pydantic |
| Data | Pandas, SQLAlchemy, SQLite (Postgres-ready) |
| Scraping | Requests, BeautifulSoup, Tenacity |
| ML | XGBoost, scikit-learn, joblib |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Tests | pytest |

---

## Project structure

```text
japan-car-import-advisory/
├── frontend/               # Web UI
├── scripts/                # Pipeline entrypoints (scrape, train, serve)
├── src/
│   ├── api/                # FastAPI app
│   ├── scrapers/           # Japan + Kenya scrapers
│   ├── etl/                # Cleaning & load
│   ├── calculator/         # Kenya import cost logic
│   ├── ml/                 # Train & predict
│   ├── services/           # Analysis, FX, matching
│   └── database/           # SQLAlchemy models
├── data/                   # Raw / cleaned data + DB
├── models/                 # Trained model artifacts
├── tests/
└── docs/
```

---

## Quick start

**Requirements:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
# 1. Install
uv sync

# 2. Initialize DB + scrape + train (uses .env settings)
uv run python scripts/init_db.py
uv run python scripts/run_scrapers.py
uv run python scripts/train_model.py

# 3. Run the app
uv run python scripts/run_server.py
```

Open **http://127.0.0.1:8003** (default port; override with `PORT`).

**One-shot CLI**

```bash
uv run python main.py all      # pipeline + server
uv run python main.py server   # server only
```

**Safer Japan-only refresh** (keeps Kenya prices):

```bash
uv run python scripts/run_japan_scraper.py
uv run python scripts/train_model.py
```

---

## Configuration notes

Copy `.env.example` → `.env` (or edit `.env`).

| Setting | Purpose |
|---------|---------|
| `SCRAPER_USE_SAMPLE_DATA=false` | Use live scrapers (recommended for demos with real data) |
| `SCRAPER_USE_REAL_LOCAL_PRICES=true` | Scrape Kenya prices (Cheki / Jiji / Autochek) |
| `SCRAPER_MAX_PAGES_PER_MAKE` | Cap pages to avoid rate limits |
| `USE_LIVE_EXCHANGE_RATE=true` | Fetch live USD/KES |

Live sites may throttle scrapers; the project includes delays, retries, and cooldowns for more reliable runs.

---

## Import cost model (Kenya)

| Component | Basis |
|-----------|--------|
| Import Duty | 25% of CIF |
| Excise Duty | 10–35% (engine size & fuel) |
| VAT | 16% of (CIF + duties) |
| Railway Development Levy | 2% of CIF |
| Import Declaration Fee | 2.25% of CIF (min KES 5,000) |
| Port / clearing / NTSA | Schedule-based fees |

---

## Tests

```bash
uv run pytest tests/ -v
```

---

## Example dataset scale (after a successful scrape)

- **~1,700+** cleaned Japan listings across **20+** makes  
- **~1,600+** Kenya local price groups from multiple marketplaces  
- Interactive tabs: Compare · Predict · Market Data · Savings  

*Exact counts depend on scrape limits and site availability.*

---

## Why this project

It connects a real buyer decision to a complete technical pipeline: **ingest → clean → model → calculate → serve**. That makes it a strong portfolio piece for roles in data engineering, applied ML, backend, or analytics engineering.

---


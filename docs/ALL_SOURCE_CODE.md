# Full Source Code

Copy each block into the matching file path in VS Code.

---

## `main.py`

```python
"""CLI entry point for Japan Car Import Advisory Platform."""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Japan Car Import Advisory Platform")
    parser.add_argument(
        "command",
        choices=["init", "scrape", "clean", "train", "server", "all"],
        help="Command to run",
    )
    args = parser.parse_args()
    root = Path(__file__).parent
    py = sys.executable

    commands = {
        "init": [py, str(root / "scripts" / "init_db.py")],
        "scrape": [py, str(root / "scripts" / "run_scrapers.py")],
        "clean": [py, str(root / "scripts" / "clean_data.py")],
        "train": [py, str(root / "scripts" / "train_model.py")],
        "server": [py, str(root / "scripts" / "run_server.py")],
    }

    if args.command == "all":
        for cmd in ["init", "scrape", "train"]:
            print(f"\n{'='*50}\nRunning: {cmd}\n{'='*50}")
            subprocess.run(commands[cmd], check=True)
        print("\nStarting web server...")
        subprocess.run(commands["server"])
    else:
        subprocess.run(commands[args.command])


if __name__ == "__main__":
    main()
```

---

## `pyproject.toml`

```toml
[project]
name = "japan-car-import-advisory"
version = "0.1.0"
description = "Japan Car Import Advisory Platform for Kenyan car buyers"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "beautifulsoup4>=4.14.3",
    "fake-useragent>=2.2.0",
    "joblib>=1.5.3",
    "jupyterlab>=4.5.7",
    "lxml>=6.1.1",
    "matplotlib>=3.10.9",
    "numpy>=2.4.6",
    "pandas>=3.0.3",
    "playwright>=1.60.0",
    "psycopg2-binary>=2.9.12",
    "pydantic>=2.13.4",
    "pydantic-settings>=2.14.1",
    "python-dotenv>=1.2.2",
    "requests>=2.34.2",
    "scikit-learn>=1.8.0",
    "seaborn>=0.13.2",
    "sqlalchemy>=2.0.49",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "tenacity>=9.1.4",
    "xgboost>=3.2.0",
]

[dependency-groups]
dev = [
    "black>=26.5.1",
    "mypy>=2.1.0",
    "pre-commit>=4.6.0",
    "pytest>=9.0.3",
    "ruff>=0.15.13",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

---

## `.env.example`

```text
# Database (SQLite by default; set PostgreSQL URL to use Postgres)
DATABASE_URL=sqlite:///data/japan_cars.db

# Exchange rate: 1 USD = X KES (update regularly)
USD_TO_KES=130.0
JPY_TO_USD=0.0067

# Scraper settings
SCRAPER_DELAY_SECONDS=2
SCRAPER_MAX_PAGES=5
SCRAPER_USE_SAMPLE_DATA=true

# ML model path
MODEL_PATH=models/price_predictor.joblib
```

---

## `sql/schema.sql`

```text
-- Japan Car Import Advisory Platform schema

CREATE TABLE IF NOT EXISTS car_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_platform VARCHAR(50) NOT NULL,
    listing_id VARCHAR(100),
    title VARCHAR(300),
    make VARCHAR(80),
    model VARCHAR(120),
    year INTEGER,
    mileage_km INTEGER,
    engine_cc INTEGER,
    fuel_type VARCHAR(30),
    transmission VARCHAR(30),
    body_type VARCHAR(50),
    price_jpy REAL,
    price_usd REAL,
    currency VARCHAR(10) DEFAULT 'JPY',
    location VARCHAR(100),
    listing_url TEXT,
    image_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_cleaned INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_listings_platform ON car_listings(source_platform);
CREATE INDEX IF NOT EXISTS idx_listings_make_model ON car_listings(make, model);
CREATE INDEX IF NOT EXISTS idx_listings_year ON car_listings(year);

CREATE TABLE IF NOT EXISTS local_market_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make VARCHAR(80),
    model VARCHAR(120),
    year INTEGER,
    avg_price_kes REAL,
    min_price_kes REAL,
    max_price_kes REAL,
    source VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_cost_estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_listing_id INTEGER,
    purchase_price_usd REAL,
    shipping_usd REAL,
    insurance_usd REAL,
    cif_usd REAL,
    import_duty_kes REAL,
    excise_duty_kes REAL,
    vat_kes REAL,
    rdl_kes REAL,
    idf_kes REAL,
    port_charges_kes REAL,
    clearing_fees_kes REAL,
    registration_kes REAL,
    other_charges_kes REAL,
    total_import_kes REAL,
    local_market_kes REAL,
    potential_savings_kes REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Japan Car Import Advisory</title>
  <link rel="stylesheet" href="/css/style.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
  <header class="header">
    <div class="header-inner">
      <div>
        <h1>🚗 Japan Car Import Advisory</h1>
        <p>Compare import costs from Japan vs buying locally in Kenya</p>
      </div>
      <div class="stats-bar" id="stats-bar">
        <div class="stat"><span id="stat-listings">—</span><label>Listings</label></div>
        <div class="stat"><span id="stat-rate">—</span><label>USD → KES</label></div>
      </div>
    </div>
  </header>

  <nav class="tabs">
    <button class="tab active" data-tab="compare">Compare Cars</button>
    <button class="tab" data-tab="predict">Price Predictor</button>
    <button class="tab" data-tab="market">Market Data</button>
    <button class="tab" data-tab="savings">Savings Analysis</button>
  </nav>

  <main class="container">
    <!-- Compare Cars -->
    <section id="tab-compare" class="panel active">
      <h2>Compare Import vs Local Price</h2>
      <p class="subtitle">Select a car to instantly see import cost, local price, and savings.</p>

      <div class="filters">
        <div class="field">
          <label>Make</label>
          <select id="filter-make"><option value="">All</option></select>
        </div>
        <div class="field">
          <label>Model</label>
          <select id="filter-model"><option value="">All</option></select>
        </div>
        <div class="field">
          <label>Year from</label>
          <input type="number" id="filter-year-min" min="2018" value="2018" />
        </div>
        <div class="field">
          <label>Year to</label>
          <input type="number" id="filter-year-max" min="2018" value="2026" />
        </div>
      </div>

      <div class="field">
        <label>Select a car</label>
        <select id="car-select" size="6"></select>
      </div>

      <div id="compare-result" class="hidden">
        <div class="vehicle-info" id="vehicle-info"></div>

        <div class="metrics">
          <div class="metric-card">
            <label>Japan Purchase</label>
            <span id="m-purchase">—</span>
          </div>
          <div class="metric-card highlight">
            <label>Full Import Cost</label>
            <span id="m-import">—</span>
          </div>
          <div class="metric-card">
            <label>Local Market</label>
            <span id="m-local">—</span>
          </div>
          <div class="metric-card" id="savings-card">
            <label>Potential Savings</label>
            <span id="m-savings">—</span>
          </div>
        </div>

        <div id="recommendation" class="banner"></div>

        <div class="charts">
          <canvas id="compare-chart"></canvas>
          <canvas id="breakdown-chart"></canvas>
        </div>

        <details class="breakdown-details">
          <summary>Full import cost breakdown</summary>
          <table id="breakdown-table">
            <thead><tr><th>Item</th><th>Amount (KES)</th></tr></thead>
            <tbody></tbody>
          </table>
        </details>
      </div>
    </section>

    <!-- Price Predictor -->
    <section id="tab-predict" class="panel">
      <h2>ML Price Predictor</h2>
      <p class="subtitle">Predict Japan car price and estimated import cost.</p>

      <form id="predict-form" class="form-grid">
        <div class="field"><label>Make</label><input name="make" value="Toyota" required /></div>
        <div class="field"><label>Model</label><input name="model" value="Harrier" required /></div>
        <div class="field"><label>Year</label><input name="year" type="number" value="2020" min="2018" required /></div>
        <div class="field"><label>Mileage (km)</label><input name="mileage_km" type="number" value="45000" required /></div>
        <div class="field"><label>Engine (cc)</label><input name="engine_cc" type="number" value="2000" required /></div>
        <div class="field"><label>Fuel</label>
          <select name="fuel_type"><option>Petrol</option><option>Diesel</option><option>Hybrid</option><option>Electric</option></select>
        </div>
        <div class="field"><label>Transmission</label>
          <select name="transmission"><option>Automatic</option><option>Manual</option><option>CVT</option></select>
        </div>
        <div class="field"><label>Body</label>
          <select name="body_type"><option>Sedan</option><option>SUV</option><option>Hatchback</option><option>Wagon</option></select>
        </div>
      </form>
      <button class="btn primary" id="predict-btn">Predict Price</button>
      <div id="predict-result" class="hidden"></div>
    </section>

    <!-- Market Data -->
    <section id="tab-market" class="panel">
      <h2>Market Data</h2>
      <div class="metrics" id="market-summary"></div>
      <div class="table-wrap">
        <table id="market-table">
          <thead>
            <tr><th>Make</th><th>Model</th><th>Year</th><th>Mileage</th><th>Engine</th><th>Fuel</th><th>USD</th><th>JPY</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <canvas id="market-chart"></canvas>
    </section>

    <!-- Savings Analysis -->
    <section id="tab-savings" class="panel">
      <h2>Savings Analysis</h2>
      <div class="metrics" id="savings-summary"></div>
      <div class="table-wrap">
        <table id="savings-table">
          <thead>
            <tr><th>Vehicle</th><th>Import (KES)</th><th>Local (KES)</th><th>Savings (KES)</th><th>Savings %</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <canvas id="savings-chart"></canvas>
    </section>
  </main>

  <footer class="footer">
    Japan Car Import Advisory Platform — Kenya
  </footer>

  <script src="/js/app.js"></script>
</body>
</html>
```

---

## `frontend/css/style.css`

```css
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #242836;
  --border: #2e3345;
  --text: #f0f2f8;
  --muted: #9aa3b8;
  --accent: #e63946;
  --accent-hover: #ff4d5a;
  --success: #2ecc71;
  --warning: #f39c12;
  --radius: 10px;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}

.header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 1.25rem 1.5rem;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.header h1 { font-size: 1.5rem; font-weight: 700; }
.header p { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }

.stats-bar { display: flex; gap: 1.5rem; }
.stat { text-align: center; }
.stat span { display: block; font-size: 1.25rem; font-weight: 700; color: var(--accent); }
.stat label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }

.tabs {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 0.25rem;
  padding: 1rem 1.5rem 0;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
}

.tab {
  background: none;
  border: none;
  color: var(--muted);
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  font-size: 0.95rem;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.2s;
  white-space: nowrap;
}

.tab:hover { color: var(--text); }
.tab.active { color: var(--text); border-bottom-color: var(--accent); }

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.panel { display: none; }
.panel.active { display: block; }

.panel h2 { font-size: 1.35rem; margin-bottom: 0.35rem; }
.subtitle { color: var(--muted); margin-bottom: 1.25rem; font-size: 0.9rem; }

.filters, .form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.field label {
  display: block;
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.field input,
.field select,
#car-select {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius);
  font-size: 0.95rem;
}

#car-select { min-height: 160px; }
#car-select option { padding: 0.5rem; }

.btn {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.65rem 1.25rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s;
}

.btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  font-weight: 600;
}

.btn.primary:hover { background: var(--accent-hover); }

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0;
}

.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  box-shadow: var(--shadow);
}

.metric-card label {
  display: block;
  font-size: 0.75rem;
  color: var(--muted);
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}

.metric-card span { font-size: 1.2rem; font-weight: 700; }
.metric-card.highlight { border-color: var(--accent); }
.metric-card.highlight span { color: var(--accent); }

.vehicle-info {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  font-size: 0.9rem;
}

.vehicle-info strong { color: var(--muted); font-weight: 500; display: block; font-size: 0.75rem; text-transform: uppercase; }

.banner {
  padding: 1rem 1.25rem;
  border-radius: var(--radius);
  margin: 1rem 0;
  font-weight: 500;
}

.banner.success { background: rgba(46, 204, 113, 0.15); border: 1px solid var(--success); color: var(--success); }
.banner.warning { background: rgba(243, 156, 18, 0.15); border: 1px solid var(--warning); color: var(--warning); }
.banner.info { background: rgba(154, 163, 184, 0.1); border: 1px solid var(--border); color: var(--muted); }

.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 1.5rem 0;
}

.charts canvas { max-height: 320px; }

.breakdown-details {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
}

.breakdown-details summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.table-wrap { overflow-x: auto; margin: 1rem 0; }

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th, td {
  padding: 0.65rem 0.85rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

th { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; }
tbody tr:hover { background: var(--surface2); }

.hidden { display: none !important; }

.footer {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.85rem;
  border-top: 1px solid var(--border);
  margin-top: 2rem;
}

@media (max-width: 600px) {
  .header-inner { flex-direction: column; align-items: flex-start; }
  .metrics { grid-template-columns: 1fr 1fr; }
}
```

---

## `frontend/js/app.js`

```javascript
const API = "/api";

let compareChart = null;
let breakdownChart = null;
let marketChart = null;
let savingsChart = null;
let carsCache = [];

const fmtKes = (n) => `KES ${Math.round(n).toLocaleString()}`;
const fmtUsd = (n) => `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// ── Tabs ──────────────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");

    if (btn.dataset.tab === "market") loadMarketData();
    if (btn.dataset.tab === "savings") loadSavings();
  });
});

// ── Stats ─────────────────────────────────────────────────────────────────
async function loadStats() {
  const stats = await fetchJson(`${API}/stats`);
  document.getElementById("stat-listings").textContent = stats.listings.toLocaleString();
  document.getElementById("stat-rate").textContent = stats.usd_to_kes;
}

// ── Filters & car list ────────────────────────────────────────────────────
async function loadFilters() {
  const data = await fetchJson(`${API}/filters`);
  const makeSel = document.getElementById("filter-make");
  data.makes.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    makeSel.appendChild(opt);
  });
  if (data.years.length) {
    document.getElementById("filter-year-min").value = Math.min(...data.years);
    document.getElementById("filter-year-max").value = Math.max(...data.years);
  }
}

async function loadCars() {
  const make = document.getElementById("filter-make").value;
  const model = document.getElementById("filter-model").value;
  const yearMin = document.getElementById("filter-year-min").value;
  const yearMax = document.getElementById("filter-year-max").value;

  const params = new URLSearchParams();
  if (make) params.set("make", make);
  if (model) params.set("model", model);
  if (yearMin) params.set("year_min", yearMin);
  if (yearMax) params.set("year_max", yearMax);

  carsCache = await fetchJson(`${API}/cars?${params}`);
  const sel = document.getElementById("car-select");
  sel.innerHTML = "";

  if (!carsCache.length) {
    sel.innerHTML = "<option>No cars found</option>";
    document.getElementById("compare-result").classList.add("hidden");
    return;
  }

  carsCache.forEach((car) => {
    const opt = document.createElement("option");
    opt.value = car.id;
    opt.textContent = car.label;
    sel.appendChild(opt);
  });

  if (carsCache[0]?.id) showComparison(carsCache[0].id);
}

document.getElementById("filter-make").addEventListener("change", async () => {
  const make = document.getElementById("filter-make").value;
  const modelSel = document.getElementById("filter-model");
  modelSel.innerHTML = "<option value=''>All</option>";

  const filters = await fetchJson(`${API}/filters`);
  let models = filters.models;
  if (make) {
    const cars = await fetchJson(`${API}/cars?make=${encodeURIComponent(make)}`);
    models = [...new Set(cars.map((c) => c.model))].sort();
  }
  models.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    modelSel.appendChild(opt);
  });
  loadCars();
});

["filter-model", "filter-year-min", "filter-year-max"].forEach((id) => {
  document.getElementById(id).addEventListener("change", loadCars);
});

document.getElementById("car-select").addEventListener("change", (e) => {
  const id = e.target.value;
  if (id) showComparison(id);
});

// ── Compare ───────────────────────────────────────────────────────────────
async function showComparison(carId) {
  const data = await fetchJson(`${API}/cars/${carId}/compare`);
  const { car, breakdown, savings_pct } = data;

  document.getElementById("compare-result").classList.remove("hidden");

  document.getElementById("vehicle-info").innerHTML = `
    <div><strong>Make / Model</strong>${car.make} ${car.model}</div>
    <div><strong>Year</strong>${car.year}</div>
    <div><strong>Mileage</strong>${car.mileage_km?.toLocaleString() ?? "—"} km</div>
    <div><strong>Engine</strong>${car.engine_cc} cc</div>
    <div><strong>Fuel</strong>${car.fuel_type}</div>
    <div><strong>Body</strong>${car.body_type}</div>
  `;

  document.getElementById("m-purchase").textContent = fmtUsd(breakdown.purchase_price_usd);
  document.getElementById("m-import").textContent = fmtKes(breakdown.total_import_kes);
  document.getElementById("m-local").textContent = breakdown.local_market_kes
    ? fmtKes(breakdown.local_market_kes)
    : "Not available";

  const savingsEl = document.getElementById("m-savings");
  const recEl = document.getElementById("recommendation");

  if (breakdown.potential_savings_kes != null && breakdown.local_market_kes) {
    const s = breakdown.potential_savings_kes;
    savingsEl.textContent = fmtKes(Math.abs(s));
    savingsEl.style.color = s > 0 ? "var(--success)" : "var(--warning)";
    recEl.className = "banner " + (s > 0 ? "success" : "warning");
    recEl.textContent = s > 0
      ? `Importing could save ${fmtKes(s)} (${savings_pct}% vs local market).`
      : `Buying locally may be cheaper by ${fmtKes(Math.abs(s))}.`;
  } else {
    savingsEl.textContent = "—";
    recEl.className = "banner info";
    recEl.textContent = "Local market price not available for this vehicle.";
  }

  renderCompareChart(breakdown);
  renderBreakdownChart(breakdown);
  renderBreakdownTable(breakdown);
}

function renderCompareChart(b) {
  const ctx = document.getElementById("compare-chart");
  if (compareChart) compareChart.destroy();
  if (!b.local_market_kes) return;

  compareChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Import from Japan", "Buy Locally"],
      datasets: [{
        data: [b.total_import_kes, b.local_market_kes],
        backgroundColor: ["#e63946", "#9aa3b8"],
      }],
    },
    options: {
      plugins: { legend: { display: false }, title: { display: true, text: "Import vs Local", color: "#f0f2f8" } },
      scales: { y: { ticks: { color: "#9aa3b8" } }, x: { ticks: { color: "#9aa3b8" } } },
    },
  });
}

function renderBreakdownChart(b) {
  const ctx = document.getElementById("breakdown-chart");
  if (breakdownChart) breakdownChart.destroy();

  const usdToKes = b.purchase_price_kes / b.purchase_price_usd;
  const items = [
    ["Purchase", b.purchase_price_kes],
    ["Shipping", b.shipping_usd * usdToKes],
    ["Insurance", b.insurance_usd * usdToKes],
    ["KRA Taxes", b.kra_taxes_kes],
    ["Port & Clearing", b.port_charges_kes + b.clearing_fees_kes],
    ["Registration", b.registration_kes],
    ["Other", b.other_charges_kes],
  ];

  breakdownChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: items.map((i) => i[0]),
      datasets: [{ data: items.map((i) => i[1]), backgroundColor: ["#e63946","#457b9d","#1d3557","#f4a261","#2a9d8f","#e9c46a","#6c757d"] }],
    },
    options: {
      plugins: { title: { display: true, text: "Cost Breakdown", color: "#f0f2f8" } },
    },
  });
}

function renderBreakdownTable(b) {
  const usdToKes = b.purchase_price_kes / b.purchase_price_usd;
  const rows = [
    ["Purchase Price (Japan)", b.purchase_price_kes],
    ["Shipping", b.shipping_usd * usdToKes],
    ["Insurance", b.insurance_usd * usdToKes],
    ["Import Duty (25%)", b.import_duty_kes],
    ["Excise Duty", b.excise_duty_kes],
    ["VAT (16%)", b.vat_kes],
    ["Railway Dev. Levy", b.rdl_kes],
    ["Import Declaration Fee", b.idf_kes],
    ["Port Charges", b.port_charges_kes],
    ["Clearing Fees", b.clearing_fees_kes],
    ["NTSA Registration", b.registration_kes],
    ["Other Charges", b.other_charges_kes],
    ["TOTAL LANDED COST", b.total_import_kes],
  ];

  const tbody = document.querySelector("#breakdown-table tbody");
  tbody.innerHTML = rows.map(([item, amt], i) =>
    `<tr${i === rows.length - 1 ? ' style="font-weight:700"' : ""}><td>${item}</td><td>${fmtKes(amt)}</td></tr>`
  ).join("");
}

// ── Predict ───────────────────────────────────────────────────────────────
document.getElementById("predict-btn").addEventListener("click", async () => {
  const form = document.getElementById("predict-form");
  const data = Object.fromEntries(new FormData(form));
  data.year = parseInt(data.year);
  data.mileage_km = parseInt(data.mileage_km);
  data.engine_cc = parseInt(data.engine_cc);

  const resultEl = document.getElementById("predict-result");
  resultEl.classList.remove("hidden");

  try {
    const res = await fetchJson(`${API}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const b = res.import_cost;
    resultEl.innerHTML = `
      <div class="metrics" style="margin-top:1rem">
        <div class="metric-card"><label>Predicted (JPY)</label><span>¥${res.prediction.price_jpy.toLocaleString()}</span></div>
        <div class="metric-card"><label>Predicted (USD)</label><span>${fmtUsd(res.prediction.price_usd)}</span></div>
        <div class="metric-card highlight"><label>Import Cost</label><span>${fmtKes(b.total_import_kes)}</span></div>
        <div class="metric-card"><label>Local Market</label><span>${b.local_market_kes ? fmtKes(b.local_market_kes) : "N/A"}</span></div>
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = `<div class="banner warning">${err.message}</div>`;
  }
});

// ── Market Data ───────────────────────────────────────────────────────────
async function loadMarketData() {
  const data = await fetchJson(`${API}/market-data`);
  const s = data.summary;

  document.getElementById("market-summary").innerHTML = `
    <div class="metric-card"><label>Total Listings</label><span>${s.total ?? 0}</span></div>
    <div class="metric-card"><label>Makes</label><span>${s.makes ?? 0}</span></div>
    <div class="metric-card"><label>Avg Price USD</label><span>${fmtUsd(s.avg_price_usd ?? 0)}</span></div>
    <div class="metric-card"><label>Year Range</label><span>${s.year_min ?? "—"}–${s.year_max ?? "—"}</span></div>
  `;

  const tbody = document.querySelector("#market-table tbody");
  tbody.innerHTML = data.listings.map((r) => `
    <tr>
      <td>${r.make}</td><td>${r.model}</td><td>${r.year}</td>
      <td>${r.mileage_km?.toLocaleString() ?? "—"}</td><td>${r.engine_cc ?? "—"}</td>
      <td>${r.fuel_type ?? "—"}</td><td>${fmtUsd(r.price_usd)}</td>
      <td>${r.price_jpy ? "¥" + Math.round(r.price_jpy).toLocaleString() : "—"}</td>
    </tr>
  `).join("");

  const ctx = document.getElementById("market-chart");
  if (marketChart) marketChart.destroy();
  if (data.by_make?.length) {
    marketChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.by_make.map((m) => m.make),
        datasets: [{ label: "Avg USD", data: data.by_make.map((m) => m.avg_usd), backgroundColor: "#e63946" }],
      },
      options: {
        plugins: { title: { display: true, text: "Average Price by Make", color: "#f0f2f8" } },
        scales: { y: { ticks: { color: "#9aa3b8" } }, x: { ticks: { color: "#9aa3b8" } } },
      },
    });
  }
}

// ── Savings ─────────────────────────────────────────────────────────────
async function loadSavings() {
  const data = await fetchJson(`${API}/savings`);
  const s = data.summary;

  document.getElementById("savings-summary").innerHTML = `
    <div class="metric-card"><label>Vehicles Analysed</label><span>${s.total ?? 0}</span></div>
    <div class="metric-card"><label>Avg Savings</label><span>${s.avg_savings_pct ?? 0}%</span></div>
    <div class="metric-card"><label>Import Cheaper</label><span>${s.import_cheaper ?? 0} / ${s.total ?? 0}</span></div>
  `;

  const tbody = document.querySelector("#savings-table tbody");
  tbody.innerHTML = data.items.slice(0, 50).map((r) => `
    <tr>
      <td>${r.vehicle}</td>
      <td>${fmtKes(r.total_import_kes)}</td>
      <td>${fmtKes(r.local_market_kes)}</td>
      <td style="color:${r.savings_kes > 0 ? "var(--success)" : "var(--warning)"}">${fmtKes(r.savings_kes)}</td>
      <td>${r.savings_pct}%</td>
    </tr>
  `).join("");

  const ctx = document.getElementById("savings-chart");
  if (savingsChart) savingsChart.destroy();
  const top = data.items.slice(0, 10);
  if (top.length) {
    savingsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: top.map((r) => r.vehicle),
        datasets: [
          { label: "Import Cost", data: top.map((r) => r.total_import_kes), backgroundColor: "#e63946" },
          { label: "Local Price", data: top.map((r) => r.local_market_kes), backgroundColor: "#9aa3b8" },
        ],
      },
      options: {
        plugins: { title: { display: true, text: "Top 10 — Import vs Local", color: "#f0f2f8" } },
        scales: { y: { ticks: { color: "#9aa3b8" } }, x: { ticks: { color: "#9aa3b8", maxRotation: 45 } } },
      },
    });
  }
}

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  try {
    await loadStats();
    await loadFilters();
    await loadCars();
  } catch (err) {
    console.error(err);
    document.querySelector(".container").innerHTML =
      `<div class="banner warning">Could not connect to API. Run: <code>uv run python scripts/run_server.py</code><br>${err.message}</div>`;
  }
}

init();
```

---

## `src/api/main.py`

```python
"""FastAPI backend for the Japan Car Import Advisory Platform."""

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.schemas import CalculateRequest, CostBreakdownResponse, PredictRequest
from src.calculator.import_cost import ImportCostBreakdown, calculate_import_cost
from src.config import settings
from src.database.models import CarListing, LocalMarketPrice, get_session, init_db
from src.ml.predict import predict_price
from src.services.analysis import build_savings_analysis, get_local_price, prepare_analysis_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Japan Car Import Advisory API", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


def _breakdown_to_response(result: ImportCostBreakdown) -> dict:
    kra = result.import_duty_kes + result.excise_duty_kes + result.vat_kes + result.rdl_kes + result.idf_kes
    data = result.to_dict()
    data["purchase_price_kes"] = round(result.purchase_price_usd * settings.usd_to_kes, 2)
    data["kra_taxes_kes"] = round(kra, 2)
    return data


def _load_cars_df() -> pd.DataFrame:
    session = get_session()
    try:
        rows = session.query(CarListing).filter(CarListing.is_cleaned == 1).all()
        if not rows:
            cleaned = settings.cleaned_data_dir / "cleaned_listings.csv"
            if cleaned.exists():
                return pd.read_csv(cleaned)
            return pd.DataFrame()
        return pd.DataFrame([{c.name: getattr(r, c.name) for c in CarListing.__table__.columns} for r in rows])
    finally:
        session.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
def stats():
    df = _load_cars_df()
    session = get_session()
    try:
        local_count = session.query(LocalMarketPrice).count()
    finally:
        session.close()
    return {
        "listings": len(df),
        "local_prices": local_count,
        "usd_to_kes": settings.usd_to_kes,
    }


@app.get("/api/filters")
def filters():
    df = _load_cars_df()
    if df.empty:
        return {"makes": [], "models": [], "years": []}
    return {
        "makes": sorted(df["make"].dropna().unique().tolist()),
        "models": sorted(df["model"].dropna().unique().tolist()),
        "years": sorted(df["year"].dropna().astype(int).unique().tolist()),
    }


@app.get("/api/cars")
def list_cars(
    make: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
):
    df = _load_cars_df()
    if df.empty:
        return []

    if make:
        df = df[df["make"] == make]
    if model:
        df = df[df["model"] == model]
    if year_min:
        df = df[df["year"] >= year_min]
    if year_max:
        df = df[df["year"] <= year_max]

    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "id": int(row["id"]) if pd.notna(row.get("id")) else None,
                "make": row["make"],
                "model": row["model"],
                "year": int(row["year"]),
                "mileage_km": int(row["mileage_km"]) if pd.notna(row.get("mileage_km")) else None,
                "engine_cc": int(row["engine_cc"]) if pd.notna(row.get("engine_cc")) else 1500,
                "fuel_type": row.get("fuel_type") or "Petrol",
                "transmission": row.get("transmission") or "Automatic",
                "body_type": row.get("body_type") or "Sedan",
                "price_usd": float(row["price_usd"]),
                "price_jpy": float(row["price_jpy"]) if pd.notna(row.get("price_jpy")) else None,
                "label": (
                    f"{row['make']} {row['model']} {int(row['year'])} | "
                    f"${float(row['price_usd']):,.0f} | {int(row['mileage_km']):,} km"
                ),
            }
        )
    return records


@app.get("/api/cars/{car_id}/compare")
def compare_car(car_id: int):
    df = _load_cars_df()
    if df.empty or "id" not in df.columns:
        raise HTTPException(404, "Car not found")

    match = df[df["id"] == car_id]
    if match.empty:
        raise HTTPException(404, "Car not found")

    row = match.iloc[0]
    session = get_session()
    try:
        local_kes = get_local_price(session, row["make"], row["model"], int(row["year"]))
    finally:
        session.close()

    result = calculate_import_cost(
        purchase_price_usd=float(row["price_usd"]),
        engine_cc=int(row.get("engine_cc") or 1500),
        fuel_type=row.get("fuel_type") or "Petrol",
        body_type=row.get("body_type") or "Sedan",
        local_market_kes=local_kes,
    )

    car = {
        "id": car_id,
        "make": row["make"],
        "model": row["model"],
        "year": int(row["year"]),
        "mileage_km": int(row["mileage_km"]) if pd.notna(row.get("mileage_km")) else None,
        "engine_cc": int(row.get("engine_cc") or 1500),
        "fuel_type": row.get("fuel_type") or "Petrol",
        "body_type": row.get("body_type") or "Sedan",
        "price_usd": float(row["price_usd"]),
    }

    breakdown = _breakdown_to_response(result)
    savings_pct = None
    if local_kes and result.potential_savings_kes is not None:
        savings_pct = round(result.potential_savings_kes / local_kes * 100, 1)

    return {"car": car, "breakdown": breakdown, "savings_pct": savings_pct}


@app.post("/api/calculate", response_model=CostBreakdownResponse)
def calculate(body: CalculateRequest):
    result = calculate_import_cost(
        purchase_price_usd=body.purchase_price_usd,
        engine_cc=body.engine_cc,
        fuel_type=body.fuel_type,
        body_type=body.body_type,
        local_market_kes=body.local_market_kes,
        shipping_usd=body.shipping_usd,
    )
    return _breakdown_to_response(result)


@app.post("/api/predict")
def predict(body: PredictRequest):
    try:
        prediction = predict_price(
            make=body.make,
            model=body.model,
            year=body.year,
            mileage_km=body.mileage_km,
            engine_cc=body.engine_cc,
            fuel_type=body.fuel_type,
            transmission=body.transmission,
            body_type=body.body_type,
            source_platform="BE FORWARD",
        )
    except FileNotFoundError:
        raise HTTPException(503, "ML model not trained. Run: uv run python scripts/train_model.py")

    session = get_session()
    try:
        local_kes = get_local_price(session, body.make, body.model, body.year)
    finally:
        session.close()

    import_result = calculate_import_cost(
        purchase_price_usd=prediction["price_usd"],
        engine_cc=body.engine_cc,
        fuel_type=body.fuel_type,
        body_type=body.body_type,
        local_market_kes=local_kes,
    )

    return {
        "prediction": prediction,
        "import_cost": _breakdown_to_response(import_result),
    }


@app.get("/api/market-data")
def market_data(make: str | None = None, year_min: int | None = None, year_max: int | None = None):
    df = _load_cars_df()
    if df.empty:
        return {"summary": {}, "listings": [], "by_make": []}

    analysis = prepare_analysis_dataset(df)
    if make:
        analysis = analysis[analysis["make"] == make]
    if year_min:
        analysis = analysis[analysis["year"] >= year_min]
    if year_max:
        analysis = analysis[analysis["year"] <= year_max]

    by_make = (
        analysis.groupby("make")["price_usd"]
        .agg(["mean", "min", "max", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_usd", "min": "min_usd", "max": "max_usd", "count": "count"})
        .to_dict("records")
    )

    listings = analysis.head(100)[
        ["make", "model", "year", "mileage_km", "engine_cc", "fuel_type", "price_usd", "price_jpy"]
    ].to_dict("records")

    return {
        "summary": {
            "total": len(analysis),
            "makes": int(analysis["make"].nunique()),
            "avg_price_usd": round(float(analysis["price_usd"].mean()), 2),
            "year_min": int(analysis["year"].min()),
            "year_max": int(analysis["year"].max()),
        },
        "listings": listings,
        "by_make": by_make,
    }


@app.get("/api/savings")
def savings():
    df = _load_cars_df()
    if df.empty:
        return {"summary": {}, "items": []}

    session = get_session()
    try:
        savings_df = build_savings_analysis(session, df)
    finally:
        session.close()

    if savings_df.empty:
        return {"summary": {}, "items": []}

    import_cheaper = int((savings_df["savings_kes"] > 0).sum())
    return {
        "summary": {
            "total": len(savings_df),
            "avg_savings_pct": round(float(savings_df["savings_pct"].mean()), 1),
            "import_cheaper": import_cheaper,
        },
        "items": savings_df.sort_values("savings_kes", ascending=False).to_dict("records"),
    }


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
```

---

## `src/api/schemas.py`

```python
"""API request/response schemas."""

from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    purchase_price_usd: float = Field(ge=500)
    engine_cc: int = Field(default=1500, ge=660, le=5000)
    fuel_type: str = "Petrol"
    body_type: str = "Sedan"
    local_market_kes: float | None = None
    shipping_usd: float | None = None


class PredictRequest(BaseModel):
    make: str
    model: str
    year: int = Field(ge=2018, le=2030)
    mileage_km: int = Field(ge=0)
    engine_cc: int = Field(ge=660)
    fuel_type: str = "Petrol"
    transmission: str = "Automatic"
    body_type: str = "Sedan"


class CostBreakdownResponse(BaseModel):
    purchase_price_usd: float
    shipping_usd: float
    insurance_usd: float
    cif_usd: float
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    rdl_kes: float
    idf_kes: float
    port_charges_kes: float
    clearing_fees_kes: float
    registration_kes: float
    other_charges_kes: float
    total_import_kes: float
    local_market_kes: float | None = None
    potential_savings_kes: float | None = None
    purchase_price_kes: float
    kra_taxes_kes: float
```

---

## `scripts/init_db.py`

```python
"""Initialize the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.models import init_db


def main():
    engine = init_db()
    print(f"Database initialized: {engine.url}")


if __name__ == "__main__":
    main()
```

---

## `scripts/run_scrapers.py`

```python
"""Run all scrapers or generate sample data."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.etl.pipeline import ETLPipeline
from src.scrapers.aaajapan import AAAJapanScraper
from src.scrapers.beforward import BeForwardScraper
from src.scrapers.carfromjapan import CarFromJapanScraper
from src.scrapers.japanesecartrade import JapaneseCarTradeScraper
from src.scrapers.sample_data import generate_local_market_prices, generate_sample_listings
from src.scrapers.sbt_japan import SBTJapanScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCRAPERS = [
    SBTJapanScraper,
    CarFromJapanScraper,
    AAAJapanScraper,
    JapaneseCarTradeScraper,
    BeForwardScraper,
]


def main():
    all_listings = []

    if settings.scraper_use_sample_data:
        logger.info("Using sample data (set SCRAPER_USE_SAMPLE_DATA=false to scrape live sites)")
        all_listings = generate_sample_listings(n=600)
    else:
        for scraper_cls in SCRAPERS:
            scraper = scraper_cls()
            try:
                listings = scraper.scrape()
                all_listings.extend(listings)
                logger.info("%s: %d listings", scraper.platform_name, len(listings))
            except Exception as exc:
                logger.error("%s failed: %s", scraper.platform_name, exc)

        if len(all_listings) < 50:
            logger.warning("Live scraping returned few results; supplementing with sample data")
            all_listings.extend(generate_sample_listings(n=400))

    local_prices = generate_local_market_prices(all_listings)
    pipeline = ETLPipeline()
    cleaned = pipeline.run(all_listings, local_prices)
    print(f"Pipeline complete: {len(cleaned)} cleaned records stored.")


if __name__ == "__main__":
    main()
```

---

## `scripts/run_pipeline.py`

```python
"""Run the full data pipeline: init → scrape → train."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def main():
    steps = [
        ("init_db.py", "Initializing database"),
        ("run_scrapers.py", "Scraping / generating data"),
        ("train_model.py", "Training ML model"),
    ]
    for script, label in steps:
        print(f"\n{'=' * 50}\n{label}\n{'=' * 50}")
        subprocess.run([PY, str(ROOT / "scripts" / script)], check=True)
    print("\nPipeline complete. Launch dashboard with:")
    print("  uv run python scripts/run_server.py")


if __name__ == "__main__":
    main()
```

---

## `scripts/run_server.py`

```python
"""Run the FastAPI web server."""

import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## `scripts/clean_data.py`

```python
"""Clean raw data and save to database."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.etl.cleaner import DataCleaner
from src.etl.pipeline import save_listings_to_db
from src.database.models import get_session, init_db


def main():
    init_db()
    raw_dir = settings.raw_data_dir
    raw_files = list(raw_dir.glob("*.csv")) if raw_dir.exists() else []

    if not raw_files:
        sample_file = settings.sample_data_dir / "sample_listings.csv"
        cleaned_file = settings.cleaned_data_dir / "cleaned_listings.csv"
        if cleaned_file.exists():
            print(f"Cleaned data already exists: {cleaned_file}")
            return
        if sample_file.exists():
            raw_files = [sample_file]
        else:
            print("No raw data found. Run: uv run python scripts/run_scrapers.py")
            return

    cleaner = DataCleaner()
    session = get_session()
    total = 0

    for file in raw_files:
        df = pd.read_csv(file)
        cleaned = cleaner.clean_dataframe(df)
        cleaner.save_cleaned(cleaned, filename=f"cleaned_{file.stem}.csv")
        total += save_listings_to_db(session, cleaned.to_dict("records"))

    session.close()
    print(f"Cleaned and stored {total} records.")


if __name__ == "__main__":
    main()
```

---

## `scripts/train_model.py`

```python
"""Train the price prediction model."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.ml.train import train_model


def main():
    cleaned_file = settings.cleaned_data_dir / "cleaned_listings.csv"
    if not cleaned_file.exists():
        print("No cleaned data. Run: uv run python scripts/run_scrapers.py")
        sys.exit(1)

    df = pd.read_csv(cleaned_file)
    metrics = train_model(df)
    print("Training complete:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
```

---

## `scripts/generate_sample_data.py`

```python
"""Generate sample CSV files for development."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scrapers.sample_data import generate_sample_listings, save_sample_csv


def main():
    listings = generate_sample_listings(n=500)
    path = save_sample_csv(listings)
    print(f"Sample data saved to {path}")


if __name__ == "__main__":
    main()
```

---

## `src/config.py`

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'japan_cars.db'}"
    usd_to_kes: float = 130.0
    jpy_to_usd: float = 0.0067
    scraper_delay_seconds: float = 2.0
    scraper_max_pages: int = 5
    scraper_use_sample_data: bool = True
    model_path: str = str(PROJECT_ROOT / "models" / "price_predictor.joblib")
    min_year: int = 2018

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def cleaned_data_dir(self) -> Path:
        return self.data_dir / "cleaned"

    @property
    def sample_data_dir(self) -> Path:
        return self.data_dir / "sample"


settings = Settings()
```

---

## `src/database/models.py`

```python
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings


class Base(DeclarativeBase):
    pass


class CarListing(Base):
    __tablename__ = "car_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_platform = Column(String(50), nullable=False, index=True)
    listing_id = Column(String(100))
    title = Column(String(300))
    make = Column(String(80), index=True)
    model = Column(String(120), index=True)
    year = Column(Integer, index=True)
    mileage_km = Column(Integer)
    engine_cc = Column(Integer)
    fuel_type = Column(String(30))
    transmission = Column(String(30))
    body_type = Column(String(50))
    price_jpy = Column(Float)
    price_usd = Column(Float)
    currency = Column(String(10), default="JPY")
    location = Column(String(100))
    listing_url = Column(Text)
    image_url = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_cleaned = Column(Integer, default=0)


class LocalMarketPrice(Base):
    __tablename__ = "local_market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    make = Column(String(80), index=True)
    model = Column(String(120), index=True)
    year = Column(Integer, index=True)
    avg_price_kes = Column(Float)
    min_price_kes = Column(Float)
    max_price_kes = Column(Float)
    source = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow)


class ImportCostEstimate(Base):
    __tablename__ = "import_cost_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_listing_id = Column(Integer)
    purchase_price_usd = Column(Float)
    shipping_usd = Column(Float)
    insurance_usd = Column(Float)
    cif_usd = Column(Float)
    import_duty_kes = Column(Float)
    excise_duty_kes = Column(Float)
    vat_kes = Column(Float)
    rdl_kes = Column(Float)
    idf_kes = Column(Float)
    port_charges_kes = Column(Float)
    clearing_fees_kes = Column(Float)
    registration_kes = Column(Float)
    other_charges_kes = Column(Float)
    total_import_kes = Column(Float)
    local_market_kes = Column(Float)
    potential_savings_kes = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=False, connect_args=connect_args)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine
```

---

## `src/utils/helpers.py`

```python
import re
from typing import Any

from src.config import settings


def jpy_to_usd(amount_jpy: float) -> float:
    return round(amount_jpy * settings.jpy_to_usd, 2)


def usd_to_kes(amount_usd: float) -> float:
    return round(amount_usd * settings.usd_to_kes, 2)


def parse_price(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(text).replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_mileage(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"([\d,]+)", str(text))
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_engine_cc(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d{3,4})", str(text))
    if match:
        return int(match.group(1))
    return None


def parse_year(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(20\d{2})", str(text))
    if match:
        year = int(match.group(1))
        if year >= settings.min_year:
            return year
    return None


def normalize_make_model(title: str) -> tuple[str | None, str | None]:
    if not title:
        return None, None
    parts = title.strip().split()
    if len(parts) >= 2:
        return parts[0].title(), " ".join(parts[1:3]).title()
    if parts:
        return parts[0].title(), None
    return None, None


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, "", "N/A"):
            return data[key]
    return default
```

---

## `src/scrapers/base.py`

```python
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CarListingData:
    source_platform: str
    listing_id: str | None = None
    title: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    engine_cc: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    body_type: str | None = None
    price_jpy: float | None = None
    price_usd: float | None = None
    currency: str = "JPY"
    location: str | None = None
    listing_url: str | None = None
    image_url: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_platform": self.source_platform,
            "listing_id": self.listing_id,
            "title": self.title,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "mileage_km": self.mileage_km,
            "engine_cc": self.engine_cc,
            "fuel_type": self.fuel_type,
            "transmission": self.transmission,
            "body_type": self.body_type,
            "price_jpy": self.price_jpy,
            "price_usd": self.price_usd,
            "currency": self.currency,
            "location": self.location,
            "listing_url": self.listing_url,
            "image_url": self.image_url,
        }


class BaseScraper(ABC):
    platform_name: str = "unknown"
    base_url: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.ua = UserAgent()
        self.delay = settings.scraper_delay_seconds

    def get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch(self, url: str) -> BeautifulSoup:
        logger.info("Fetching %s", url)
        response = self.session.get(url, headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        time.sleep(self.delay)
        return BeautifulSoup(response.content, "lxml")

    @abstractmethod
    def build_search_url(self, page: int = 1) -> str:
        pass

    @abstractmethod
    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        pass

    def scrape(self, max_pages: int | None = None) -> list[CarListingData]:
        max_pages = max_pages or settings.scraper_max_pages
        all_listings: list[CarListingData] = []

        for page in range(1, max_pages + 1):
            try:
                url = self.build_search_url(page)
                soup = self.fetch(url)
                listings = self.parse_listing_page(soup)
                if not listings:
                    logger.warning("%s: no listings on page %d", self.platform_name, page)
                    break
                all_listings.extend(listings)
                logger.info("%s: scraped %d listings from page %d", self.platform_name, len(listings), page)
            except Exception as exc:
                logger.error("%s page %d failed: %s", self.platform_name, page, exc)
                break

        return all_listings
```

---

## `src/scrapers/sample_data.py`

```python
"""Generate realistic sample car listing data for demo and ML training."""

import random
from datetime import datetime, timedelta

import pandas as pd

from src.config import settings
from src.scrapers.base import CarListingData
from src.utils.helpers import jpy_to_usd

PLATFORMS = [
    "SBT Japan",
    "Car From Japan",
    "AAAJapan",
    "JapaneseCarTrade",
    "BE FORWARD",
]

MAKES_MODELS = {
    "Toyota": ["Vitz", "Axio", "Fielder", "Harrier", "RAV4", "Prado", "Land Cruiser", "Premio", "Allion"],
    "Nissan": ["Note", "X-Trail", "Juke", "Serena", "Leaf", "Skyline"],
    "Honda": ["Fit", "Vezel", "CR-V", "Freed", "Stepwgn"],
    "Mazda": ["Demio", "CX-5", "Axela", "Atenza"],
    "Subaru": ["Impreza", "Forester", "Legacy", "XV"],
    "Mitsubishi": ["Outlander", "Pajero", "RVR", "Mirage"],
    "Suzuki": ["Swift", "Jimny", "Vitara", "Alto"],
}

FUEL_TYPES = ["Petrol", "Diesel", "Hybrid", "Electric"]
TRANSMISSIONS = ["Automatic", "Manual", "CVT"]
BODY_TYPES = ["Sedan", "SUV", "Hatchback", "Wagon", "Van", "Pickup"]


def _random_engine_cc(body_type: str) -> int:
    if body_type in ("SUV", "Pickup", "Van"):
        return random.choice([2000, 2500, 2800, 3000, 3500, 4000])
    if body_type == "Sedan":
        return random.choice([1300, 1500, 1800, 2000, 2500])
    return random.choice([660, 1000, 1200, 1500, 1800])


def _estimate_price_jpy(make: str, model: str, year: int, mileage: int, engine_cc: int) -> float:
    base = 800_000
    year_factor = (year - 2017) * 120_000
    mileage_factor = max(0, (120_000 - mileage) * 3)
    engine_factor = engine_cc * 80
    brand_factor = {"Toyota": 200_000, "Subaru": 150_000, "Honda": 120_000}.get(make, 80_000)
    noise = random.randint(-100_000, 150_000)
    return max(450_000, base + year_factor + mileage_factor + engine_factor + brand_factor + noise)


def generate_sample_listings(n: int = 500) -> list[CarListingData]:
    listings: list[CarListingData] = []
    current_year = datetime.now().year

    for i in range(n):
        make = random.choice(list(MAKES_MODELS.keys()))
        model = random.choice(MAKES_MODELS[make])
        year = random.randint(settings.min_year, current_year)
        mileage = random.randint(5_000, 180_000)
        body_type = random.choice(BODY_TYPES)
        engine_cc = _random_engine_cc(body_type)
        fuel_type = random.choice(FUEL_TYPES)
        transmission = random.choice(TRANSMISSIONS)
        platform = random.choice(PLATFORMS)
        price_jpy = _estimate_price_jpy(make, model, year, mileage, engine_cc)

        title = f"{make} {model} {year}"
        listing_id = f"{platform[:3].upper()}-{i + 1:05d}"

        listings.append(
            CarListingData(
                source_platform=platform,
                listing_id=listing_id,
                title=title,
                make=make,
                model=model,
                year=year,
                mileage_km=mileage,
                engine_cc=engine_cc,
                fuel_type=fuel_type,
                transmission=transmission,
                body_type=body_type,
                price_jpy=price_jpy,
                price_usd=jpy_to_usd(price_jpy),
                location="Japan",
                listing_url=f"https://example.com/{listing_id}",
            )
        )

    return listings


def generate_local_market_prices(listings: list[CarListingData]) -> pd.DataFrame:
    """Estimate Kenyan local market prices (typically 30-80% higher than import cost)."""
    rows = []
    for listing in listings:
        import_estimate_usd = (listing.price_usd or 0) + 1200  # rough landed cost proxy
        import_kes = import_estimate_usd * settings.usd_to_kes
        markup = random.uniform(1.25, 1.85)
        avg = import_kes * markup
        rows.append(
            {
                "make": listing.make,
                "model": listing.model,
                "year": listing.year,
                "avg_price_kes": round(avg, 0),
                "min_price_kes": round(avg * 0.9, 0),
                "max_price_kes": round(avg * 1.15, 0),
                "source": "Kenya Market Estimate",
            }
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["make", "model", "year"])
    return df


def save_sample_csv(listings: list[CarListingData], path=None) -> str:
    settings.sample_data_dir.mkdir(parents=True, exist_ok=True)
    path = path or settings.sample_data_dir / "sample_listings.csv"
    df = pd.DataFrame([item.to_dict() for item in listings])
    df["scraped_at"] = datetime.utcnow() - timedelta(days=random.randint(0, 30))
    df.to_csv(path, index=False)
    return str(path)
```

---

## `src/scrapers/sbt_japan.py`

```python
import logging
import re

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class SBTJapanScraper(BaseScraper):
    platform_name = "SBT Japan"
    base_url = "https://www.sbtjapan.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/used-cars/toyota?page={page}&year_from=2018"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".product-item, .car-item, .vehicle-card, article")

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, .title, .car-name, a")
                price_el = card.select_one(".price, .car-price, [class*='price']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")

                mileage_el = card.find(string=re.compile(r"km|mileage", re.I))
                mileage = parse_mileage(str(mileage_el)) if mileage_el else None

                listing_url = link_el["href"] if link_el and link_el.get("href") else None
                if listing_url and listing_url.startswith("/"):
                    listing_url = f"{self.base_url}{listing_url}"

                listing_id = None
                if listing_url:
                    match = re.search(r"/(\d+)/?$", listing_url)
                    listing_id = match.group(1) if match else listing_url.split("/")[-1]

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=listing_id,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=listing_url,
                        image_url=img_el.get("src") if img_el else None,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("SBT parse error: %s", exc)

        return listings
```

---

## `src/scrapers/carfromjapan.py`

```python
import logging
import re

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class CarFromJapanScraper(BaseScraper):
    platform_name = "Car From Japan"
    base_url = "https://carfromjapan.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/vehicle/search/year-from/2018/page/{page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".vehicle-item, .car-list-item, .product, .listing-card")

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, .vehicle-title, .title")
                price_el = card.select_one(".price, .vehicle-price, [class*='Price']")
                link_el = card.select_one("a[href*='/vehicle/'], a[href*='/car/']")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")

                spec_text = card.get_text(" ", strip=True)
                mileage = parse_mileage(spec_text)

                listing_url = link_el["href"] if link_el else None
                if listing_url and listing_url.startswith("/"):
                    listing_url = f"{self.base_url}{listing_url}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=listing_url.split("/")[-1] if listing_url else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=listing_url,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("CarFromJapan parse error: %s", exc)

        return listings
```

---

## `src/scrapers/aaajapan.py`

```python
import logging

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class AAAJapanScraper(BaseScraper):
    platform_name = "AAAJapan"
    base_url = "https://www.aaajapan.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/search?year_from=2018&page={page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".car-block, .vehicle, .stock-item, tr[data-id]")

        for card in cards:
            try:
                title_el = card.select_one("a, .car-name, .title")
                price_el = card.select_one(".price, .car-price, td.price")

                title = title_el.get_text(strip=True) if title_el else card.get_text(" ", strip=True)[:120]
                make, model = normalize_make_model(title)
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title)
                mileage = parse_mileage(card.get_text())

                link = title_el.get("href") if title_el and title_el.name == "a" else None
                if link and link.startswith("/"):
                    link = f"{self.base_url}{link}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=link.split("/")[-1] if link else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=link,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("AAAJapan parse error: %s", exc)

        return listings
```

---

## `src/scrapers/japanesecartrade.py`

```python
import logging

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class JapaneseCarTradeScraper(BaseScraper):
    platform_name = "JapaneseCarTrade"
    base_url = "https://www.japanesecartrade.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/used-cars?year_from=2018&page={page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".car-listing, .vehicle-box, .product-listing, .list-item")

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, .car-title, .title")
                price_el = card.select_one(".price, .car-price")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")
                mileage = parse_mileage(card.get_text())

                link_el = card.select_one("a[href]")
                link = link_el["href"] if link_el else None
                if link and link.startswith("/"):
                    link = f"{self.base_url}{link}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=link.split("/")[-1] if link else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=link,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("JCT parse error: %s", exc)

        return listings
```

---

## `src/scrapers/beforward.py`

```python
import logging

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class BeForwardScraper(BaseScraper):
    platform_name = "BE FORWARD"
    base_url = "https://www.beforward.jp"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/stocklist/make=Toyota/year_from=2018/page={page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".stock-list-row, .vehicle-item, .car-item, .stock-item")

        for card in cards:
            try:
                title_el = card.select_one("a.title, .car-name, h3, .stock-name")
                price_el = card.select_one(".price, .car-price, .stock-price")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")
                mileage = parse_mileage(card.get_text())

                link = title_el.get("href") if title_el and title_el.name == "a" else None
                if not link:
                    link_el = card.select_one("a[href*='/detail/']")
                    link = link_el["href"] if link_el else None
                if link and link.startswith("/"):
                    link = f"{self.base_url}{link}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=link.split("/")[-1] if link else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=link,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("BE FORWARD parse error: %s", exc)

        return listings
```

---

## `src/etl/cleaner.py`

```python
import logging
from datetime import datetime

import pandas as pd

from src.config import settings
from src.utils.helpers import jpy_to_usd, parse_engine_cc, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)

VALID_FUEL = {"petrol", "diesel", "hybrid", "electric", "lpg"}
VALID_TRANSMISSION = {"automatic", "manual", "cvt", "semi-automatic"}
VALID_BODY = {"sedan", "suv", "hatchback", "wagon", "van", "pickup", "coupe", "minivan"}


def _normalize_text(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text and text.lower() not in {"n/a", "na", "none", ""} else None


def _normalize_category(value, valid_set: set[str], default: str | None = None) -> str | None:
    text = _normalize_text(value)
    if not text:
        return default
    lowered = text.lower()
    for item in valid_set:
        if item in lowered:
            return item.title()
    return text.title()


class DataCleaner:
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        cleaned = df.copy()
        cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]

        # Standardize column names
        rename_map = {
            "platform": "source_platform",
            "source": "source_platform",
            "mileage": "mileage_km",
            "engine_size": "engine_cc",
            "engine": "engine_cc",
            "price": "price_jpy",
        }
        cleaned = cleaned.rename(columns={k: v for k, v in rename_map.items() if k in cleaned.columns})

        # Parse numeric fields from text where needed
        if "year" in cleaned.columns:
            cleaned["year"] = cleaned["year"].apply(
                lambda x: parse_year(str(x)) if not isinstance(x, (int, float)) or pd.isna(x) else int(x)
            )
        if "mileage_km" in cleaned.columns:
            cleaned["mileage_km"] = cleaned["mileage_km"].apply(
                lambda x: parse_mileage(str(x)) if not isinstance(x, (int, float)) or pd.isna(x) else int(x)
            )
        if "engine_cc" in cleaned.columns:
            cleaned["engine_cc"] = cleaned["engine_cc"].apply(
                lambda x: parse_engine_cc(str(x)) if not isinstance(x, (int, float)) or pd.isna(x) else int(x)
            )
        if "price_jpy" in cleaned.columns:
            cleaned["price_jpy"] = cleaned["price_jpy"].apply(
                lambda x: parse_price(str(x)) if not isinstance(x, (int, float)) or pd.isna(x) else float(x)
            )

        # Filter year >= 2018
        if "year" in cleaned.columns:
            cleaned = cleaned[cleaned["year"].notna() & (cleaned["year"] >= settings.min_year)]

        # Remove invalid prices
        if "price_jpy" in cleaned.columns:
            cleaned = cleaned[cleaned["price_jpy"].notna() & (cleaned["price_jpy"] > 100_000)]

        # Normalize categories
        if "fuel_type" in cleaned.columns:
            cleaned["fuel_type"] = cleaned["fuel_type"].apply(
                lambda x: _normalize_category(x, VALID_FUEL, "Petrol")
            )
        if "transmission" in cleaned.columns:
            cleaned["transmission"] = cleaned["transmission"].apply(
                lambda x: _normalize_category(x, VALID_TRANSMISSION, "Automatic")
            )
        if "body_type" in cleaned.columns:
            cleaned["body_type"] = cleaned["body_type"].apply(
                lambda x: _normalize_category(x, VALID_BODY, "Sedan")
            )

        # Compute USD price
        if "price_usd" not in cleaned.columns or cleaned["price_usd"].isna().all():
            cleaned["price_usd"] = cleaned["price_jpy"].apply(jpy_to_usd)

        # Deduplicate
        dedup_cols = [c for c in ["source_platform", "listing_id", "title", "price_jpy"] if c in cleaned.columns]
        if dedup_cols:
            cleaned = cleaned.drop_duplicates(subset=dedup_cols)

        cleaned["is_cleaned"] = 1
        cleaned["scraped_at"] = cleaned.get("scraped_at", datetime.utcnow())

        logger.info("Cleaned %d records (from %d)", len(cleaned), len(df))
        return cleaned.reset_index(drop=True)

    def save_cleaned(self, df: pd.DataFrame, filename: str = "cleaned_listings.csv") -> str:
        settings.cleaned_data_dir.mkdir(parents=True, exist_ok=True)
        path = settings.cleaned_data_dir / filename
        df.to_csv(path, index=False)
        logger.info("Saved cleaned data to %s", path)
        return str(path)
```

---

## `src/etl/pipeline.py`

```python
import logging
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import CarListing, LocalMarketPrice, init_db
from src.etl.cleaner import DataCleaner
from src.scrapers.base import CarListingData

logger = logging.getLogger(__name__)


def save_listings_to_db(session: Session, listings: Iterable[CarListingData | dict]) -> int:
    count = 0
    for item in listings:
        data = item.to_dict() if isinstance(item, CarListingData) else item
        record = CarListing(**{k: v for k, v in data.items() if hasattr(CarListing, k)})
        session.add(record)
        count += 1
    session.commit()
    return count


def load_listings_from_db(session: Session) -> pd.DataFrame:
    rows = session.query(CarListing).all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{c.name: getattr(r, c.name) for c in CarListing.__table__.columns} for r in rows])


def save_local_prices_to_db(session: Session, df: pd.DataFrame) -> int:
    count = 0
    for _, row in df.iterrows():
        record = LocalMarketPrice(
            make=row.get("make"),
            model=row.get("model"),
            year=int(row.get("year")),
            avg_price_kes=float(row.get("avg_price_kes")),
            min_price_kes=float(row.get("min_price_kes", row.get("avg_price_kes"))),
            max_price_kes=float(row.get("max_price_kes", row.get("avg_price_kes"))),
            source=row.get("source", "Kenya Market"),
        )
        session.add(record)
        count += 1
    session.commit()
    return count


class ETLPipeline:
    def __init__(self) -> None:
        self.cleaner = DataCleaner()
        init_db()

    def run(self, listings: list[CarListingData | dict], local_prices_df: pd.DataFrame | None = None) -> pd.DataFrame:
        from src.database.models import get_session

        df = pd.DataFrame(
            [item.to_dict() if isinstance(item, CarListingData) else item for item in listings]
        )
        cleaned = self.cleaner.clean_dataframe(df)
        self.cleaner.save_cleaned(cleaned)

        session = get_session()
        try:
            save_listings_to_db(session, cleaned.to_dict("records"))
            if local_prices_df is not None and not local_prices_df.empty:
                save_local_prices_to_db(session, local_prices_df)
        finally:
            session.close()

        return cleaned
```

---

## `src/calculator/kra_taxes.py`

```python
"""Kenya Revenue Authority (KRA) import duty calculations."""

from dataclasses import dataclass

from src.config import settings


@dataclass
class KRABreakdown:
    cif_kes: float
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    rdl_kes: float
    idf_kes: float
    total_tax_kes: float


def get_excise_rate(engine_cc: int, fuel_type: str = "Petrol") -> float:
    fuel = (fuel_type or "Petrol").lower()
    if "electric" in fuel:
        return 0.10
    if engine_cc <= 1500:
        return 0.20
    if engine_cc <= 3000:
        return 0.25
    return 0.35


def calculate_kra_taxes(
    cif_usd: float,
    engine_cc: int = 1500,
    fuel_type: str = "Petrol",
) -> KRABreakdown:
    """Calculate KRA taxes based on CIF value."""
    cif_kes = cif_usd * settings.usd_to_kes

    import_duty = cif_kes * 0.25
    excise_rate = get_excise_rate(engine_cc, fuel_type)
    excise_duty = cif_kes * excise_rate
    vat_base = cif_kes + import_duty + excise_duty
    vat = vat_base * 0.16
    rdl = cif_kes * 0.02
    idf = max(cif_kes * 0.0225, 5000)

    total = import_duty + excise_duty + vat + rdl + idf

    return KRABreakdown(
        cif_kes=round(cif_kes, 2),
        import_duty_kes=round(import_duty, 2),
        excise_duty_kes=round(excise_duty, 2),
        vat_kes=round(vat, 2),
        rdl_kes=round(rdl, 2),
        idf_kes=round(idf, 2),
        total_tax_kes=round(total, 2),
    )
```

---

## `src/calculator/import_cost.py`

```python
"""Full import cost calculator for Kenya."""

from dataclasses import dataclass, asdict

from src.calculator.kra_taxes import calculate_kra_taxes
from src.config import settings


@dataclass
class ImportCostBreakdown:
    purchase_price_usd: float
    shipping_usd: float
    insurance_usd: float
    cif_usd: float
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    rdl_kes: float
    idf_kes: float
    port_charges_kes: float
    clearing_fees_kes: float
    registration_kes: float
    other_charges_kes: float
    total_import_kes: float
    local_market_kes: float | None = None
    potential_savings_kes: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_shipping(body_type: str = "Sedan") -> float:
    """Estimate RoRo shipping cost USD from Japan to Mombasa."""
    rates = {
        "Sedan": 950,
        "Hatchback": 900,
        "SUV": 1100,
        "Wagon": 980,
        "Van": 1200,
        "Pickup": 1300,
    }
    return rates.get(body_type or "Sedan", 1000)


def estimate_insurance(fob_usd: float) -> float:
    return round(fob_usd * 0.015, 2)


def estimate_port_charges(body_type: str = "Sedan") -> float:
    base = {"Sedan": 45000, "SUV": 55000, "Van": 60000, "Pickup": 65000}
    return base.get(body_type or "Sedan", 50000)


def estimate_clearing_fees(cif_usd: float) -> float:
    return max(25000, cif_usd * settings.usd_to_kes * 0.02)


def estimate_registration(engine_cc: int) -> float:
    if engine_cc <= 1200:
        return 15000
    if engine_cc <= 2000:
        return 20000
    return 25000


def calculate_import_cost(
    purchase_price_usd: float,
    engine_cc: int = 1500,
    fuel_type: str = "Petrol",
    body_type: str = "Sedan",
    local_market_kes: float | None = None,
    shipping_usd: float | None = None,
) -> ImportCostBreakdown:
    shipping = shipping_usd if shipping_usd is not None else estimate_shipping(body_type)
    insurance = estimate_insurance(purchase_price_usd)
    cif_usd = purchase_price_usd + shipping + insurance

    kra = calculate_kra_taxes(cif_usd, engine_cc, fuel_type)
    port_charges = estimate_port_charges(body_type)
    clearing = estimate_clearing_fees(cif_usd)
    registration = estimate_registration(engine_cc)
    other = 15000  # inspection, handling, misc

    total_kes = (
        cif_usd * settings.usd_to_kes
        + kra.total_tax_kes
        + port_charges
        + clearing
        + registration
        + other
    )

    savings = None
    if local_market_kes is not None:
        savings = round(local_market_kes - total_kes, 2)

    return ImportCostBreakdown(
        purchase_price_usd=round(purchase_price_usd, 2),
        shipping_usd=round(shipping, 2),
        insurance_usd=insurance,
        cif_usd=round(cif_usd, 2),
        import_duty_kes=kra.import_duty_kes,
        excise_duty_kes=kra.excise_duty_kes,
        vat_kes=kra.vat_kes,
        rdl_kes=kra.rdl_kes,
        idf_kes=kra.idf_kes,
        port_charges_kes=port_charges,
        clearing_fees_kes=round(clearing, 2),
        registration_kes=registration,
        other_charges_kes=other,
        total_import_kes=round(total_kes, 2),
        local_market_kes=local_market_kes,
        potential_savings_kes=savings,
    )
```

---

## `src/ml/train.py`

```python
"""Train XGBoost model to predict car prices in Japan."""

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from src.config import settings

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "make",
    "model",
    "year",
    "mileage_km",
    "engine_cc",
    "fuel_type",
    "transmission",
    "body_type",
    "source_platform",
]
TARGET_COL = "price_jpy"
CATEGORICAL = ["make", "model", "fuel_type", "transmission", "body_type", "source_platform"]
NUMERIC = ["year", "mileage_km", "engine_cc"]


def prepare_training_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for col in FEATURE_COLS + [TARGET_COL]:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")

    data = data.dropna(subset=[TARGET_COL, "year", "mileage_km", "engine_cc"])
    data = data[data[TARGET_COL] > 0]

    for col in CATEGORICAL:
        data[col] = data[col].fillna("Unknown").astype(str)

    for col in NUMERIC:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=NUMERIC)

    return data


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", "passthrough", NUMERIC),
        ]
    )
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def train_model(df: pd.DataFrame, test_size: float = 0.2) -> dict:
    data = prepare_training_data(df)
    X = data[FEATURE_COLS]
    y = data[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = {
        "r2": round(r2_score(y_test, y_pred), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
        "mae": round(mean_absolute_error(y_test, y_pred), 2),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    model_path = Path(settings.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "feature_cols": FEATURE_COLS, "metrics": metrics}, model_path)

    logger.info("Model saved to %s | R²=%.4f RMSE=%.0f", model_path, metrics["r2"], metrics["rmse"])
    return metrics
```

---

## `src/ml/predict.py`

```python
"""Predict car prices using trained model."""

from pathlib import Path

import joblib
import pandas as pd

from src.config import settings
from src.utils.helpers import jpy_to_usd


def load_model():
    path = Path(settings.model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run: uv run python scripts/train_model.py"
        )
    return joblib.load(path)


def predict_price(
    make: str,
    model: str,
    year: int,
    mileage_km: int,
    engine_cc: int,
    fuel_type: str = "Petrol",
    transmission: str = "Automatic",
    body_type: str = "Sedan",
    source_platform: str = "SBT Japan",
) -> dict:
    artifact = load_model()
    pipeline = artifact["pipeline"]

    input_df = pd.DataFrame(
        [
            {
                "make": make,
                "model": model,
                "year": year,
                "mileage_km": mileage_km,
                "engine_cc": engine_cc,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "body_type": body_type,
                "source_platform": source_platform,
            }
        ]
    )

    price_jpy = float(pipeline.predict(input_df)[0])
    return {
        "price_jpy": round(price_jpy, 0),
        "price_usd": jpy_to_usd(price_jpy),
        "metrics": artifact.get("metrics", {}),
    }
```

---

## `tests/conftest.py`

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

---

## `tests/test_calculator.py`

```python
import pytest

from src.calculator.import_cost import calculate_import_cost
from src.calculator.kra_taxes import calculate_kra_taxes, get_excise_rate
from src.etl.cleaner import DataCleaner
import pandas as pd


def test_kra_taxes_basic():
    result = calculate_kra_taxes(cif_usd=10000, engine_cc=1500, fuel_type="Petrol")
    assert result.import_duty_kes > 0
    assert result.vat_kes > 0
    assert result.total_tax_kes == pytest.approx(
        result.import_duty_kes + result.excise_duty_kes + result.vat_kes + result.rdl_kes + result.idf_kes,
        rel=0.01,
    )


def test_excise_rate_electric():
    assert get_excise_rate(2000, "Electric") == 0.10


def test_import_cost_total():
    result = calculate_import_cost(purchase_price_usd=8000, engine_cc=1500, local_market_kes=2_000_000)
    assert result.total_import_kes > 0
    assert result.potential_savings_kes is not None


def test_data_cleaner():
    df = pd.DataFrame([
        {"make": "Toyota", "model": "Vitz", "year": 2019, "price_jpy": 900000, "mileage_km": 50000, "engine_cc": 1300},
        {"make": "Toyota", "model": "Vitz", "year": 2015, "price_jpy": 500000, "mileage_km": 100000, "engine_cc": 1300},
        {"make": "Nissan", "model": "Note", "year": 2020, "price_jpy": None, "mileage_km": 30000, "engine_cc": 1200},
    ])
    cleaner = DataCleaner()
    cleaned = cleaner.clean_dataframe(df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["year"] == 2019
```

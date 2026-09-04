const API = "/api";

let compareChart = null;
let breakdownChart = null;
let marketChart = null;
let savingsChart = null;
let carsCache = [];
let filterData = {
  models_by_make: {},
  models: [],
  makes: [],
  years: [],
  engines: [],
  mileages: [],
  fuels: [],
  transmissions: [],
  bodies: [],
};

const DEFAULT_MILEAGES = [10000, 20000, 30000, 45000, 60000, 80000, 100000, 120000, 150000, 200000];
const DEFAULT_ENGINES = [660, 1000, 1300, 1500, 1800, 2000, 2400, 2500, 3000, 3500, 4000];
const DEFAULT_FUELS = ["Petrol", "Diesel", "Hybrid", "Electric"];
const DEFAULT_TRANSMISSIONS = ["Automatic", "Manual", "CVT"];
const DEFAULT_BODIES = ["Sedan", "SUV", "Hatchback", "Wagon", "Van", "Minivan", "Pickup", "Coupe"];

function fillSelect(sel, values, { placeholder = null, selected = null, format = null } = {}) {
  sel.innerHTML = "";
  if (placeholder != null) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    sel.appendChild(opt);
  }
  values.forEach((value) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = format ? format(value) : value;
    if (selected != null && String(value) === String(selected)) opt.selected = true;
    sel.appendChild(opt);
  });
}

function uniqueSortedNumbers(values, fallback) {
  const nums = [...new Set((values || []).map(Number).filter((n) => Number.isFinite(n) && n >= 0))];
  nums.sort((a, b) => a - b);
  return nums.length ? nums : fallback;
}

const fmtKes = (n) => `KES ${Math.round(n).toLocaleString()}`;
const fmtUsd = (n) => `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err));
  }
  return res.json();
}

function formatApiError(err) {
  const detail = err?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        const msg = item.msg || JSON.stringify(item);
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return err?.message || "Request failed";
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
  filterData = await fetchJson(`${API}/filters`);
  const makeSel = document.getElementById("filter-make");
  filterData.makes.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    makeSel.appendChild(opt);
  });
  populateModelFilter("");
  if (filterData.years.length) {
    document.getElementById("filter-year-min").value = Math.min(...filterData.years);
    document.getElementById("filter-year-max").value = Math.max(...filterData.years);
  }
  initPredictForm();
}

function populatePredictModels(make, preferredModel = null) {
  const models = make ? (filterData.models_by_make[make] || []) : filterData.models || [];
  const modelSel = document.getElementById("predict-model");
  const selected = preferredModel && models.includes(preferredModel) ? preferredModel : models[0];
  fillSelect(modelSel, models, { selected });
}

function initPredictForm() {
  const makes = filterData.makes || [];
  const years = filterData.years?.length ? filterData.years : [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
  const engines = uniqueSortedNumbers(filterData.engines, DEFAULT_ENGINES).filter(
    (cc) => cc >= 660 && cc <= 5000
  );
  const mileages = DEFAULT_MILEAGES;
  const fuels = filterData.fuels?.length ? filterData.fuels : DEFAULT_FUELS;
  const transmissions = filterData.transmissions?.length ? filterData.transmissions : DEFAULT_TRANSMISSIONS;
  const bodies = filterData.bodies?.length ? filterData.bodies : DEFAULT_BODIES;

  const preferredMake = makes.includes("Toyota") ? "Toyota" : makes[0];
  fillSelect(document.getElementById("predict-make"), makes, { selected: preferredMake });
  populatePredictModels(preferredMake, "Harrier");

  fillSelect(document.getElementById("predict-year"), years, {
    selected: years.includes(2020) ? 2020 : years[Math.floor(years.length / 2)],
  });
  fillSelect(document.getElementById("predict-mileage"), mileages, {
    selected: mileages.includes(45000) ? 45000 : mileages[Math.floor(mileages.length / 2)],
    format: (v) => Number(v).toLocaleString(),
  });
  fillSelect(document.getElementById("predict-engine"), engines, {
    selected: engines.includes(2000) ? 2000 : engines[Math.floor(engines.length / 2)],
    format: (v) => `${v} cc`,
  });
  fillSelect(document.getElementById("predict-fuel"), fuels, {
    selected: fuels.find((f) => /petrol/i.test(f)) || fuels[0],
  });
  fillSelect(document.getElementById("predict-transmission"), transmissions, {
    selected: transmissions.find((t) => /automatic/i.test(t)) || transmissions[0],
  });
  fillSelect(document.getElementById("predict-body"), bodies, {
    selected: bodies.find((b) => /suv/i.test(b)) || bodies.find((b) => /sedan/i.test(b)) || bodies[0],
  });
}

document.getElementById("predict-make").addEventListener("change", (e) => {
  populatePredictModels(e.target.value);
});

function populateModelFilter(make) {
  const modelSel = document.getElementById("filter-model");
  modelSel.innerHTML = "<option value=''>All</option>";
  const models = make ? (filterData.models_by_make[make] || []) : filterData.models;
  models.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    modelSel.appendChild(opt);
  });
}

function renderCarSelect(cars) {
  const sel = document.getElementById("car-select");
  const search = document.getElementById("car-search").value.toLowerCase().trim();
  sel.innerHTML = "";

  const filtered = search
    ? cars.filter((c) => c.label.toLowerCase().includes(search) || `${c.make} ${c.model}`.toLowerCase().includes(search))
    : cars;

  document.getElementById("car-count").textContent =
    `(${filtered.length} cars · ${new Set(filtered.map((c) => c.make + c.model)).size} models)`;

  if (!filtered.length) {
    sel.innerHTML = "<option>No cars match your search</option>";
    document.getElementById("compare-result").classList.add("hidden");
    return;
  }

  filtered.forEach((car) => {
    const opt = document.createElement("option");
    opt.value = car.id;
    opt.textContent = car.label;
    sel.appendChild(opt);
  });

  if (filtered[0]?.id) showComparison(filtered[0].id);
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
  renderCarSelect(carsCache);
}

document.getElementById("filter-make").addEventListener("change", () => {
  populateModelFilter(document.getElementById("filter-make").value);
  loadCars();
});

document.getElementById("car-search").addEventListener("input", () => {
  renderCarSelect(carsCache);
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

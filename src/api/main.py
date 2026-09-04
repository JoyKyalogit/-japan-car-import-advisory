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
from src.services.exchange_rate import get_usd_to_kes
from src.utils.helpers import is_missing, json_safe

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Japan Car Import Advisory API", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()
    get_usd_to_kes()


def _breakdown_to_response(result: ImportCostBreakdown) -> dict:
    kra = result.import_duty_kes + result.excise_duty_kes + result.vat_kes + result.rdl_kes + result.idf_kes
    data = result.to_dict()
    data["purchase_price_kes"] = round(result.purchase_price_usd * result.usd_to_kes, 2)
    data["kra_taxes_kes"] = round(kra, 2)
    return json_safe(data)


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
        "usd_to_kes": get_usd_to_kes(),
        "exchange_rate_live": settings.use_live_exchange_rate,
    }


@app.get("/api/filters")
def filters():
    df = _load_cars_df()
    if df.empty:
        return {
            "makes": [],
            "models": [],
            "years": [],
            "models_by_make": {},
            "engines": [],
            "fuels": [],
            "transmissions": [],
            "bodies": [],
            "totals": {},
        }

    models_by_make = {}
    for make in df["make"].dropna().unique():
        models_by_make[make] = sorted(df[df["make"] == make]["model"].dropna().unique().tolist())

    return {
        "makes": sorted(df["make"].dropna().unique().tolist()),
        "models": sorted(df["model"].dropna().unique().tolist()),
        "years": sorted(df["year"].dropna().astype(int).unique().tolist()),
        "models_by_make": models_by_make,
        "engines": sorted(
            int(v)
            for v in df["engine_cc"].dropna().unique().tolist()
            if 660 <= int(v) <= 5000
        ),
        "fuels": sorted(df["fuel_type"].dropna().unique().tolist()) if "fuel_type" in df.columns else [],
        "transmissions": sorted(df["transmission"].dropna().unique().tolist()) if "transmission" in df.columns else [],
        "bodies": sorted(df["body_type"].dropna().unique().tolist()) if "body_type" in df.columns else [],
        "totals": {
            "listings": len(df),
            "makes": int(df["make"].nunique()),
            "models": int(df.groupby(["make", "model"]).ngroups),
        },
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
        mileage = None if is_missing(row.get("mileage_km")) else int(row["mileage_km"])
        records.append(
            {
                "id": None if is_missing(row.get("id")) else int(row["id"]),
                "make": row["make"],
                "model": row["model"],
                "year": int(row["year"]),
                "mileage_km": mileage,
                "engine_cc": 1500 if is_missing(row.get("engine_cc")) else int(row["engine_cc"]),
                "fuel_type": json_safe(row.get("fuel_type")) or "Petrol",
                "transmission": json_safe(row.get("transmission")) or "Automatic",
                "body_type": json_safe(row.get("body_type")) or "Sedan",
                "price_usd": float(row["price_usd"]),
                "cf_price_usd": None if is_missing(row.get("cf_price_usd")) else float(row["cf_price_usd"]),
                "destination_port": json_safe(row.get("destination_port")),
                "price_jpy": None if is_missing(row.get("price_jpy")) else float(row["price_jpy"]),
                "label": (
                    f"{row['make']} {row['model']} {int(row['year'])} | "
                    f"${float(row['price_usd']):,.0f} | {mileage:,} km"
                    if mileage is not None
                    else f"{row['make']} {row['model']} {int(row['year'])} | ${float(row['price_usd']):,.0f}"
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

    cf_price = row.get("cf_price_usd")
    result = calculate_import_cost(
        purchase_price_usd=float(row["price_usd"]),
        engine_cc=int(row.get("engine_cc") or 1500),
        fuel_type=row.get("fuel_type") or "Petrol",
        body_type=row.get("body_type") or "Sedan",
        local_market_kes=local_kes,
        cf_price_usd=float(cf_price) if pd.notna(cf_price) else None,
        make=row.get("make"),
        model=row.get("model"),
        year=int(row["year"]),
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
        cf_price_usd=body.cf_price_usd,
        make=body.make,
        model=body.model,
        year=body.year,
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

    # Show a balanced sample across makes (not only the first 100 DB rows).
    sample_parts = []
    for make_name, group in analysis.groupby("make", sort=True):
        sample_parts.append(group.head(5))
    listings_df = pd.concat(sample_parts, ignore_index=True) if sample_parts else analysis.head(0)
    listings_df = listings_df.head(120)

    listings = listings_df[
        ["make", "model", "year", "mileage_km", "engine_cc", "fuel_type", "price_usd", "price_jpy"]
    ].to_dict("records")

    return json_safe(
        {
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
    )


@app.get("/api/savings")
def savings():
    df = _load_cars_df()
    if df.empty:
        return {"summary": {}, "items": []}

    # Prefer a mix of makes so the tab is not only the first scrape batch.
    if len(df) > 200 and "make" in df.columns:
        parts = []
        for _, group in df.groupby(df["make"].astype(str), sort=False):
            parts.append(group.head(max(8, 200 // max(df["make"].nunique(), 1))))
        df = pd.concat(parts, ignore_index=True).head(200)

    session = get_session()
    try:
        savings_df = build_savings_analysis(session, df, limit=200)
    finally:
        session.close()

    if savings_df.empty:
        return {"summary": {}, "items": []}

    import_cheaper = int((savings_df["savings_kes"] > 0).sum())
    return json_safe(
        {
            "summary": {
                "total": len(savings_df),
                "avg_savings_pct": round(float(savings_df["savings_pct"].mean()), 1),
                "import_cheaper": import_cheaper,
            },
            "items": savings_df.sort_values("savings_kes", ascending=False).to_dict("records"),
        }
    )


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

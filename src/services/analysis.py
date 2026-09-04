"""Analysis helpers: import cost comparison from database listings."""

from __future__ import annotations

import re

import pandas as pd
from sqlalchemy.orm import Session

from src.calculator.import_cost import ImportCostBreakdown, calculate_import_cost
from src.database.models import ImportCostEstimate, LocalMarketPrice

# Max year gap when falling back to a nearby Kenya listing.
_MAX_YEAR_DISTANCE = 5

# Grade / trim / marketing noise that should not block matching.
_MODEL_NOISE = {
    "m",
    "sport",
    "msport",
    "aircus",
    "airsus",
    "airsuspension",
    "suspension",
    "package",
    "pkg",
    "xdrive",
    "drive",
    "awd",
    "4wd",
    "2wd",
    "fwd",
    "rwd",
    "hybrid",
    "petrol",
    "diesel",
    "automatic",
    "manual",
    "auto",
    "black",
    "white",
    "silver",
    "grey",
    "gray",
    "blue",
    "red",
    "pearl",
    "edition",
    "limited",
    "premium",
    "exclusive",
    "luxury",
    "type",
    "series",
    "van",
    "wagon",
    "truck",
    "long",
    "short",
    "dx",
    "gx",
    "gl",
    "ex",
    "lx",
    "sx",
    "rs",
    "xg",
    "mx",
    "ve",
    "xl",
    "kc",
    "ac",
    "ps",
    "vp",
    "comfort",
    "sensing",
    "honda",
    "hev",
    "phev",
    "home",
    "expert",
    "brawny",
    "front",
    "power",
    "window",
    "turbo",
    "petrol",
    "diesel",
    "cc",
}

# Canonical aliases for market naming differences (Japan ↔ Kenya).
_MODEL_ALIASES = {
    "regiusace": "hiace",
    "regius": "hiace",
    "ad": "advan",
    "advan": "advan",
    "atenza": "mazda6",
    "axela": "mazda3",
    "demio": "mazda2",
    "verisa": "mazda2",
    "familia": "mazda2",
    "premacy": "mazda5",
    "vitz": "yaris",
    "passo": "passo",
    "ist": "ist",
}


def normalize_model_name(model: str | None) -> str:
    text = (model or "").lower()
    text = text.replace("e:hev", " hev ").replace("e hev", " hev ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Common phrase aliases before tokenization.
    text = text.replace("ad van", "advan")
    text = text.replace("regius ace", "hiace")
    text = re.sub(r"\b(19|20)\d{2}\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def model_tokens(model: str | None) -> list[str]:
    tokens = normalize_model_name(model).split()
    cleaned: list[str] = []
    for token in tokens:
        token = _MODEL_ALIASES.get(token, token)
        if token in _MODEL_NOISE:
            continue
        if re.fullmatch(r"\d{4}", token):
            continue
        if re.fullmatch(r"\d+(\.\d+)?", token):
            continue
        # Drop lone "x" left behind from "x drive"
        if token == "x":
            continue
        cleaned.append(token)
    return cleaned


def base_model_key(model: str | None) -> str:
    tokens = model_tokens(model)
    if not tokens:
        return normalize_model_name(model)
    key = tokens[0]
    return _MODEL_ALIASES.get(key, key)


def models_compatible(left: str | None, right: str | None) -> bool:
    """Return True when two model strings likely refer to the same vehicle family."""
    left_norm = normalize_model_name(left)
    right_norm = normalize_model_name(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    if left_norm in right_norm or right_norm in left_norm:
        return True

    left_tokens = set(model_tokens(left))
    right_tokens = set(model_tokens(right))
    if not left_tokens or not right_tokens:
        return False

    left_base = base_model_key(left)
    right_base = base_model_key(right)
    if left_base and right_base and left_base == right_base:
        return True
    if left_base in right_tokens or right_base in left_tokens:
        return True
    return bool(left_tokens & right_tokens)


def get_local_price(session: Session, make: str, model: str, year: int) -> float | None:
    year = int(year)

    record = (
        session.query(LocalMarketPrice)
        .filter(
            LocalMarketPrice.make == make,
            LocalMarketPrice.model == model,
            LocalMarketPrice.year == year,
        )
        .first()
    )
    if record:
        return record.avg_price_kes

    # Search same make across nearby years, then pick the closest compatible model.
    candidates = (
        session.query(LocalMarketPrice)
        .filter(
            LocalMarketPrice.make.ilike(make),
            LocalMarketPrice.year >= year - _MAX_YEAR_DISTANCE,
            LocalMarketPrice.year <= year + _MAX_YEAR_DISTANCE,
        )
        .all()
    )
    return _pick_local_price(model, year, candidates)


def _pick_local_price(model: str, year: int, candidates: list[LocalMarketPrice]) -> float | None:
    scored: list[tuple[int, int, int, float]] = []
    for candidate in candidates:
        if not models_compatible(model, candidate.model):
            continue
        year_distance = abs(int(candidate.year) - year)
        specificity = len(normalize_model_name(candidate.model))
        scored.append((year_distance, specificity, int(candidate.id or 0), float(candidate.avg_price_kes)))

    if not scored:
        return None

    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return scored[0][3]


def _local_price_from_index(
    make: str,
    model: str,
    year: int,
    by_make_year: dict[tuple[str, int], list[LocalMarketPrice]],
    by_make: dict[str, list[LocalMarketPrice]],
) -> float | None:
    """In-memory local price lookup (same rules as get_local_price)."""
    year = int(year)
    make_key = (make or "").strip().lower()
    make_keys = [make_key]
    if " " in make_key:
        make_keys.append(make_key.split()[0])
    # Common scrape truncations / casing variants
    aliases = {"land rover": "land", "mercedes-benz": "mercedes", "mercedes benz": "mercedes"}
    if make_key in aliases:
        make_keys.append(aliases[make_key])

    for key in make_keys:
        exact_pool = by_make_year.get((key, year), [])
        for candidate in exact_pool:
            if normalize_model_name(candidate.model) == normalize_model_name(model):
                return float(candidate.avg_price_kes)

    nearby: list[LocalMarketPrice] = []
    for key in make_keys:
        for y in range(year - _MAX_YEAR_DISTANCE, year + _MAX_YEAR_DISTANCE + 1):
            nearby.extend(by_make_year.get((key, y), []))
    if not nearby:
        for key in make_keys:
            nearby.extend(
                [c for c in by_make.get(key, []) if abs(int(c.year) - year) <= _MAX_YEAR_DISTANCE]
            )
    return _pick_local_price(model, year, nearby)


def estimate_for_listing(row: dict | pd.Series, local_market_kes: float | None = None) -> ImportCostBreakdown:
    cf_price = row.get("cf_price_usd")
    cf_price_usd = float(cf_price) if pd.notna(cf_price) else None

    raw_cc = row.get("engine_cc")
    if pd.notna(raw_cc) and float(raw_cc) > 0:
        engine_cc = int(float(raw_cc))
    else:
        engine_cc = 1500

    raw_year = row.get("year")
    year = int(float(raw_year)) if pd.notna(raw_year) else None

    return calculate_import_cost(
        purchase_price_usd=float(row["price_usd"]),
        engine_cc=engine_cc,
        fuel_type=row.get("fuel_type") or "Petrol",
        body_type=row.get("body_type") or "Sedan",
        local_market_kes=local_market_kes,
        cf_price_usd=cf_price_usd,
        make=row.get("make"),
        model=row.get("model"),
        year=year,
    )


def save_import_estimate(session: Session, car_listing_id: int | None, result: ImportCostBreakdown) -> None:
    record = ImportCostEstimate(
        car_listing_id=car_listing_id,
        purchase_price_usd=result.purchase_price_usd,
        shipping_usd=result.shipping_usd,
        insurance_usd=result.insurance_usd,
        cif_usd=result.cif_usd,
        import_duty_kes=result.import_duty_kes,
        excise_duty_kes=result.excise_duty_kes,
        vat_kes=result.vat_kes,
        rdl_kes=result.rdl_kes,
        idf_kes=result.idf_kes,
        port_charges_kes=result.port_charges_kes,
        clearing_fees_kes=result.clearing_fees_kes,
        registration_kes=result.registration_kes,
        other_charges_kes=result.other_charges_kes,
        total_import_kes=result.total_import_kes,
        local_market_kes=result.local_market_kes,
        potential_savings_kes=result.potential_savings_kes,
    )
    session.add(record)
    session.commit()


def build_savings_analysis(session: Session, listings_df: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
    """Compare import cost vs local market for all listings with local price data."""
    rows = []
    data = listings_df.head(limit) if limit else listings_df

    # Load Kenya prices once; per-row SQL was too slow for the Savings tab.
    local_rows = session.query(LocalMarketPrice).all()
    by_make_year: dict[tuple[str, int], list[LocalMarketPrice]] = {}
    by_make: dict[str, list[LocalMarketPrice]] = {}
    for item in local_rows:
        make_key = (item.make or "").strip().lower()
        by_make_year.setdefault((make_key, int(item.year)), []).append(item)
        by_make.setdefault(make_key, []).append(item)
        # Handle truncated scrapes like "Land" for "Land Rover"
        if " " in make_key:
            by_make.setdefault(make_key.split()[0], []).append(item)

    for _, row in data.iterrows():
        try:
            if pd.isna(row.get("year")) or pd.isna(row.get("price_usd")):
                continue
            year = int(float(row["year"]))
            local = _local_price_from_index(
                row["make"], row["model"], year, by_make_year, by_make
            )
            if not local:
                continue

            cost = estimate_for_listing(row, local_market_kes=local)

            rows.append(
                {
                    "listing_id": row.get("id"),
                    "vehicle": f"{row['make']} {row['model']} {year}",
                    "purchase_usd": cost.purchase_price_usd,
                    "shipping_usd": cost.shipping_usd,
                    "cf_price_usd": cost.cf_price_usd,
                    "kra_taxes_kes": (
                        cost.import_duty_kes + cost.excise_duty_kes + cost.vat_kes + cost.rdl_kes + cost.idf_kes
                    ),
                    "port_clearing_reg_kes": cost.port_charges_kes + cost.clearing_fees_kes + cost.registration_kes,
                    "other_charges_kes": cost.other_charges_kes,
                    "total_import_kes": cost.total_import_kes,
                    "local_market_kes": local,
                    "savings_kes": cost.potential_savings_kes,
                    "savings_pct": round((cost.potential_savings_kes or 0) / local * 100, 1) if local else 0,
                }
            )
        except (TypeError, ValueError, KeyError):
            continue

    return pd.DataFrame(rows)


def prepare_analysis_dataset(listings_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare cleaned listings for exploratory analysis."""
    if listings_df.empty:
        return listings_df

    analysis = listings_df.copy()
    analysis["price_usd"] = pd.to_numeric(analysis["price_usd"], errors="coerce")
    analysis["price_jpy"] = pd.to_numeric(analysis["price_jpy"], errors="coerce")
    analysis["mileage_km"] = pd.to_numeric(analysis["mileage_km"], errors="coerce")
    analysis["engine_cc"] = pd.to_numeric(analysis["engine_cc"], errors="coerce")
    analysis["year"] = pd.to_numeric(analysis["year"], errors="coerce").astype("Int64")
    analysis["vehicle"] = analysis["make"] + " " + analysis["model"] + " " + analysis["year"].astype(str)
    analysis["price_per_km"] = analysis["price_jpy"] / analysis["mileage_km"].clip(lower=1)
    return analysis

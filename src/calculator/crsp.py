"""CRSP lookup and customs valuation helpers."""

from __future__ import annotations

import logging
import re
from datetime import datetime

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)

DEPRECIATION_BY_AGE = {
    0: 1.00,
    1: 0.90,
    2: 0.80,
    3: 0.70,
    4: 0.60,
    5: 0.50,
    6: 0.45,
    7: 0.40,
    8: 0.35,
}


def _crsp_path():
    return settings.data_dir / "reference" / "crsp.csv"


def load_crsp_table() -> pd.DataFrame:
    path = _crsp_path()
    if not path.exists():
        return pd.DataFrame(columns=["make", "model", "crsp_kes"])
    df = pd.read_csv(path)
    df.columns = [col.strip().lower() for col in df.columns]
    return df


def _normalize(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _score_match(model_key: str, row_model: str, engine_cc: int | None, row_engine) -> int:
    score = 0
    if row_model == model_key:
        score += 100
    elif row_model in model_key or model_key in row_model:
        score += 60
    else:
        model_tokens = set(model_key.split())
        row_tokens = set(row_model.split())
        overlap = len(model_tokens & row_tokens)
        if overlap:
            score += overlap * 10

    if engine_cc and pd.notna(row_engine):
        try:
            row_cc = int(float(row_engine))
            if abs(row_cc - engine_cc) <= 100:
                score += 20
        except (TypeError, ValueError):
            pass
    return score


def lookup_crsp(
    make: str | None,
    model: str | None,
    year: int | None = None,
    engine_cc: int | None = None,
) -> float | None:
    if not make or not model:
        return None

    table = load_crsp_table()
    if table.empty:
        return None

    make_key = _normalize(make).title()
    model_key = _normalize(model)
    candidates = table[table["make"].astype(str).str.lower() == make_key.lower()]
    if candidates.empty:
        return None

    best_score = -1
    best_value = None
    for _, row in candidates.iterrows():
        row_model = _normalize(str(row.get("model", "")))
        score = _score_match(model_key, row_model, engine_cc, row.get("engine_cc"))
        if score > best_score:
            best_score = score
            best_value = float(row["crsp_kes"])

    if best_score <= 0:
        return None
    return best_value


def depreciation_factor(year: int | None) -> float:
    if not year:
        return 1.0
    age = max(datetime.now().year - int(year), 0)
    if age in DEPRECIATION_BY_AGE:
        return DEPRECIATION_BY_AGE[age]
    return 0.30 if age > 8 else DEPRECIATION_BY_AGE.get(age, 0.35)


def customs_value_kes(
    cif_kes: float,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
    engine_cc: int | None = None,
) -> tuple[float, str]:
    crsp = lookup_crsp(make, model, year=year, engine_cc=engine_cc)
    if crsp:
        depreciated = crsp * depreciation_factor(year)
        value = max(cif_kes, depreciated)
        source = load_crsp_table()["source"].iloc[0] if "source" in load_crsp_table().columns else "KRA CRSP"
        return round(value, 2), f"max(CIF, depreciated CRSP from {source})"

    return round(cif_kes, 2), "CIF"

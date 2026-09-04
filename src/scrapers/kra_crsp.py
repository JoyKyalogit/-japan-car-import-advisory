"""Download and parse the official KRA CRSP Excel publication."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

from src.config import settings

logger = logging.getLogger(__name__)

KRA_CRSP_URL = "https://www.kra.go.ke/images/publications/New-CRSP---July-2025.xlsx"
VEHICLE_SHEET = "M.Vehicle CRSP July 2025"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in df.columns:
        key = re.sub(r"\s+", " ", str(column).strip()).lower()
        if key == "make":
            renamed[column] = "make"
        elif key == "model":
            renamed[column] = "model"
        elif "engine" in key:
            renamed[column] = "engine_cc"
        elif "body" in key:
            renamed[column] = "body_type"
        elif key == "fuel":
            renamed[column] = "fuel_type"
        elif "crsp" in key:
            renamed[column] = "crsp_kes"
        elif "transmission" in key:
            renamed[column] = "transmission"
    return df.rename(columns=renamed)


def _clean_crsp_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalize_columns(df)
    required = {"make", "model", "crsp_kes"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"CRSP sheet missing columns: {missing}")

    cleaned = df.copy()
    cleaned["make"] = cleaned["make"].astype(str).str.strip().str.title()
    cleaned["model"] = cleaned["model"].astype(str).str.strip().str.title()
    cleaned["crsp_kes"] = pd.to_numeric(cleaned["crsp_kes"], errors="coerce")
    cleaned = cleaned[cleaned["make"].notna() & cleaned["model"].notna() & cleaned["crsp_kes"].notna()]
    cleaned = cleaned[~cleaned["make"].str.lower().isin({"make", "nan"})]

    if "engine_cc" in cleaned.columns:
        cleaned["engine_cc"] = pd.to_numeric(
            cleaned["engine_cc"].astype(str).str.extract(r"(\d+)")[0],
            errors="coerce",
        )

    for column in ("fuel_type", "body_type", "transmission"):
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype(str).str.strip().str.title()
            cleaned.loc[cleaned[column].str.lower().isin({"nan", "none"}), column] = None

    cleaned["source"] = "KRA CRSP July 2025"
    cleaned["updated_at"] = datetime.utcnow().isoformat()
    return cleaned.reset_index(drop=True)


def download_kra_crsp(url: str = KRA_CRSP_URL) -> bytes:
    logger.info("Downloading KRA CRSP from %s", url)
    response = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content


def parse_kra_crsp(content: bytes, sheet_name: str = VEHICLE_SHEET) -> pd.DataFrame:
    raw = pd.read_excel(BytesIO(content), sheet_name=sheet_name, header=1)
    return _clean_crsp_frame(raw)


def save_crsp_table(df: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or settings.data_dir / "reference" / "crsp.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved %d CRSP records to %s", len(df), path)
    return path


def fetch_and_save_kra_crsp(url: str = KRA_CRSP_URL) -> pd.DataFrame:
    content = download_kra_crsp(url)
    parsed = parse_kra_crsp(content)
    save_crsp_table(parsed)
    raw_path = settings.data_dir / "reference" / "kra_crsp_july_2025.xlsx"
    raw_path.write_bytes(content)
    logger.info("Saved raw KRA workbook to %s", raw_path)
    return parsed

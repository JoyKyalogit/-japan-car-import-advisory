import logging
from datetime import datetime

import pandas as pd

from src.config import settings
from src.utils.helpers import jpy_to_usd, parse_engine_cc, parse_mileage, parse_price, parse_year, usd_to_jpy

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

        # Keep only cars within configured year range (default 2018-2026)
        if settings.scrape_filter_year_range and "year" in cleaned.columns:
            cleaned = cleaned[
                cleaned["year"].notna()
                & (cleaned["year"] >= settings.min_year)
                & (cleaned["year"] <= settings.max_year)
            ]

        # Normalize USD listings (e.g. BE FORWARD prices are in USD)
        if "currency" in cleaned.columns and "price_usd" in cleaned.columns:
            usd_mask = cleaned["currency"].astype(str).str.upper() == "USD"
            if usd_mask.any():
                cleaned.loc[usd_mask, "price_jpy"] = cleaned.loc[usd_mask, "price_usd"].apply(
                    lambda x: usd_to_jpy(x) if pd.notna(x) else None
                )

        # Remove invalid prices
        price_ok = pd.Series(True, index=cleaned.index)
        if "price_usd" in cleaned.columns:
            price_ok &= cleaned["price_usd"].notna() & (cleaned["price_usd"] >= 500)
        elif "price_jpy" in cleaned.columns:
            price_ok &= cleaned["price_jpy"].notna() & (cleaned["price_jpy"] > 100_000)
        cleaned = cleaned[price_ok]

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

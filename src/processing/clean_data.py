"""Clean raw car listing data."""

from pathlib import Path

import pandas as pd

from src.etl.cleaner import DataCleaner
from src.config import settings


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw listings DataFrame."""
    cleaner = DataCleaner()
    return cleaner.clean_dataframe(df)


def load_and_clean(csv_path: str | Path) -> pd.DataFrame:
    """Load a CSV file and return cleaned data."""
    df = pd.read_csv(csv_path)
    cleaned = clean_listings(df)
    cleaner = DataCleaner()
    cleaner.save_cleaned(cleaned)
    return cleaned


def clean_from_raw_dir() -> pd.DataFrame:
    """Clean all CSV files in the raw data directory."""
    raw_dir = settings.raw_data_dir
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    frames = []
    for csv_file in raw_dir.glob("*.csv"):
        frames.append(load_and_clean(csv_file))

    if not frames:
        raise FileNotFoundError("No CSV files found in raw data directory")

    return pd.concat(frames, ignore_index=True)

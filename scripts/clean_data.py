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

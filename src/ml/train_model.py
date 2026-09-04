"""Train the price prediction model (module entry point)."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import settings
from src.ml.train import train_model


def main():
    cleaned_file = settings.cleaned_data_dir / "cleaned_listings.csv"
    if not cleaned_file.exists():
        print("No cleaned data found. Run: uv run python scripts/run_scrapers.py")
        sys.exit(1)

    df = pd.read_csv(cleaned_file)
    metrics = train_model(df)
    print("Training complete:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

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

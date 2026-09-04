"""Generate realistic sample car listing data for demo and ML training."""

import random
from datetime import datetime, timedelta

import pandas as pd

from src.config import settings
from src.scrapers.base import CarListingData
from src.utils.helpers import jpy_to_usd

PLATFORMS = [
    "SBT Japan",
    "Car From Japan",
    "AAAJapan",
    "JapaneseCarTrade",
    "BE FORWARD",
]

MAKES_MODELS = {
    "Toyota": [
        "Vitz", "Axio", "Fielder", "Harrier", "RAV4", "Prado", "Land Cruiser",
        "Premio", "Allion", "Corolla", "Camry", "Fortuner", "Hiace", "Noah",
        "Wish", "C-HR", "Mark X", "Probox", "Rush", "Succeed",
    ],
    "Nissan": [
        "Note", "X-Trail", "Juke", "Serena", "Leaf", "Skyline", "Navara",
        "March", "Dualis", "Tiida", "AD", "Wingroad", "Qashqai", "Murano",
    ],
    "Honda": [
        "Fit", "Vezel", "CR-V", "Freed", "Stepwgn", "Accord", "Civic",
        "Shuttle", "Stream", "Odyssey", "HR-V", "City",
    ],
    "Mazda": ["Demio", "CX-5", "Axela", "Atenza", "CX-3", "BT-50", "Verisa", "Premacy"],
    "Subaru": ["Impreza", "Forester", "Legacy", "XV", "Outback", "Levorg", "Exiga"],
    "Mitsubishi": ["Outlander", "Pajero", "RVR", "Mirage", "Lancer", "Canter", "Delica"],
    "Suzuki": ["Swift", "Jimny", "Vitara", "Alto", "Escudo", "Every", "Baleno", "Ignis"],
    "Lexus": ["RX", "NX", "IS", "ES", "LX", "UX", "CT", "GS"],
    "Daihatsu": ["Mira", "Move", "Tanto", "Cast", "Rocky", "Thor", "Boon"],
    "Isuzu": ["D-Max", "MU-X", "Elf"],
    "BMW": ["X1", "X3", "X5", "320i", "520i", "118i", "116i", "X4"],
    "Mercedes-Benz": ["C200", "E300", "GLC", "GLE", "A180", "CLA", "GLA"],
    "Audi": ["A3", "A4", "Q3", "Q5", "Q7", "A6", "Q2"],
    "Volkswagen": ["Golf", "Tiguan", "Polo", "Passat", "T-Roc", "Jetta"],
    "Peugeot": ["208", "3008", "2008", "508"],
}

FUEL_TYPES = ["Petrol", "Diesel", "Hybrid", "Electric"]
TRANSMISSIONS = ["Automatic", "Manual", "CVT"]
BODY_TYPES = ["Sedan", "SUV", "Hatchback", "Wagon", "Van", "Pickup"]


def _random_engine_cc(body_type: str) -> int:
    if body_type in ("SUV", "Pickup", "Van"):
        return random.choice([2000, 2500, 2800, 3000, 3500, 4000])
    if body_type == "Sedan":
        return random.choice([1300, 1500, 1800, 2000, 2500])
    return random.choice([660, 1000, 1200, 1500, 1800])


def _estimate_price_jpy(make: str, model: str, year: int, mileage: int, engine_cc: int) -> float:
    base = 800_000
    year_factor = (year - 2017) * 120_000
    mileage_factor = max(0, (120_000 - mileage) * 3)
    engine_factor = engine_cc * 80
    brand_factor = {"Toyota": 200_000, "Subaru": 150_000, "Honda": 120_000}.get(make, 80_000)
    noise = random.randint(-100_000, 150_000)
    return max(450_000, base + year_factor + mileage_factor + engine_factor + brand_factor + noise)


def _make_listing(make: str, model: str, year: int, index: int) -> CarListingData:
    mileage = random.randint(5_000, 180_000)
    body_type = random.choice(BODY_TYPES)
    engine_cc = _random_engine_cc(body_type)
    fuel_type = random.choice(FUEL_TYPES)
    transmission = random.choice(TRANSMISSIONS)
    platform = random.choice(PLATFORMS)
    price_jpy = _estimate_price_jpy(make, model, year, mileage, engine_cc)
    listing_id = f"JPN-{index + 1:05d}"

    return CarListingData(
        source_platform=platform,
        listing_id=listing_id,
        title=f"{make} {model} {year}",
        make=make,
        model=model,
        year=year,
        mileage_km=mileage,
        engine_cc=engine_cc,
        fuel_type=fuel_type,
        transmission=transmission,
        body_type=body_type,
        price_jpy=price_jpy,
        price_usd=jpy_to_usd(price_jpy),
        location="Japan",
        listing_url=f"https://example.com/{listing_id}",
    )


def generate_sample_listings(n: int = 600, full_coverage: bool = True) -> list[CarListingData]:
    """Generate sample listings. With full_coverage=True, every make/model/year combo is included."""
    listings: list[CarListingData] = []
    current_year = datetime.now().year
    index = 0

    if full_coverage:
        for make, models in MAKES_MODELS.items():
            for model in models:
                for year in range(settings.min_year, settings.max_year + 1):
                    listings.append(_make_listing(make, model, year, index))
                    index += 1

    while len(listings) < n:
        make = random.choice(list(MAKES_MODELS.keys()))
        model = random.choice(MAKES_MODELS[make])
        year = random.randint(settings.min_year, settings.max_year)
        listings.append(_make_listing(make, model, year, index))
        index += 1

    return listings


def generate_local_market_prices(listings: list[CarListingData]) -> pd.DataFrame:
    """Estimate Kenyan local market prices (typically 30-80% higher than import cost)."""
    rows = []
    for listing in listings:
        if not listing.make or not listing.model or not listing.year:
            continue
        import_estimate_usd = (listing.price_usd or 0) + 1200  # rough landed cost proxy
        import_kes = import_estimate_usd * settings.usd_to_kes
        markup = random.uniform(1.25, 1.85)
        avg = import_kes * markup
        rows.append(
            {
                "make": listing.make,
                "model": listing.model,
                "year": listing.year,
                "avg_price_kes": round(avg, 0),
                "min_price_kes": round(avg * 0.9, 0),
                "max_price_kes": round(avg * 1.15, 0),
                "source": "Kenya Market Estimate",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["make", "model", "year"])


def save_sample_csv(listings: list[CarListingData], path=None) -> str:
    settings.sample_data_dir.mkdir(parents=True, exist_ok=True)
    path = path or settings.sample_data_dir / "sample_listings.csv"
    df = pd.DataFrame([item.to_dict() for item in listings])
    df["scraped_at"] = datetime.utcnow() - timedelta(days=random.randint(0, 30))
    df.to_csv(path, index=False)
    return str(path)

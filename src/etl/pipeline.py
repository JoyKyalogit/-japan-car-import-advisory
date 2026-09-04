import logging
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import CarListing, LocalMarketPrice, init_db
from src.etl.cleaner import DataCleaner
from src.scrapers.base import CarListingData

logger = logging.getLogger(__name__)


def save_listings_to_db(session: Session, listings: Iterable[CarListingData | dict]) -> int:
    count = 0
    for item in listings:
        data = item.to_dict() if isinstance(item, CarListingData) else item
        record = CarListing(**{k: v for k, v in data.items() if hasattr(CarListing, k)})
        session.add(record)
        count += 1
    session.commit()
    return count


def load_listings_from_db(session: Session) -> pd.DataFrame:
    rows = session.query(CarListing).all()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([{c.name: getattr(r, c.name) for c in CarListing.__table__.columns} for r in rows])


def save_local_prices_to_db(session: Session, df: pd.DataFrame) -> int:
    count = 0
    for _, row in df.iterrows():
        if pd.isna(row.get("year")):
            continue
        record = LocalMarketPrice(
            make=row.get("make"),
            model=row.get("model"),
            year=int(row.get("year")),
            avg_price_kes=float(row.get("avg_price_kes")),
            min_price_kes=float(row.get("min_price_kes", row.get("avg_price_kes"))),
            max_price_kes=float(row.get("max_price_kes", row.get("avg_price_kes"))),
            source=row.get("source", "Kenya Market"),
        )
        session.add(record)
        count += 1
    session.commit()
    return count


class ETLPipeline:
    def __init__(self) -> None:
        self.cleaner = DataCleaner()
        init_db()

    def run(self, listings: list[CarListingData | dict], local_prices_df: pd.DataFrame | None = None) -> pd.DataFrame:
        from src.database.models import get_session

        df = pd.DataFrame(
            [item.to_dict() if isinstance(item, CarListingData) else item for item in listings]
        )
        cleaned = self.cleaner.clean_dataframe(df)
        self.cleaner.save_cleaned(cleaned)

        session = get_session()
        try:
            save_listings_to_db(session, cleaned.to_dict("records"))
            if local_prices_df is not None and not local_prices_df.empty:
                save_local_prices_to_db(session, local_prices_df)
        finally:
            session.close()

        return cleaned

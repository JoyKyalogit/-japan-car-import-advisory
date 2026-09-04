from datetime import datetime
from pathlib import Path
import shutil

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import PROJECT_ROOT, settings


class Base(DeclarativeBase):
    pass


class CarListing(Base):
    __tablename__ = "car_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_platform = Column(String(50), nullable=False, index=True)
    listing_id = Column(String(100))
    title = Column(String(300))
    make = Column(String(80), index=True)
    model = Column(String(120), index=True)
    year = Column(Integer, index=True)
    mileage_km = Column(Integer)
    engine_cc = Column(Integer)
    fuel_type = Column(String(30))
    transmission = Column(String(30))
    body_type = Column(String(50))
    price_jpy = Column(Float)
    price_usd = Column(Float)
    cf_price_usd = Column(Float)
    destination_port = Column(String(80))
    currency = Column(String(10), default="JPY")
    location = Column(String(100))
    listing_url = Column(Text)
    image_url = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_cleaned = Column(Integer, default=0)


class LocalMarketPrice(Base):
    __tablename__ = "local_market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    make = Column(String(80), index=True)
    model = Column(String(120), index=True)
    year = Column(Integer, index=True)
    avg_price_kes = Column(Float)
    min_price_kes = Column(Float)
    max_price_kes = Column(Float)
    source = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow)


class ImportCostEstimate(Base):
    __tablename__ = "import_cost_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_listing_id = Column(Integer)
    purchase_price_usd = Column(Float)
    shipping_usd = Column(Float)
    insurance_usd = Column(Float)
    cif_usd = Column(Float)
    import_duty_kes = Column(Float)
    excise_duty_kes = Column(Float)
    vat_kes = Column(Float)
    rdl_kes = Column(Float)
    idf_kes = Column(Float)
    port_charges_kes = Column(Float)
    clearing_fees_kes = Column(Float)
    registration_kes = Column(Float)
    other_charges_kes = Column(Float)
    total_import_kes = Column(Float)
    local_market_kes = Column(Float)
    potential_savings_kes = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, echo=False, connect_args=connect_args)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def _seed_demo_sqlite_if_needed() -> None:
    """Copy bundled demo DB when the runtime SQLite file is missing or empty."""
    if not settings.database_url.startswith("sqlite"):
        return

    db_path = Path(settings.database_url.replace("sqlite:///", "", 1))
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path

    demo_path = settings.data_dir / "demo" / "japan_cars.db"
    if not demo_path.exists():
        return

    needs_seed = not db_path.exists() or db_path.stat().st_size == 0
    if not needs_seed and db_path.exists():
        try:
            engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
            )
            with engine.connect() as conn:
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='car_listings'")
                ).fetchone()
                if tables:
                    count = conn.execute(text("SELECT COUNT(*) FROM car_listings")).scalar() or 0
                    needs_seed = count == 0
                else:
                    needs_seed = True
            engine.dispose()
        except Exception:
            needs_seed = True

    if needs_seed:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(demo_path, db_path)


def init_db():
    _seed_demo_sqlite_if_needed()
    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_columns(engine)
    return engine


def _ensure_columns(engine) -> None:
    """Add new columns to existing SQLite databases when models evolve."""
    if not settings.database_url.startswith("sqlite"):
        return

    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "car_listings" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("car_listings")}
    migrations = {
        "cf_price_usd": "FLOAT",
        "destination_port": "VARCHAR(80)",
    }
    with engine.begin() as conn:
        for column, col_type in migrations.items():
            if column not in existing:
                conn.execute(text(f"ALTER TABLE car_listings ADD COLUMN {column} {col_type}"))

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'japan_cars.db'}"
    usd_to_kes: float = 130.0
    jpy_to_usd: float = 0.0067
    scraper_delay_seconds: float = 4.0
    scraper_max_pages: int = 5
    scraper_max_pages_per_make: int = 8
    scraper_scrape_all_makes: bool = True
    scraper_use_sample_data: bool = True
    scraper_clear_db: bool = True
    scraper_clear_listings: bool = True
    scraper_clear_local_prices: bool = False
    scraper_refresh_local_prices: bool = True
    scraper_make_pause_seconds: float = 10.0
    scraper_block_cooldown_seconds: float = 180.0
    scraper_page_retries: int = 4
    scraper_use_real_local_prices: bool = True
    local_scraper_max_pages_per_make: int = 0
    local_scraper_sources: str = "cheki,jiji,autochek"
    local_scraper_makes: str = (
        "toyota,nissan,honda,mazda,mitsubishi,subaru,suzuki,bmw,mercedes,audi,"
        "volkswagen,ford,range-rover,jeep,lexus,hyundai,kia,isuzu,daihatsu,volvo,peugeot"
    )
    scrape_filter_year_range: bool = True
    model_path: str = str(PROJECT_ROOT / "models" / "price_predictor.joblib")
    min_year: int = 2018
    max_year: int = 2026
    use_live_exchange_rate: bool = True

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def cleaned_data_dir(self) -> Path:
        return self.data_dir / "cleaned"

    @property
    def sample_data_dir(self) -> Path:
        return self.data_dir / "sample"


settings = Settings()

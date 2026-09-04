import logging
import re

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class CarFromJapanScraper(BaseScraper):
    platform_name = "Car From Japan"
    base_url = "https://carfromjapan.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/vehicle/search/year-from/2018/page/{page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".vehicle-item, .car-list-item, .product, .listing-card")

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, .vehicle-title, .title")
                price_el = card.select_one(".price, .vehicle-price, [class*='Price']")
                link_el = card.select_one("a[href*='/vehicle/'], a[href*='/car/']")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")

                spec_text = card.get_text(" ", strip=True)
                mileage = parse_mileage(spec_text)

                listing_url = link_el["href"] if link_el else None
                if listing_url and listing_url.startswith("/"):
                    listing_url = f"{self.base_url}{listing_url}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=listing_url.split("/")[-1] if listing_url else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=listing_url,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("CarFromJapan parse error: %s", exc)

        return listings

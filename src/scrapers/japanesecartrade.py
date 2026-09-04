import logging

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, CarListingData
from src.utils.helpers import jpy_to_usd, normalize_make_model, parse_mileage, parse_price, parse_year

logger = logging.getLogger(__name__)


class JapaneseCarTradeScraper(BaseScraper):
    platform_name = "JapaneseCarTrade"
    base_url = "https://www.japanesecartrade.com"

    def build_search_url(self, page: int = 1) -> str:
        return f"{self.base_url}/used-cars?year_from=2018&page={page}"

    def parse_listing_page(self, soup: BeautifulSoup) -> list[CarListingData]:
        listings: list[CarListingData] = []
        cards = soup.select(".car-listing, .vehicle-box, .product-listing, .list-item")

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, .car-title, .title")
                price_el = card.select_one(".price, .car-price")

                title = title_el.get_text(strip=True) if title_el else None
                make, model = normalize_make_model(title or "")
                price_jpy = parse_price(price_el.get_text() if price_el else "")
                year = parse_year(title or "")
                mileage = parse_mileage(card.get_text())

                link_el = card.select_one("a[href]")
                link = link_el["href"] if link_el else None
                if link and link.startswith("/"):
                    link = f"{self.base_url}{link}"

                if not title or not price_jpy:
                    continue

                listings.append(
                    CarListingData(
                        source_platform=self.platform_name,
                        listing_id=link.split("/")[-1] if link else None,
                        title=title,
                        make=make,
                        model=model,
                        year=year,
                        mileage_km=mileage,
                        price_jpy=price_jpy,
                        price_usd=jpy_to_usd(price_jpy),
                        listing_url=link,
                        location="Japan",
                    )
                )
            except Exception as exc:
                logger.debug("JCT parse error: %s", exc)

        return listings

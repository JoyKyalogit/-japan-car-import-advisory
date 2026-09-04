from dataclasses import dataclass, field
from typing import Any


@dataclass
class LocalListingData:
    source_platform: str
    title: str
    make: str | None = None
    model: str | None = None
    year: int | None = None
    price_kes: float | None = None
    fuel_type: str | None = None
    condition: str | None = None
    listing_url: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_platform": self.source_platform,
            "title": self.title,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "price_kes": self.price_kes,
            "fuel_type": self.fuel_type,
            "condition": self.condition,
            "listing_url": self.listing_url,
        }

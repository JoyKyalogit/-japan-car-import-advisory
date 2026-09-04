"""API request/response schemas."""

from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    purchase_price_usd: float = Field(ge=500)
    engine_cc: int = Field(default=1500, ge=660, le=5000)
    fuel_type: str = "Petrol"
    body_type: str = "Sedan"
    local_market_kes: float | None = None
    shipping_usd: float | None = None
    cf_price_usd: float | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=2018, le=2026)


class PredictRequest(BaseModel):
    make: str
    model: str
    year: int = Field(ge=2018, le=2026)
    mileage_km: int = Field(ge=0)
    engine_cc: int = Field(ge=660)
    fuel_type: str = "Petrol"
    transmission: str = "Automatic"
    body_type: str = "Sedan"


class CostBreakdownResponse(BaseModel):
    purchase_price_usd: float
    shipping_usd: float
    insurance_usd: float
    cif_usd: float
    cf_price_usd: float | None = None
    customs_value_kes: float | None = None
    valuation_method: str | None = None
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    rdl_kes: float
    idf_kes: float
    port_charges_kes: float
    clearing_fees_kes: float
    registration_kes: float
    other_charges_kes: float
    total_import_kes: float
    usd_to_kes: float | None = None
    local_market_kes: float | None = None
    potential_savings_kes: float | None = None
    purchase_price_kes: float
    kra_taxes_kes: float

"""Full import cost calculator for Kenya using live FX, C&F prices, and published fee schedules."""

from dataclasses import dataclass, asdict

from src.calculator.kenya_fees import (
    clearing_fees_kes,
    ntsa_registration_kes,
    other_charges_kes,
    port_charges_kes,
)
from src.calculator.kra_taxes import calculate_kra_taxes
from src.services.exchange_rate import get_usd_to_kes


@dataclass
class ImportCostBreakdown:
    purchase_price_usd: float
    shipping_usd: float
    insurance_usd: float
    cif_usd: float
    cf_price_usd: float | None
    customs_value_kes: float
    valuation_method: str
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
    usd_to_kes: float
    local_market_kes: float | None = None
    potential_savings_kes: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def estimate_shipping(body_type: str = "Sedan") -> float:
    """Fallback RoRo shipping when BE FORWARD C&F price is unavailable."""
    rates = {
        "Sedan": 950,
        "Hatchback": 900,
        "SUV": 1100,
        "Wagon": 980,
        "Van": 1200,
        "Pickup": 1300,
        "Minivan": 1050,
        "Coupe": 980,
    }
    return rates.get(body_type or "Sedan", 1000)


def estimate_insurance(fob_usd: float) -> float:
    return round(fob_usd * 0.015, 2)


def _resolve_cif(
    purchase_price_usd: float,
    cf_price_usd: float | None,
    body_type: str,
    shipping_usd: float | None,
) -> tuple[float, float, float, float | None]:
    if cf_price_usd and cf_price_usd >= purchase_price_usd:
        shipping = round(max(cf_price_usd - purchase_price_usd, 0), 2)
        return cf_price_usd, shipping, 0.0, cf_price_usd

    shipping = shipping_usd if shipping_usd is not None else estimate_shipping(body_type)
    insurance = estimate_insurance(purchase_price_usd)
    cif_usd = purchase_price_usd + shipping + insurance
    return cif_usd, shipping, insurance, None


def calculate_import_cost(
    purchase_price_usd: float,
    engine_cc: int = 1500,
    fuel_type: str = "Petrol",
    body_type: str = "Sedan",
    local_market_kes: float | None = None,
    shipping_usd: float | None = None,
    cf_price_usd: float | None = None,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
) -> ImportCostBreakdown:
    cif_usd, shipping, insurance, cf_used = _resolve_cif(
        purchase_price_usd, cf_price_usd, body_type, shipping_usd
    )
    usd_to_kes = get_usd_to_kes()

    kra = calculate_kra_taxes(
        cif_usd,
        engine_cc=engine_cc,
        fuel_type=fuel_type,
        make=make,
        model=model,
        year=year,
    )
    port, port_source = port_charges_kes(body_type)
    clearing, clearing_source = clearing_fees_kes(cif_usd)
    registration, registration_source = ntsa_registration_kes(engine_cc)
    other, other_source = other_charges_kes()

    total_kes = (
        cif_usd * usd_to_kes
        + kra.total_tax_kes
        + port
        + clearing
        + registration
        + other
    )

    savings = None
    if local_market_kes is not None:
        savings = round(local_market_kes - total_kes, 2)

    return ImportCostBreakdown(
        purchase_price_usd=round(purchase_price_usd, 2),
        shipping_usd=round(shipping, 2),
        insurance_usd=insurance,
        cif_usd=round(cif_usd, 2),
        cf_price_usd=cf_used,
        customs_value_kes=kra.customs_value_kes,
        valuation_method=kra.valuation_method,
        import_duty_kes=kra.import_duty_kes,
        excise_duty_kes=kra.excise_duty_kes,
        vat_kes=kra.vat_kes,
        rdl_kes=kra.rdl_kes,
        idf_kes=kra.idf_kes,
        port_charges_kes=port,
        clearing_fees_kes=clearing,
        registration_kes=registration,
        other_charges_kes=other,
        total_import_kes=round(total_kes, 2),
        usd_to_kes=usd_to_kes,
        local_market_kes=local_market_kes,
        potential_savings_kes=savings,
    )

"""Kenya Revenue Authority (KRA) import duty calculations."""

from dataclasses import dataclass

from src.calculator.crsp import customs_value_kes
from src.services.exchange_rate import get_usd_to_kes

# Statutory rates (Finance Act / EAC CET schedules for passenger vehicles).
IMPORT_DUTY_RATE = 0.25
VAT_RATE = 0.16
RDL_RATE = 0.02
IDF_RATE = 0.0225
IDF_MINIMUM_KES = 5_000


@dataclass
class KRABreakdown:
    cif_kes: float
    customs_value_kes: float
    valuation_method: str
    import_duty_kes: float
    excise_duty_kes: float
    vat_kes: float
    rdl_kes: float
    idf_kes: float
    total_tax_kes: float


def get_excise_rate(engine_cc: int, fuel_type: str = "Petrol") -> float:
    fuel = (fuel_type or "Petrol").lower()
    if "electric" in fuel:
        return 0.10
    if "hybrid" in fuel and engine_cc <= 1500:
        return 0.15
    if engine_cc <= 1500:
        return 0.20
    if engine_cc <= 3000:
        return 0.25
    return 0.35


def calculate_kra_taxes(
    cif_usd: float,
    engine_cc: int = 1500,
    fuel_type: str = "Petrol",
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
) -> KRABreakdown:
    """Calculate KRA taxes using customs value (CIF or depreciated CRSP, whichever is higher)."""
    usd_to_kes = get_usd_to_kes()
    cif_kes = cif_usd * usd_to_kes
    customs_kes, method = customs_value_kes(
        cif_kes, make=make, model=model, year=year, engine_cc=engine_cc
    )

    import_duty = customs_kes * IMPORT_DUTY_RATE
    excise_rate = get_excise_rate(engine_cc, fuel_type)
    excise_duty = customs_kes * excise_rate
    vat_base = customs_kes + import_duty + excise_duty
    vat = vat_base * VAT_RATE
    rdl = customs_kes * RDL_RATE
    idf = max(customs_kes * IDF_RATE, IDF_MINIMUM_KES)

    total = import_duty + excise_duty + vat + rdl + idf

    return KRABreakdown(
        cif_kes=round(cif_kes, 2),
        customs_value_kes=round(customs_kes, 2),
        valuation_method=method,
        import_duty_kes=round(import_duty, 2),
        excise_duty_kes=round(excise_duty, 2),
        vat_kes=round(vat, 2),
        rdl_kes=round(rdl, 2),
        idf_kes=round(idf, 2),
        total_tax_kes=round(total, 2),
    )

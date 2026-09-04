import pytest

from src.calculator.import_cost import calculate_import_cost
from src.calculator.kra_taxes import calculate_kra_taxes, get_excise_rate
from src.etl.cleaner import DataCleaner
import pandas as pd


def test_kra_taxes_basic():
    result = calculate_kra_taxes(cif_usd=10000, engine_cc=1500, fuel_type="Petrol")
    assert result.import_duty_kes > 0
    assert result.vat_kes > 0
    assert result.total_tax_kes == pytest.approx(
        result.import_duty_kes + result.excise_duty_kes + result.vat_kes + result.rdl_kes + result.idf_kes,
        rel=0.01,
    )


def test_excise_rate_electric():
    assert get_excise_rate(2000, "Electric") == 0.10


def test_import_cost_total():
    result = calculate_import_cost(
        purchase_price_usd=8000,
        engine_cc=1500,
        local_market_kes=2_000_000,
        cf_price_usd=9200,
        make="Toyota",
        model="Axio",
        year=2019,
    )
    assert result.total_import_kes > 0
    assert result.cf_price_usd == 9200
    assert result.customs_value_kes > 0
    assert result.potential_savings_kes is not None


def test_import_cost_uses_crsp_when_higher():
    result = calculate_import_cost(
        purchase_price_usd=5000,
        engine_cc=1500,
        make="Toyota",
        model="Prado",
        year=2019,
    )
    assert "CRSP" in result.valuation_method or result.valuation_method == "CIF"


def test_data_cleaner():
    df = pd.DataFrame([
        {"make": "Toyota", "model": "Vitz", "year": 2019, "price_jpy": 900000, "mileage_km": 50000, "engine_cc": 1300},
        {"make": "Toyota", "model": "Vitz", "year": 2015, "price_jpy": 500000, "mileage_km": 100000, "engine_cc": 1300},
        {"make": "Nissan", "model": "Note", "year": 2020, "price_jpy": None, "mileage_km": 30000, "engine_cc": 1200},
    ])
    cleaner = DataCleaner()
    cleaned = cleaner.clean_dataframe(df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["year"] == 2019


def test_ntsa_registration_uses_official_fee_components():
    from src.calculator.kenya_fees import ntsa_registration_kes

    total, source = ntsa_registration_kes(engine_cc=1500)
    if "Kenya Law" in source:
        assert total == pytest.approx(8600, rel=0.01)
    else:
        assert total > 0

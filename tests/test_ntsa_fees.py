"""Tests for NTSA fee PDF parsing."""

from src.scrapers.ntsa_fees import (
    DEFAULT_INSPECTION_TIERS,
    DEFAULT_PLATE_FEES,
    DEFAULT_REGISTRATION_TIERS,
    _parse_inspection_tiers,
    _parse_plate_fees,
    _parse_registration_tiers,
)


def test_parse_registration_tiers_from_traffic_rules_excerpt():
    text = """
    (a) not exceeding 1,000 1,700
    cc.........................
    (b) exceeding 1,000 cc 2,100
    but not exceeding 1,200
    cc....................
    (h) exceeding 3,000 cc 8,300
    """
    tiers = _parse_registration_tiers(text)
    assert tiers[0]["fee_kes"] == 1700
    assert tiers[-1]["fee_kes"] == 8300


def test_parse_inspection_tiers_from_traffic_rules_excerpt():
    text = """
    Inspection of three- 2,600
    wheelers and vehicles
    with engine capacities of
    up to 3,000 cc................
    Inspection of vehicles 3,900
    with engine capacities of
    over 3,000 cc..................
    """
    tiers = _parse_inspection_tiers(text)
    assert tiers[0]["fee_kes"] == 2600
    assert tiers[1]["fee_kes"] == 3900


def test_parse_plate_fees_from_registration_rules_excerpt():
    text = """
    Fee for an application for or replacement of front and 3,000
    Fee for an application for or replacement of third 700
    """
    fees = _parse_plate_fees(text)
    assert fees["registration_plates_pair_kes"] == 3000
    assert fees["third_license_kes"] == 700


def test_defaults_match_official_schedule():
    assert DEFAULT_REGISTRATION_TIERS[0]["fee_kes"] == 1700
    assert DEFAULT_INSPECTION_TIERS[0]["fee_kes"] == 2600
    assert DEFAULT_PLATE_FEES["registration_plates_pair_kes"] == 3000

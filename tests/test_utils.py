import pytest
from decimal import Decimal
from scripts.utils import uakt_to_akt, akt_to_uakt, safe_get, parse_escrow_amount

def test_uakt_to_akt():
    assert uakt_to_akt(1_000_000) == Decimal('1.0')
    assert uakt_to_akt(500_000) == Decimal('0.5')
    assert uakt_to_akt(0) == Decimal('0')
    assert uakt_to_akt(1_123_456) == Decimal('1.1')  # Tests rounding

def test_akt_to_uakt():
    assert akt_to_uakt(Decimal('1.0')) == 1_000_000
    assert akt_to_uakt(Decimal('0.5')) == 500_000
    assert akt_to_uakt(Decimal('0')) == 0
    assert akt_to_uakt(Decimal('1.123456')) == 1_123_456  # Tests precision

def test_amount_conversion_roundtrip():
    amounts = [
        Decimal('1.5'),
        Decimal('0.5'),
        Decimal('1.123456'),
        Decimal('10.0')
    ]
    for amount in amounts:
        assert uakt_to_akt(akt_to_uakt(amount)) == amount.quantize(Decimal('0.1'))

def test_parse_escrow_amount():
    # Test valid amounts
    assert parse_escrow_amount({"funds": {"denom": "uakt", "amount": "1000000"}}) == 1000000
    assert parse_escrow_amount({"funds": {"denom": "uakt", "amount": "1.23e6"}}) == 1230000
    
    # Test invalid amounts
    assert parse_escrow_amount({"funds": {"denom": "btc", "amount": "1000000"}}) is None
    assert parse_escrow_amount({"funds": {"amount": "1000000"}}) is None
    assert parse_escrow_amount({"funds": {"denom": "uakt"}}) is None
    assert parse_escrow_amount({}) is None

def test_safe_get():
    test_dict = {'a': {'b': {'c': 1}}}
    assert safe_get(test_dict, 'a', 'b', 'c') == 1
    assert safe_get(test_dict, 'x', default=None) is None
    assert safe_get(test_dict, 'a', 'b', 'x', default=5) == 5

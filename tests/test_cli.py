import pytest
from argparse import ArgumentTypeError
from decimal import Decimal
from scripts.cli import validate_akt_amount

def test_validate_akt_amount_valid():
    assert validate_akt_amount("1.0") == Decimal("1.0")
    assert validate_akt_amount("0.5") == Decimal("0.5")
    assert validate_akt_amount("1.123456") == Decimal("1.123456")

def test_validate_akt_amount_invalid():
    with pytest.raises(ArgumentTypeError):
        validate_akt_amount("invalid")
    
    with pytest.raises(ArgumentTypeError):
        validate_akt_amount("-1.0")
    
    with pytest.raises(ArgumentTypeError):
        validate_akt_amount("0")

def test_validate_akt_amount_zero():
    with pytest.raises(ArgumentTypeError):
        validate_akt_amount("0.0")

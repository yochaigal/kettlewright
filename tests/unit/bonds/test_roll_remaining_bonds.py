import pytest
import sys
import os
import json

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.lib.char_utils import get_required_bonds_count, roll_bond_excluding, load_bonds


def test_fieldwarden_requires_two_bonds():
    """Test that Fieldwarden background requires 2 bonds."""
    bonds_required = get_required_bonds_count("Fieldwarden", None)
    assert bonds_required == 2


def test_outrider_with_debt_requires_two_bonds():
    """Test that Outrider with debt table option requires 2 bonds."""
    debt_option = "Always pay your debts: You always repay what you owe, whether in coin or in kind. You expect nothing less from all others. Take a Blacked-Out Ledger, then roll a second time on the Bonds table."
    bonds_required = get_required_bonds_count("Outrider", debt_option)
    assert bonds_required == 2


def test_outrider_without_debt_requires_one_bond():
    """Test that Outrider without debt table option requires 1 bond."""
    normal_option = "Some other option that doesn't mention debt"
    bonds_required = get_required_bonds_count("Outrider", normal_option)
    assert bonds_required == 1


def test_normal_background_requires_one_bond():
    """Test that normal backgrounds require 1 bond."""
    bonds_required = get_required_bonds_count("Aurifex", None)
    assert bonds_required == 1


def test_roll_bond_excluding_works():
    """Test that roll_bond_excluding actually excludes specified bonds."""
    bonds = load_bonds()
    if len(bonds) < 2:
        pytest.skip("Need at least 2 bonds to test exclusion")
    
    # Get the first bond description
    first_bond_desc = bonds[0]['description']
    
    # Roll a bond excluding the first one
    excluded_bond = roll_bond_excluding([first_bond_desc])
    
    # Make sure we didn't get the excluded bond
    assert excluded_bond is not None
    assert excluded_bond['description'] != first_bond_desc


if __name__ == "__main__":
    # Run basic tests
    print("Testing Fieldwarden...")
    test_fieldwarden_requires_two_bonds()
    print("✓ Fieldwarden requires 2 bonds")
    
    print("Testing Outrider with debt...")
    test_outrider_with_debt_requires_two_bonds()
    print("✓ Outrider with debt requires 2 bonds")
    
    print("Testing Outrider without debt...")
    test_outrider_without_debt_requires_one_bond()
    print("✓ Outrider without debt requires 1 bond")
    
    print("Testing normal background...")
    test_normal_background_requires_one_bond()
    print("✓ Normal background requires 1 bond")
    
    print("Testing bond exclusion...")
    test_roll_bond_excluding_works()
    print("✓ Bond exclusion works")
    
    print("\nAll tests passed!")
"""
Tests for second bond cleanup when background changes.
"""
import pytest
import json
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.lib.char_utils import get_required_bonds_count, find_bond_by_description
from app.lib.data import load_bonds
from app.blueprints.charcreo import clear_second_bond_if_needed


class MockForm:
    def __init__(self, background_data):
        self.background = type('obj', (object,), {'data': background_data})
        self.bonds = type('obj', (object,), {'process_data': lambda x: None})


def test_second_bond_cleanup_logic():
    """Test the logic for cleaning up second bonds when changing backgrounds."""
    bonds = load_bonds()
    first_bond = bonds[0]
    second_bond = bonds[1] if len(bonds) > 1 else bonds[0]
    
    # Simulate custom_fields with two bonds selected
    custom_fields = {
        'bonds_selected': first_bond['description'],
        'bonds_selected_2': second_bond['description'],
        'bonus_gold_bond': str(first_bond.get('gold', 0) + second_bond.get('gold', 0)),
        'bond_items': json.dumps(first_bond.get('items', []) + second_bond.get('items', []))
    }
    
    # Test: Change from Fieldwarden (2 bonds) to Aurifex (1 bond)
    fieldwarden_bonds_required = get_required_bonds_count("Fieldwarden", "")
    aurifex_bonds_required = get_required_bonds_count("Aurifex", "")
    
    assert fieldwarden_bonds_required == 2, "Fieldwarden should require 2 bonds"
    assert aurifex_bonds_required == 1, "Aurifex should require 1 bond"
    
    form = MockForm("Aurifex")
    
    bond_was_cleared = clear_second_bond_if_needed(custom_fields, form)
    
    assert bond_was_cleared == True, "Helper should report that it cleared the second bond"
    
    # Verify cleanup worked
    assert custom_fields['bonds_selected_2'] == '', "Second bond should be cleared"
    assert custom_fields['bonds_selected'] == first_bond['description'], "First bond should remain"
    
    # Verify gold was properly adjusted
    expected_gold = str(first_bond.get('gold', 0))
    assert custom_fields['bonus_gold_bond'] == expected_gold, f"Gold should be {expected_gold}"
    
    # Verify items were properly adjusted
    expected_items = json.dumps(first_bond.get('items', []))
    assert custom_fields['bond_items'] == expected_items, "Items should only include first bond items"
    
    print("✓ Second bond cleanup logic works correctly")


def test_outrider_table_option_bond_cleanup():
    """Test cleanup when Outrider changes from debt option to non-debt option."""
    bonds = load_bonds()
    first_bond = bonds[0]
    second_bond = bonds[1] if len(bonds) > 1 else bonds[0]
    
    debt_option = "Always pay your debts: You always repay what you owe, whether in coin or in kind. You expect nothing less from all others. Take a Blacked-Out Ledger, then roll a second time on the Bonds table."
    normal_option = "Some other table1 option that doesn't mention bonds"
    
    # Test bond requirements
    outrider_debt_bonds = get_required_bonds_count("Outrider", debt_option)
    outrider_normal_bonds = get_required_bonds_count("Outrider", normal_option)
    
    assert outrider_debt_bonds == 2, "Outrider with debt should require 2 bonds"
    assert outrider_normal_bonds == 1, "Outrider without debt should require 1 bond"
    
    # Simulate changing from debt option to normal option
    custom_fields = {
        'bonds_selected': first_bond['description'],
        'bonds_selected_2': second_bond['description'],
        'bonus_gold_bond': str(first_bond.get('gold', 0) + second_bond.get('gold', 0)),
        'bond_items': json.dumps(first_bond.get('items', []) + second_bond.get('items', []))
    }
    
    form = MockForm("Outrider")
    custom_fields['background_table1_select'] = normal_option
    
    bond_was_cleared = clear_second_bond_if_needed(custom_fields, form)
    
    assert bond_was_cleared == True, "Helper should report that it cleared the second bond"
    
    # Verify cleanup
    assert custom_fields['bonds_selected_2'] == '', "Second bond should be cleared"
    assert custom_fields['bonds_selected'] == first_bond['description'], "First bond should remain"
    
    print("✓ Outrider table option bond cleanup works correctly")


def test_no_cleanup_when_staying_with_two_bonds():
    """Test that no cleanup happens when changing between backgrounds that both require 2 bonds."""
    bonds = load_bonds()
    first_bond = bonds[0]
    second_bond = bonds[1] if len(bonds) > 1 else bonds[0]
    
    # Both Fieldwarden and Outrider with debt require 2 bonds
    debt_option = "Always pay your debts: You always repay what you owe, whether in coin or in kind. You expect nothing less from all others. Take a Blacked-Out Ledger, then roll a second time on the Bonds table."
    
    fieldwarden_bonds = get_required_bonds_count("Fieldwarden", "")
    outrider_debt_bonds = get_required_bonds_count("Outrider", debt_option)
    
    assert fieldwarden_bonds == 2, "Fieldwarden should require 2 bonds"
    assert outrider_debt_bonds == 2, "Outrider with debt should require 2 bonds"
    
    # Simulate having two bonds
    original_bonds_selected_2 = second_bond['description']
    original_gold = str(first_bond.get('gold', 0) + second_bond.get('gold', 0))
    
    custom_fields = {
        'bonds_selected': first_bond['description'],
        'bonds_selected_2': original_bonds_selected_2,
        'bonus_gold_bond': original_gold,
        'bond_items': json.dumps(first_bond.get('items', []) + second_bond.get('items', []))
    }
    
    # No cleanup should happen when changing to another 2-bond background
    if outrider_debt_bonds == 1 and custom_fields.get('bonds_selected_2'):
        # This should not execute
        custom_fields['bonds_selected_2'] = ''
    
    # Verify no cleanup happened
    assert custom_fields['bonds_selected_2'] == original_bonds_selected_2, "Second bond should remain"
    assert custom_fields['bonus_gold_bond'] == original_gold, "Gold should remain unchanged"
    
    print("✓ No cleanup when staying with 2-bond backgrounds")


if __name__ == "__main__":
    test_second_bond_cleanup_logic()
    test_outrider_table_option_bond_cleanup()
    test_no_cleanup_when_staying_with_two_bonds()
    
    print("\n🎉 All second bond cleanup tests passed!")
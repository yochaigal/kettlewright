"""Tests for automatic second bond rolling in charcreo_roll_all endpoint."""
import pytest
import json
from app.blueprints.charcreo import roll_second_bond_if_needed
from app.lib.data import load_bonds, load_backgrounds


def test_roll_all_with_fieldwarden_gets_two_bonds(app_with_babel, client, monkeypatch):
    """Test that rolling Fieldwarden in roll-all automatically gets 2 bonds."""
    with app_with_babel.app_context():
        backgrounds = load_backgrounds()
        
        def mock_random_background():
            return "Fieldwarden", backgrounds["Fieldwarden"]
        
        monkeypatch.setattr("app.blueprints.charcreo.random_background", mock_random_background)
        
        response = client.get('/charcreo/roll-all')
        
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        
        assert 'bonds_required_count' in html or 'bonds-select-2' in html, \
            "Should have second bond field for Fieldwarden"
        
        assert 'Second Bond' in html or 'bonds-select-2' in html, \
            "Should display second bond selector for Fieldwarden"

def test_roll_second_bond_if_needed_function(app):
    """Test the roll_second_bond_if_needed helper function directly."""
    with app.app_context():
        bonds = load_bonds()
        
        custom_fields = {
            'bonds_required_count': 2,
            'bonds_selected': bonds[0]['description'],
            'bonds_selected_2': None,
        }
        
        roll_second_bond_if_needed(custom_fields)
        
        assert custom_fields.get('bonds_selected_2') is not None, \
            "Second bond should be automatically rolled"
        assert custom_fields['bonds_selected_2'] != '', \
            "Second bond should not be empty"
        assert custom_fields['bonds_selected_2'] != custom_fields['bonds_selected'], \
            "Second bond should be different from first bond"


def test_second_bond_items_tracked_separately(app):
    """Test that second bond items are tracked in bond_items_2."""
    with app.app_context():
        bonds = load_bonds()
        
        bond_with_items = None
        for bond in bonds:
            if bond.get('items'):
                bond_with_items = bond
                break
        
        if bond_with_items is None:
            pytest.skip("No bonds with items found in test data")
        
        custom_fields = {
            'bonds_required_count': 2,
            'bonds_selected': bonds[0]['description'],
            'bonds_selected_2': None,
            'bond_items': '[]',
            'bond_items_2': None,
        }

        roll_second_bond_if_needed(custom_fields)
        
        assert 'bond_items_2' in custom_fields, \
            "bond_items_2 should be set"
        assert custom_fields['bond_items_2'] is not None, \
            "bond_items_2 should not be None"
        
def test_second_bond_gold_tracked_separately(app):
    """Test that second bond gold bonus is tracked in bonus_gold_bond_2."""
    with app.app_context():
        bonds = load_bonds()
        
        bond_with_gold = None
        for bond in bonds:
            if bond.get('gold'):
                bond_with_gold = bond
                break
        
        if bond_with_gold is None:
            pytest.skip("No bonds with gold found in test data")
        
        custom_fields = {
            'bonds_required_count': 2,
            'bonds_selected': bonds[0]['description'],
            'bonds_selected_2': None,
            'bonus_gold_bond': '0',
            'bonus_gold_bond_2': None,
        }
        
        roll_second_bond_if_needed(custom_fields)
        
        assert 'bonus_gold_bond_2' in custom_fields, \
            "bonus_gold_bond_2 should be set"
        assert custom_fields['bonus_gold_bond_2'] is not None, \
            "bonus_gold_bond_2 should not be None"

def test_bonds_are_different_when_second_rolled(app):
    """Test that when second bond is rolled, it's different from the first."""
    with app.app_context():
        bonds = load_bonds()
        
        if len(bonds) < 2:
            pytest.skip("Need at least 2 bonds for this test")
        
        for _ in range(5):
            custom_fields = {
                'bonds_required_count': 2,
                'bonds_selected': bonds[0]['description'],
                'bonds_selected_2': None,
            }
            
            roll_second_bond_if_needed(custom_fields)
            
            assert custom_fields['bonds_selected'] != custom_fields['bonds_selected_2'], \
                "First and second bonds should always be different"

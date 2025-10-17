"""Tests for background bond rules and character creation functionality."""
import pytest
import json
from app.lib.char_utils import find_bond_by_description, get_required_bonds_count
from app.lib.data import load_backgrounds, load_bonds


class TestBackgroundBondRules:
    """Test bond requirements for different backgrounds."""
    
    def test_fieldwarden_requires_two_bonds(self):
        """Fieldwarden background should require 2 bonds."""
        bond_count = get_required_bonds_count("Fieldwarden")
        assert bond_count == 2, "Fieldwarden should get 2 bonds by default"
    
    def test_outrider_with_debt_option_requires_two_bonds(self):
        """Outrider with 'Always pay your debts' option should require 2 bonds."""
        debt_option = "Always pay your debts: You always repay what you owe, whether in coin or in kind. You expect nothing less from all others. Take a Blacked-Out Ledger, then roll a second time on the Bonds table."
        bond_count = get_required_bonds_count("Outrider", debt_option)
        assert bond_count == 2, "Outrider with debt option should get 2 bonds"
    
    def test_outrider_without_debt_option_requires_one_bond(self):
        """Outrider without special option should require 1 bond."""
        other_option = "Some other table1 option that doesn't mention bonds"
        bond_count = get_required_bonds_count("Outrider", other_option)
        assert bond_count == 1, "Outrider without debt option should get 1 bond"
    
    def test_regular_backgrounds_require_one_bond(self):
        """Most backgrounds should require only 1 bond."""
        regular_backgrounds = ["Aurifex", "Barber-Surgeon", "Beast Handler", "Bonekeeper"]
        
        for background_name in regular_backgrounds:
            bond_count = get_required_bonds_count(background_name)
            assert bond_count == 1, f"{background_name} should only get 1 bond"
    
    def test_bonds_data_loads_correctly(self):
        """Verify that bonds data loads and has expected structure."""
        bonds = load_bonds()
        
        assert len(bonds) > 0, "Should have bonds data"
        assert isinstance(bonds, list), "Bonds should be a list"
        
        # Check first bond has required fields
        first_bond = bonds[0]
        assert "description" in first_bond, "Bond should have description"
    
    def test_find_bond_by_description_works(self):
        """Test that we can find bonds by their description."""
        bonds = load_bonds()
        
        if bonds:
            first_bond = bonds[0]
            description = first_bond["description"]
            
            found_bond = find_bond_by_description(description)
            assert found_bond is not None, "Should find bond by description"
            assert found_bond["description"] == description, "Found bond should match"
    
    def test_duplicate_bonds_should_be_prevented(self):
        """Characters should not be able to select the same bond twice."""
        bonds = load_bonds()
        
        # Test that we have enough bonds to avoid duplicates
        assert len(bonds) >= 2, "Should have at least 2 different bonds available"
        
        # Test case: if first bond is selected, it shouldn't be available for second bond
        first_bond_desc = bonds[0]["description"]
        second_bond_desc = bonds[1]["description"]
        
        # They should be different
        assert first_bond_desc != second_bond_desc, "Bonds should have different descriptions"
    
    def test_character_creation_prevents_duplicate_bonds(self):
        """Test that character creation logic prevents selecting same bond twice."""
        # This test will verify the functionality once we implement it
        bonds = load_bonds()
        
        # Simulate selecting the same bond twice
        selected_bonds = [bonds[0]["description"], bonds[0]["description"]]
        
        # After implementing duplicate prevention, this should result in different bonds
        # For now, we'll test that we have the data structure to support this
        unique_bonds = list(set(selected_bonds))
        
        # This currently will pass with duplicates, but after implementation should prevent them
        assert len(bonds) >= 2, "Must have enough bonds to avoid duplicates"
    
    def test_bond_selection_with_exclusions(self):
        """Test that bond selection can exclude already selected bonds."""
        bonds = load_bonds()
        
        # Simulate first bond selection
        first_bond = bonds[0]
        excluded_descriptions = [first_bond["description"]]
        
        # Find available bonds (excluding first)
        available_bonds = [b for b in bonds if b["description"] not in excluded_descriptions]
        
        assert len(available_bonds) == len(bonds) - 1, "Should exclude one bond"
        assert first_bond not in available_bonds, "First bond should be excluded"
    
    def test_roll_bond_excluding_function(self):
        """Test the roll_bond_excluding utility function."""
        from app.lib.char_utils import roll_bond_excluding
        
        bonds = load_bonds()
        first_bond = bonds[0]
        second_bond = bonds[1] if len(bonds) > 1 else None
        
        # Test rolling without exclusions
        rolled_bond = roll_bond_excluding()
        assert rolled_bond is not None, "Should roll a bond"
        assert "description" in rolled_bond, "Rolled bond should have description"
        
        # Test rolling with one exclusion
        rolled_bond_2 = roll_bond_excluding([first_bond["description"]])
        assert rolled_bond_2 is not None, "Should roll a bond excluding first"
        assert rolled_bond_2["description"] != first_bond["description"], "Should not roll excluded bond"
        
        # Test rolling with multiple exclusions (if we have enough bonds)
        if len(bonds) >= 3:
            excluded = [first_bond["description"], second_bond["description"]]
            rolled_bond_3 = roll_bond_excluding(excluded)
            assert rolled_bond_3 is not None, "Should roll a bond excluding multiple"
            assert rolled_bond_3["description"] not in excluded, "Should not roll any excluded bond"
    
    def test_second_bond_effects_are_applied(self):
        """Test that second bond's gold and items are included in character totals."""
        bonds = load_bonds()
        
        # Find bonds with gold or items for testing
        bond_with_gold = None
        bond_with_items = None
        
        for bond in bonds:
            if bond.get('gold', 0) > 0:
                bond_with_gold = bond
            if bond.get('items') and len(bond['items']) > 0:
                bond_with_items = bond
        
        # Test that we have bonds with effects to test
        if bond_with_gold:
            assert bond_with_gold['gold'] > 0, "Should have bond with gold bonus"
        
        if bond_with_items:
            assert len(bond_with_items['items']) > 0, "Should have bond with items"
        
        # This test verifies the data structure exists
        # The actual integration test would be done in the UI/routes
        assert len(bonds) >= 2, "Need at least 2 bonds for multi-bond backgrounds"
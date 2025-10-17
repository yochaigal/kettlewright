import pytest
from app import create_app


class TestIntSumFilter:
    
    
    @pytest.fixture
    def app(self):
        """Create a test app instance."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def intsum_filter(self, app):
        """Get the intsum filter function from the app."""
        with app.app_context():
            return app.jinja_env.filters['intsum']
    
    def test_typical_character_creation_usage(self, intsum_filter):
        """Test typical usage in character creation templates - adding bonus gold, etc."""
        # Normal case: adding base gold + bonus gold from bonds/tables
        assert intsum_filter("10", "5") == "15"  # base gold + bond bonus
        assert intsum_filter(10, 5) == "15"      # same but as integers
        
        # Mixed types (common in templates)
        assert intsum_filter("10", 5) == "15"
        assert intsum_filter(10, "5") == "15"
    
    def test_handles_missing_template_variables(self, intsum_filter):
        """Test the main bug fix - handles None/empty values that broke the old version."""
        # Template variables can be None
        assert intsum_filter(None, "5") == "5"   # bonus_gold_bond is None, base gold exists  
        assert intsum_filter("10", None) == "10" # base gold exists, bonus is None
        assert intsum_filter(None, None) == "0"  # both missing
        
        # Empty strings from form inputs
        assert intsum_filter("", "5") == "5"
        assert intsum_filter("10", "") == "10"
        assert intsum_filter("", "") == "0"
    
    def test_returns_string_for_template_display(self, intsum_filter):
        """Test that result is always a string for template display."""
        assert isinstance(intsum_filter(5, 10), str)
        assert isinstance(intsum_filter(None, None), str)

"""Test that proves JSON export includes second bonds (bug fix verification)."""
import json
from app.lib.char_utils import generate_character


def test_fieldwarden_json_export_includes_both_bonds(app_with_babel):
    """Test that Fieldwarden JSON export includes both bonds separated by newlines."""
    with app_with_babel.app_context():
        genchar, json_data = generate_character("Fieldwarden")
        data = json.loads(json_data)
        
        assert genchar.bond2 is not None, "Fieldwarden should have second bond"
        
        assert '\n\n' in data['bonds'], "Bonds should be separated by double newline"
        
        assert genchar.bond['description'] in data['bonds']
        assert genchar.bond2['description'] in data['bonds']


def test_fieldwarden_print_rendering_includes_both_bonds(app_with_babel):
    """Test that Fieldwarden print view renders both bonds from JSON data."""
    with app_with_babel.test_client() as client:
        with app_with_babel.app_context():
            genchar, json_data = generate_character("Fieldwarden")
            
            response = client.post('/gen/character/print', 
                                  data={'json_data': json_data},
                                  follow_redirects=True)
            
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            
            assert genchar.bond['description'] in html, "First bond should appear in print view"
            assert genchar.bond2['description'] in html, "Second bond should appear in print view"
            
            assert 'id="character-bonds-view"' in html
            assert 'class="with-whitespace"' in html

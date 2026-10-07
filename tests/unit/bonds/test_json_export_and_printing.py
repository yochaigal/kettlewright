"""Test that proves JSON export includes second bonds (bug fix verification)."""
import html as html_lib
import json
import re
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
            
            bonds_view = re.search(r'<div id="character-bonds-view"[^>]*>(.*?)</div>', html, re.S)
            assert bonds_view is not None, "Print view should have a bonds section"
            paragraphs = [html_lib.unescape(p).strip()
                          for p in re.findall(r'<p>(.*?)</p>', bonds_view.group(1), re.S)]
            assert paragraphs == [genchar.bond['description'], genchar.bond2['description']], \
                "Each bond should render as its own paragraph"

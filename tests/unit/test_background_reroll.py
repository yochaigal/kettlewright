"""Exercise background changes with the form actually rendered by Roll All."""
from html.parser import HTMLParser
import json

import pytest

from app.blueprints.charcreo import get_custom_fields
from app.lib.data import load_backgrounds


ITEM_FIELDS = ('bond_items', 'bond_items_2', 't1_items', 't2_items', 'bkg_items')


class FormValues(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.select = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name'):
            self.values[attrs['name']] = attrs.get('value', '')
        elif tag == 'select':
            self.select = attrs.get('name')
        elif tag == 'option' and self.select and 'selected' in attrs:
            self.values[self.select] = attrs.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'select':
            self.select = None


@pytest.mark.parametrize('endpoint', ['roll-background', 'select-background'])
@pytest.mark.parametrize('background,legacy', [
    ('Aurifex', False),
    ('Aurifex', True),
    ('Fieldwarden', False),
])
def test_background_change_after_roll_all(app_with_babel, monkeypatch, endpoint, background, legacy):
    with app_with_babel.test_request_context('/'):
        backgrounds = load_backgrounds()
    monkeypatch.setattr('app.blueprints.charcreo.random_background',
                        lambda: (background, backgrounds[background]))
    client = app_with_babel.test_client()
    rolled = client.get('/charcreo/roll-all')
    assert rolled.status_code == 200
    original = FormValues(rolled.get_data(as_text=True)).values
    posted = original.copy()
    target = 'Outrider' if background == 'Aurifex' else background
    monkeypatch.setattr('app.blueprints.charcreo.random_background',
                        lambda: (target, backgrounds[target]))
    if endpoint == 'select-background':
        posted['background'] = target
    if legacy:
        # An already open form rendered before the fix.
        posted['bond_items_2'] = 'None'

    response = client.post(f'/charcreo/{endpoint}', data=posted)
    assert response.status_code == 200
    assert response.headers['HX-Trigger-After-Settle'] == 'background-changed'
    updated = FormValues(response.get_data(as_text=True)).values
    assert updated['background'] == target
    assert json.loads(updated['bkg_items']) == backgrounds[target]['starting_gear']
    for field in ITEM_FIELDS:
        assert isinstance(json.loads(original[field]), list)
    assert updated['t1_items'] == updated['t2_items'] == '[]'
    names = [item['name'] for item in json.loads(updated['items'])]
    for field in ('bond_items', 'bond_items_2'):
        for item in json.loads(original[field]):
            assert item['name'] in names


@pytest.mark.parametrize('value', [None, '', 'None', '[]', '[{"name": "Keepsake"}]'])
def test_item_fields_use_json_arrays(value):
    fields = get_custom_fields(dict.fromkeys(ITEM_FIELDS, value))
    expected = [] if value in (None, '', 'None') else json.loads(value)
    for field in ITEM_FIELDS:
        assert json.loads(fields[field]) == expected


def test_missing_item_fields_use_empty_arrays():
    fields = get_custom_fields({})
    for field in ITEM_FIELDS:
        assert json.loads(fields[field]) == []

import json

from app.lib import Inventory, Market
from app.models import Character, db


def test_library_consumable_preserves_charges_on_creation(app_context):
    character = Character(name='Test', background='Test', items='[]',
                          containers='[{"id":0,"name":"Main","slots":10}]')
    db.session.add(character)
    db.session.commit()
    market = Market()
    equipment = {'name': 'Test wand', 'tags': ['charges'], 'charges': 3}
    market.market.append(equipment)
    item = market.buy([equipment['name']])[0]
    Inventory(character).create_item(item['name'], ','.join(item['tags']), item['uses'],
                                     item['charges'], item['max_charges'], 0, item['description'])
    saved = json.loads(character.items)[0]
    assert saved['charges'] == equipment['charges']
    assert saved['max_charges'] == equipment['charges']
    assert saved['tags'] == equipment['tags']


def test_unusual_marketplace_tags_are_available_when_reopening_editor(app_with_babel):
    from flask import render_template
    with app_with_babel.test_request_context():
        item = Market().buy(['Trap'])[0]
        assert 'd6 STR' in item['tags']
        html = render_template('partial/modal/extra_item_tags.html', item=item, mode='edit')
        assert 'data-tag="d6 STR"' in html
        assert 'selected' in html

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

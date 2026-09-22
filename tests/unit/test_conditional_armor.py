import json

import pytest
from app.models import Character, db
from app.lib import Inventory


@pytest.mark.parametrize('name, active, location, expected', [
    ('Sloth-Tarp', None, 0, 0), ('Sloth-Tarp', True, 0, 1),
    ('Sloth-Tarp', False, 0, 0), ('Shield', None, 0, 1),
    ('Shield', False, 0, 0), ('Shield', True, 1, 0),
])
def test_conditional_armor_consistent(name, active, location, expected):
    item = dict(id='test', name=name, tags=['1 Armor'], location=location)
    if active is not None:
        item['armor_active'] = active
    character = Character(items=json.dumps([item]), containers=json.dumps([
        dict(id=0, name='Main', slots=10), dict(id=1, name='Bag', slots=10)]))
    assert character.armorValue() == expected
    assert Inventory(character).compute_armor() == expected


def test_armor_toggle_survives_item_save_and_export(app_context):
    character = Character(name='Test', background='Test', items='[]',
                          containers='[{"id": 0, "name": "Main", "slots": 10}]')
    db.session.add(character)
    inventory = Inventory(character)
    item = inventory.create_item('Sloth-Tarp', '1 Armor', '', '', '', 0, '', armor_active=True)
    assert character.armorValue() == 1
    assert json.loads(character.toJSON())['items'][0]['armor_active'] is True
    inventory.update_item(item['id'], 'Sloth-Tarp', '1 Armor', '', '', '', 0, '', armor_active=False)
    assert character.armorValue() == 0

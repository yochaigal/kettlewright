import json

import pytest
from werkzeug.exceptions import BadRequest
from app.models import Character, Party, db
from app.lib import Inventory


@pytest.fixture
def inventories(app_context):
    containers = json.dumps([dict(id=0, name='Main', slots=10), dict(id=3, name='Stash', slots=2)])
    character = Character(id=1, name='Test', background='Test', party_id=1,
                          items=json.dumps([dict(id='item', name='Shield', location=3, tags=['1 Armor'], armor_active=False)]), containers=containers)
    party = Party(id=1, name='Party', members='[1]', items='[]', containers=containers)
    db.session.add_all([character, party])
    db.session.commit()
    return character, party


def test_round_trip_preserves_item_and_uses_destination_container(inventories):
    character, party = inventories
    Inventory(character).move_item_to_party('item', 3)
    assert json.loads(character.items) == []
    item = json.loads(party.items)[0]
    assert item['location'] == 3
    assert item['armor_active'] is False
    Inventory(party).move_item_to_user('item', character.id)
    assert json.loads(party.items) == []
    assert json.loads(character.items)[0]['location'] == 0


@pytest.mark.parametrize('destination', [99, -1])
def test_missing_container_does_not_remove_item(inventories, destination):
    character, party = inventories
    with pytest.raises(BadRequest):
        Inventory(character).move_item_to_party('item', destination)
    assert len(json.loads(character.items)) == 1
    assert party.items == '[]'


def test_full_container_does_not_remove_item(inventories):
    character, party = inventories
    party.items = json.dumps([dict(id='full', name='Large', location=3, tags=['bulky'])])
    with pytest.raises(BadRequest):
        Inventory(character).move_item_to_party('item', 3)
    assert len(json.loads(character.items)) == 1
    assert len(json.loads(party.items)) == 1


def test_cannot_transfer_to_nonmember(inventories):
    character, party = inventories
    Inventory(character).move_item_to_party('item')
    party.members = '[]'
    with pytest.raises(BadRequest):
        Inventory(party).move_item_to_user('item', character.id)
    assert len(json.loads(party.items)) == 1

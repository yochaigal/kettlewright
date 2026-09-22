import json

import pytest
from app.models import Character, User, db
from app.lib.character_json import normalize_inventory


def test_export_import_round_trip(app_with_babel):
    with app_with_babel.app_context():
        owner = User(username='json-user')
        db.session.add(owner)
        db.session.flush()
        owner_id = owner.id
        source = Character(name='JSON Hero', background='Custom', custom_name='Alias',
            custom_background='Explorer', strength=3, strength_max=12, dexterity=7, dexterity_max=14,
            willpower=8, willpower_max=11, hp=0, hp_max=6, gold=0, deprived=True, panicked=True, dead=True,
            custom_image=True, image_url='https://example.org/portrait.png', traits='Quiet',
            notes='Note', bonds='Bond', scars='Scar', omens='Omen', description='Description',
            items='[{"id": "shield", "name": "Shield", "tags": ["1 Armor"], "location": 0, "armor_active": false}]',
            containers='[{"id": 0, "name": "Main", "slots": 10}]', owner=owner_id)
        db.session.add(source)
        db.session.commit()
        db.session.expire(source)
        data = json.loads(source.toJSON())
        assert 'owner' not in data and 'id' not in data
        form = {key: json.dumps(value) if isinstance(value, (list, bool)) else value
                for key, value in data.items() if value is not None}
        client = app_with_babel.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(owner_id)
        response = client.post('/new_from_json/', data=form)
        assert response.status_code == 302
        imported = Character.query.order_by(Character.id.desc()).first()
        assert imported.id != source.id
        assert json.loads(imported.toJSON()) == data


def test_missing_legacy_inventory_is_normalized():
    items, containers = normalize_inventory('', '')
    assert items == []
    assert containers[0]['id'] == 0


@pytest.mark.parametrize('items, containers', [
    ('{}', '[]'), ('[]', '{}'), ('not json', '[]'),
    ('[{"name":"Item","location":99}]', '[]'),
    ('[{"name":"Item","tags":"bulky"}]', '[]'),
    ('[]', '[{"id":0,"name":"Bag","slots":-1}]'),
])
def test_invalid_inventory_is_rejected(items, containers):
    with pytest.raises(ValueError):
        normalize_inventory(items, containers)


def test_legacy_integer_item_ids_and_nested_items():
    items, containers = normalize_inventory('[{"id":4,"name":"Rope"}]',
        '[{"id":"0","name":"Main","slots":"10","items":[{"name":"duplicate"}]}]')
    assert items[0]['id'] == '4'
    assert items[0]['location'] == 0
    assert 'items' not in containers[0]

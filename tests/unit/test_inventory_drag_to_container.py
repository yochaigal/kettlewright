"""Dragging an item onto another container tab, or onto a carried cart (#415)."""
import json

import pytest

from app.models import Character, Companion, Party, User, db

MOVE_URL = '/charedit/inplace-inventory/player/hero/move'
CONTAINERS = [
    {'id': 0, 'name': 'Main', 'slots': 10},
    {'id': 1, 'name': 'Satchel', 'slots': 2},
    {'id': 2, 'name': 'Cart', 'slots': 4, 'carried_by': 0},
    {'id': 9, 'name': 'Ground', 'slots': 10, 'on_the_ground': True},
]
ITEMS = [
    {'id': 'rope', 'name': 'Rope', 'tags': [], 'location': 0, 'slot': 0},
    {'id': 'torch', 'name': 'Torch', 'tags': [], 'location': 0, 'slot': 3},
    {'id': 'tent', 'name': 'Tent', 'tags': ['bulky'], 'location': 0, 'slot': 4},
    {'id': 'coin', 'name': 'Lucky coin', 'tags': ['petty'], 'location': 0},
    {'id': 'fatigue', 'name': 'Fatigue', 'tags': [], 'location': 0, 'editable': False},
    {'id': 'cart_0', 'name': 'Carrying Cart', 'tags': [], 'location': 0, 'editable': False, 'carrying': 2},
    {'id': 'map', 'name': 'Map', 'tags': [], 'location': 1, 'slot': 1},
    {'id': 'pebble', 'name': 'Pebble', 'tags': [], 'location': 9},
]


@pytest.fixture
def sheet(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='player'), User(id=2, username='outsider')])
        db.session.add(Character(id=1, owner=1, owner_username='player', name='Hero', url_name='hero',
                                 background='Test', containers=json.dumps(CONTAINERS), items=json.dumps(ITEMS)))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return app_with_babel, client


def stored(app):
    with app.app_context():
        return {item['id']: item for item in json.loads(db.session.get(Character, 1).items)}


def move(client, item_id, container):
    return client.post(MOVE_URL, data={'item_id': item_id, 'container': container, 'inventory_context': 'sheet'})


def test_drop_on_container_tab_moves_item_and_keeps_other_slots(sheet):
    app, client = sheet
    response = move(client, 'torch', 1)
    assert response.status_code == 200
    assert response.headers['HX-Trigger'] == 'refresh-stats'
    page = response.get_data(as_text=True)
    assert 'aria-label="Main"' in page  # Still showing the container the item came from.
    items = stored(app)
    assert items['torch']['location'] == 1
    assert items['torch']['slot'] == 0  # First free slot in the Satchel; the Map keeps slot 1.
    assert items['map']['slot'] == 1
    assert (items['rope']['slot'], items['tent']['slot']) == (0, 4)


def test_drop_on_a_carried_cart_moves_item_into_the_cart(sheet):
    app, client = sheet
    assert move(client, 'tent', 2).status_code == 200
    assert stored(app)['tent']['location'] == 2


def test_petty_items_fit_anywhere(sheet):
    app, client = sheet
    assert move(client, 'map', 0).status_code == 200
    assert move(client, 'rope', 1).status_code == 200
    assert move(client, 'coin', 1).status_code == 200  # Satchel is now full, but petty takes no slot.
    assert stored(app)['coin']['location'] == 1


def test_full_container_refuses_and_nothing_changes(sheet):
    app, client = sheet
    before = stored(app)
    assert move(client, 'tent', 1).status_code == 400  # Bulky needs 2, the Satchel has 1 free.
    assert stored(app) == before


@pytest.mark.parametrize('item_id, container, status', [
    ('fatigue', 1, 400),   # Fatigue stays where it is.
    ('cart_0', 1, 400),    # So do the slots the cart takes up.
    ('torch', 9, 400),     # The ground has its own Drop item flow...
    ('pebble', 0, 400),    # ...and Pick up.
    ('torch', 7, 404),
    ('torch', 'x', 404),
    ('ghost', 1, 404),
])
def test_moves_that_are_refused(sheet, item_id, container, status):
    app, client = sheet
    before = stored(app)
    assert move(client, item_id, container).status_code == status
    assert stored(app) == before


def test_drop_on_own_container_changes_nothing(sheet):
    app, client = sheet
    before = stored(app)
    assert move(client, 'torch', 0).status_code == 200
    assert stored(app) == before


def test_only_editors_can_move(sheet):
    app, _ = sheet
    outsider = app.test_client()
    with outsider.session_transaction() as session:
        session['_user_id'] = '2'
    assert move(outsider, 'torch', 1).status_code == 403
    assert stored(app)['torch']['location'] == 0


def test_slot_moves_still_work(sheet):
    app, client = sheet
    response = client.post(MOVE_URL, data={'item_id': 'torch', 'slot': 1, 'inventory_context': 'sheet'})
    assert response.status_code == 200
    assert stored(app)['torch'] == dict(ITEMS[1], slot=1)


def test_sheet_marks_drop_targets(sheet):
    _, client = sheet
    page = client.get('/charedit/inventory-select-container/player/hero/0',
                      query_string={'inventory_context': 'sheet'}).get_data(as_text=True)
    assert 'data-drop-container="1" data-drop-name="Satchel" data-free="1"' in page
    assert 'data-drop-container="2" data-drop-name="Cart" data-free="4"' in page  # Its tab and its carried slot.
    assert page.count('data-drop-container="2"') == 2
    assert 'data-drop-container="0"' not in page  # Not the container being shown...
    assert 'data-drop-container="9"' not in page  # ...nor the ground.
    assert 'data-move-item="torch" data-move-across="1"' in page
    assert 'data-move-item="tent" data-move-across="2"' in page
    assert 'data-move-item="fatigue" data-move-across' not in page
    assert 'There is not enough room in that container.' in page


def test_visitors_get_no_drop_targets(sheet):
    app, _ = sheet
    page = app.test_client().get('/charedit/inventory-select-container/player/hero/0',
                                 query_string={'inventory_context': 'sheet'}).get_data(as_text=True)
    assert 'data-drop-container' not in page


def test_hireling_items_can_change_containers(sheet):
    app, client = sheet
    with app.app_context():
        db.session.add(Party(id=1, owner=1, owner_username='player', name='Party', party_url='party',
                             members='[]', items='[]', containers='[{"id":0,"name":"Main","slots":10}]'))
        db.session.add(Companion(id=1, kind='hireling', party_id=1, name='Bodyguard',
                                 containers=json.dumps(CONTAINERS[:2]),
                                 items=json.dumps([dict(ITEMS[0]), dict(ITEMS[2])])))
        db.session.commit()
    url = '/companions/1/inventory/move'
    assert client.post(url, data={'item_id': 'tent', 'container': 1}).status_code == 200  # Bulky fills the Satchel.
    assert client.post(url, data={'item_id': 'rope', 'container': 1}).status_code == 400
    assert client.post(url, data={'item_id': 'tent', 'container': 0}).status_code == 200
    assert client.post(url, data={'item_id': 'rope', 'container': 1}).status_code == 200
    with app.app_context():
        locations = {item['id']: item['location'] for item in json.loads(db.session.get(Companion, 1).items)}
    assert locations == {'rope': 1, 'tent': 0}

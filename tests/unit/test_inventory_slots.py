import json

import pytest

from app.lib.inventory import Inventory
from app.lib.inventory_slots import arrange_slots
from app.models import Character, User, db


def item(id, tags=None, **kwargs):
    return dict(id=id, name=id, tags=tags or [], location=0, description='', **kwargs)


def test_bulky_spans_two_and_petty_takes_no_slot():
    layout = arrange_slots([item('axe', ['bulky']), item('torch'), item('coin', ['petty'])], 10)
    assert layout['used'] == 3
    assert layout['rows'][0]['span'] == 2
    assert layout['rows'][1]['slot'] == 2
    assert sum(row['span'] for row in layout['rows']) == 10
    assert [entry['id'] for entry in layout['petty']] == ['coin']
    assert len([row for row in layout['rows'] if row['item'] is None]) == 7


def test_saved_positions_survive_alphabetical_order_and_invalid_imports():
    layout = arrange_slots([item('axe', slot=7), item('torch', slot=2), item('bad', slot='oops')], 10)
    assert layout['positions'] == {'axe': 7, 'torch': 2, 'bad': 0}


def test_overloaded_items_remain_visible():
    layout = arrange_slots([item('axe', ['bulky']), item('torch')], 2)
    assert layout['used'] == 3
    assert layout['rows'][-1]['overflow'] is True
    assert len([row for row in layout['rows'] if row['item']]) == 2


@pytest.fixture
def inventory_sheet(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='other')])
        db.session.add(Character(id=1, owner=1, name='Hero', url_name='hero', background='Test',
            items=json.dumps([item('axe', ['bulky']), item('torch', ['uses'], uses=3), item('coin', ['petty'])]),
            containers=json.dumps([dict(id=0, name='Main', slots=10)])))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return app_with_babel, client


MOVE = '/charedit/inplace-inventory/owner/hero/move'


def test_move_persists_and_preserves_items(inventory_sheet):
    app, client = inventory_sheet
    response = client.post(MOVE, data={'item_id': 'axe', 'slot': '6', 'inventory_context': 'sheet'})
    assert response.status_code == 200
    assert b'grid-row: 4; grid-column: 1 / span 2' in response.data
    assert b'Edit inventory' not in response.data
    assert response.headers['HX-Trigger'] == 'refresh-stats'
    with app.app_context():
        character = db.session.get(Character, 1)
        items = {item['id']: item for item in json.loads(character.items)}
        assert items['axe']['slot'] == 6
        assert items['torch']['uses'] == 3
        assert len(items) == 3
        assert character.occupiedMainSlots() == 3
        inventory = Inventory(character)
        inventory.decorate()
        assert inventory.slot_layout()['positions']['axe'] == 6
    response = client.post(MOVE, data={'item_id': 'torch', 'slot': '6'})
    assert response.status_code == 200
    with app.app_context():
        layout = Inventory(db.session.get(Character, 1)).slot_layout()
        assert layout['positions']['torch'] == 6
        assert layout['positions']['axe'] not in (5, 6)


@pytest.mark.parametrize('id,slot,code', [('axe', -1, 400), ('axe', 9, 400), ('axe', 'bad', 400), ('coin', 1, 400), ('missing', 1, 404)])
def test_rejected_move_leaves_inventory_intact(inventory_sheet, id, slot, code):
    app, client = inventory_sheet
    with app.app_context():
        before = db.session.get(Character, 1).items
    assert client.post(MOVE, data={'item_id': id, 'slot': slot}).status_code == code
    with app.app_context():
        assert db.session.get(Character, 1).items == before


def test_move_requires_permission_and_csrf(inventory_sheet):
    app, client = inventory_sheet
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert client.post(MOVE, data={'item_id': 'axe', 'slot': 3}).status_code == 403
    with client.session_transaction() as session:
        session.clear()
    assert client.post(MOVE, data={'item_id': 'axe', 'slot': 3}).status_code == 403
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(MOVE, data={'item_id': 'axe', 'slot': 3}).status_code == 400


def test_creation_uses_selected_slot_and_render_stays_inline(inventory_sheet):
    app, client = inventory_sheet
    response = client.post('/charedit/inplace-inventory/owner/hero/item-edit/None/save?mode=create', data={
        'edit_item_container': '0', 'edit_item_name': 'Rope', 'edit_item_tags': '',
        'edit_item_uses': '', 'edit_item_charges': '', 'edit_item_max_charges': '',
        'edit_item_description': '', 'edit_item_slot': '8', 'slot_container': '0', 'inventory_context': 'sheet'})
    assert response.status_code == 200
    assert b'slot-inventory' in response.data
    with app.app_context():
        items = json.loads(db.session.get(Character, 1).items)
        assert next(item for item in items if item['name'] == 'Rope')['slot'] == 8


def test_full_inventory_allows_petty_but_rejects_oversize(inventory_sheet):
    app, _ = inventory_sheet
    with app.app_context():
        character = db.session.get(Character, 1)
        character.containers = json.dumps([dict(id=0, name='Main', slots=3)])
        db.session.commit()
        inventory = Inventory(character)
        assert inventory.create_item('Pin', 'petty', '', '', '', 0, '') is not None
        assert inventory.create_item('Sword', 'bulky', '', '', '', 0, '') is None


def test_public_inventory_has_slots_without_mutation_controls(inventory_sheet):
    _, client = inventory_sheet
    with client.session_transaction() as session:
        session.clear()
    response = client.get('/charedit/inventory-select-container/owner/hero/0?inventory_context=sheet')
    assert response.status_code == 200
    assert b'slot-bulky' in response.data
    assert b'data-move-item=' not in response.data
    assert b'hx-post=' not in response.data


def test_new_item_does_not_reorder_existing_legacy_items(inventory_sheet):
    app, client = inventory_sheet
    with app.app_context():
        before = Inventory(db.session.get(Character, 1)).slot_layout()['positions']
    response = client.post('/charedit/inplace-inventory/owner/hero/item-edit/None/save?mode=create', data={
        'edit_item_container': '0', 'edit_item_name': 'AAA first alphabetically', 'edit_item_tags': '',
        'edit_item_uses': '', 'edit_item_charges': '', 'edit_item_max_charges': '',
        'edit_item_description': '', 'edit_item_slot': '8', 'slot_container': '0', 'inventory_context': 'sheet'})
    assert response.status_code == 200
    with app.app_context():
        after = Inventory(db.session.get(Character, 1)).slot_layout()['positions']
        for id, slot in before.items():
            assert after[id] == slot


def test_use_dots_keep_empty_dots_and_only_change_uses(inventory_sheet):
    app, client = inventory_sheet
    path = '/charedit/inplace-inventory/owner/hero/item-edit/torch/uses'
    for value in (2, 0, 3):
        response = client.post(path, data={'uses': value})
        assert response.status_code == 200
        assert response.data.count(b'aria-label="Uses: ') == 3
        with app.app_context():
            inventory = Inventory(db.session.get(Character, 1))
            torch = inventory.get_item('torch')
            assert torch['uses'] == value
            assert torch['max_uses'] == 3
            assert len(json.loads(inventory.character.items)) == 3
    assert client.post(path, data={'uses': 4}).status_code == 400
    assert client.post(path, data={'uses': -1}).status_code == 400
    assert client.post(path, data={'uses': 'bad'}).status_code == 400


def test_tiles_keep_names_separate_from_properties(inventory_sheet):
    _, client = inventory_sheet
    response = client.get('/charedit/inventory-select-container/owner/hero/0?inventory_context=sheet')
    html = response.get_data(as_text=True)
    assert '>axe</button>' in html
    assert 'axe (<i>bulky</i>)' not in html
    assert 'slot-tag' in html
    assert 'slot-use-dot' in html
    assert 'grid-column: 1 / span 2' in html


def test_bulky_aligns_to_a_full_grid_row():
    layout = arrange_slots([item('torch'), item('axe', ['bulky'])], 10)
    assert layout['positions']['torch'] == 0
    assert layout['positions']['axe'] == 2
    assert next(row for row in layout['rows'] if row['slot'] == 1)['item'] is None

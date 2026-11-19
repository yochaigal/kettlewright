"""Background containers (#404) and setting carried containers down (#435)."""
import json
import re

import pytest

from app.lib.inventory import Inventory, starting_containers
from app.models import Character, Companion, User, db
from tests.helpers import login
from tests.unit.test_background_reroll import FormValues


def carts(containers):
    return [c for c in json.loads(containers) if c['name'] == 'Cart']


def reservations(items, container_id):
    return [it for it in json.loads(items) if it.get('carrying') == container_id]


def assert_mountebank_cart(values):
    cart, = carts(values['containers'])
    assert cart['carried_by'] == '0' and cart['load'] == 2
    held = reservations(values['items'], cart['id'])
    # A load of 2 is one bulky tile, not two separate slots.
    assert len(held) == 1 and held[0]['tags'] == ['bulky'] and held[0]['location'] == 0


def test_starting_containers_resolve_carriers_by_name():
    items = []
    built = starting_containers([
        {'name': 'Burial Wagon', 'slots': 6, 'carried_by': 'Donkey', 'load': 2},
        {'name': 'Donkey', 'slots': 4},
        {'name': 'Cart', 'slots': 4, 'carried_by': 'main', 'load': 2},
    ], items)
    wagon, donkey, cart = built
    assert [c['id'] for c in built] == [1, 2, 3]
    assert wagon['carried_by'] == str(donkey['id']) and 'carried_by' not in donkey
    assert cart['carried_by'] == '0'
    assert sorted((it['location'], it['carrying'], it['tags']) for it in items) == [(0, 3, ['bulky']), (2, 1, ['bulky'])]


def test_mountebank_keeps_cart_through_character_creation(app_with_babel):
    with app_with_babel.app_context():
        from app.lib.data import load_backgrounds
        background = load_backgrounds()['Mountebank']
        db.session.add(User(id=1, username='creator'))
        db.session.commit()
    client = login(app_with_babel.test_client(), 1)
    response = client.post('/charcreo/select-background', data={
        'background': 'Mountebank', 'items': '[]', 'containers': '[{"name": "Main", "slots": 10, "id": 0}]'})
    values = FormValues(response.text).values
    assert_mountebank_cart(values)

    # Answering or rolling a background table used to drop the Cart.
    values['background_table1_select'] = background['table1']['options'][0]['description']
    values = FormValues(client.post('/charcreo/bkg-table-select/1', data=values).text).values
    assert_mountebank_cart(values)
    values = FormValues(client.post('/charcreo/bkg-table-roll/2', data=values).text).values
    assert_mountebank_cart(values)
    names = [it['name'] for it in json.loads(values['items'])]
    assert names.count('Rations') == 1 and 'Bandages' in names

    values.update(age='20', name='Ambrose', strength_max='10', dexterity_max='10',
                  willpower_max='10', hp_max='4')
    response = client.post('/charcreo/roll-remaining', data=values)
    values.update(FormValues(response.text).values)
    assert_mountebank_cart(values)

    response = client.post('/charcreo/save', data=values)
    assert response.status_code == 200 and 'HX-Redirect' in response.headers
    with app_with_babel.app_context():
        character = Character.query.one()
        assert_mountebank_cart({'containers': character.containers, 'items': character.items})


def test_random_mountebank_carries_cart(app_with_babel):
    from app.lib.char_utils import generate_character
    with app_with_babel.test_request_context('/'):
        genchar, data = generate_character('Mountebank')
    data = json.loads(data)
    assert_mountebank_cart({'containers': json.dumps(data['containers']), 'items': json.dumps(data['items'])})


@pytest.fixture
def carted(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='stranger')])
        db.session.flush()
        character = Character(owner=1, owner_username='owner', name='Ambrose', url_name='ambrose',
                              background='Mountebank', items='[]', containers=json.dumps([
                                  {'id': 0, 'name': 'Main', 'slots': 10},
                                  {'id': 1, 'name': 'Cart', 'slots': 4}]))
        db.session.add(character)
        db.session.commit()
        inventory = Inventory(character)
        inventory.update_container('1', 'Cart', 4, '0', '2')
        inventory.create_item('Rope', '', None, None, None, 1, '')
        character_id = character.id
    return app_with_babel, character_id


def test_cart_can_be_set_down_and_picked_up(carted):
    app, character_id = carted
    with app.app_context():
        character = db.session.get(Character, character_id)
        inventory = Inventory(character)
        inventory.set_container_down(1, True)
        cart = inventory.get_container(1)
        assert cart['set_down'] and cart['load'] == '2'
        assert reservations(character.items, 1) == []
        assert [it['name'] for it in cart['items']] == ['Rope']
        inventory.decorate()
        assert inventory.get_container(1)['title'].endswith('set down')

        # Editing a cart that is set down keeps it down.
        inventory.update_container('1', 'Big cart', 6, '0', '3')
        assert reservations(character.items, 1) == []
        assert inventory.get_container(1)['set_down']

        inventory.set_container_down(1, False)
        assert 'set_down' not in inventory.get_container(1)
        held = reservations(character.items, 1)
        assert sorted(it['tags'] for it in held) == [[], ['bulky']]
        assert {it['name'] for it in held} == {'Carrying Big cart'}


def test_only_carried_containers_can_be_set_down(carted):
    from werkzeug.exceptions import BadRequest
    app, character_id = carted
    with app.app_context():
        inventory = Inventory(db.session.get(Character, character_id))
        with pytest.raises(BadRequest):
            inventory.set_container_down(0, True)


@pytest.mark.parametrize('context', ['sheet', ''])
def test_set_down_route_on_character_sheet(carted, context):
    app, character_id = carted
    client = login(app.test_client(), 1)
    base = '/charedit/inplace-inventory/owner/ambrose/container-edit/1/set-down'
    response = client.post(base, data={'down': '1', 'inventory_context': context})
    assert response.status_code == 200 and 'Pick up' in response.text
    response = client.post(base, data={'down': '0', 'inventory_context': context})
    assert response.status_code == 200 and 'Set down' in response.text
    with app.app_context():
        held, = reservations(db.session.get(Character, character_id).items, 1)
        assert held['tags'] == ['bulky']
    assert login(app.test_client(), 2).post(base, data={'down': '1'}).status_code == 403


def test_set_down_route_on_companion_sheet(app_with_babel):
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='owner'))
        db.session.flush()
        parent = Character(owner=1, owner_username='owner', name='Owner', url_name='owner',
                           background='Test', items='[]', containers='[]')
        db.session.add(parent)
        db.session.flush()
        donkey = Companion(character_id=parent.id, kind='pet', name='Donkey', items='[]',
                           containers=json.dumps([{'id': 0, 'name': 'Main', 'slots': 4},
                                                  {'id': 1, 'name': 'Wagon', 'slots': 6}]))
        db.session.add(donkey)
        db.session.commit()
        Inventory(donkey).update_container('1', 'Wagon', 6, '0', '2')
        donkey_id = donkey.id
    client = login(app_with_babel.test_client(), 1)
    response = client.post(f'/companions/{donkey_id}/inventory/container-edit/1/set-down', data={'down': '1'})
    assert response.status_code == 200 and 'Pick up' in response.text
    with app_with_babel.app_context():
        assert reservations(db.session.get(Companion, donkey_id).items, 1) == []




def toolbar(page):
    bar = re.search(r'<div class="slot-container-actions".*?</div>', page, re.S)
    return ' '.join(re.sub(r'<[^>]+>', ' ', bar[0]).split()) if bar else None


def test_cart_tab_shows_container_actions_above_items(carted):
    app, character_id = carted
    client = login(app.test_client(), 1)
    select = '/charedit/inventory-select-container/owner/ambrose/1?mode=edit&inventory_context=sheet'
    page = client.get(select).text
    assert toolbar(page) == 'Set down Clear Remove'
    # In Main, the "Carrying Cart" tile offers Remove (the cart), not Set down.
    main = client.get('/charedit/inventory-select-container/owner/ambrose/0?mode=edit&inventory_context=sheet').text
    assert toolbar(main) is None and '/set-down' not in main
    remove, = re.findall(r'<button[^>]*container-edit/1/delete"[^>]*>', main)
    assert 'title="Remove: Cart"' in remove
    assert page.index('slot-container-actions') < page.index('class="inventory-slots"')
    # Set down from the "Carrying Cart" tile in Main keeps Main open; the Cart tab offers Pick up.
    page = client.post('/charedit/inplace-inventory/owner/ambrose/container-edit/1/set-down',
                       data={'down': '1', 'container': '0', 'inventory_context': 'sheet'}).text
    assert re.search(r'inventory-container-title-selected"[^>]*>([^<]*)<', page)[1].startswith('Main')
    assert toolbar(page) is None and 'Pick up' not in page
    assert toolbar(client.get(select).text) == 'Pick up Clear Remove'


def test_clear_keeps_the_container_and_remove_deletes_it(carted):
    app, character_id = carted
    client = login(app.test_client(), 1)
    base = '/charedit/inplace-inventory/owner/ambrose/container-edit/1'
    page = client.post(f'{base}/clear', data={'inventory_context': 'sheet'}).text
    assert 'Rope' not in page and toolbar(page) == 'Set down Clear Remove'
    assert 'disabled' in re.search(r'<button[^>]*/clear"[^>]*>', page)[0]
    with app.app_context():
        character = db.session.get(Character, character_id)
        assert [it['name'] for it in json.loads(character.items)] == ['Carrying Cart']
    client.post(f'{base}/delete', data={'delete-items': '', 'inventory_context': 'sheet'})
    with app.app_context():
        character = db.session.get(Character, character_id)
        assert [c['name'] for c in json.loads(character.containers)] == ['Main']
        assert json.loads(character.items) == []


def test_clear_keeps_load_of_carried_containers(carted):
    app, character_id = carted
    with app.app_context():
        inventory = Inventory(db.session.get(Character, character_id))
        wagon = inventory.add_container('Wagon', 6, '1', '2')
        inventory.clear_container(1)
        assert len(reservations(inventory.character.items, wagon)) == 1

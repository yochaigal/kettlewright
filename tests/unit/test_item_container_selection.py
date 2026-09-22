import json

import pytest
from app.models import User, Character, Party, db


EDIT_URL = '/charedit/inplace-inventory/player/test/item-edit/item'


@pytest.fixture
def editor(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=1, username='player'), User(id=2, username='outsider')])
        containers = '[{"id":0,"name":"Main","slots":10},{"id":3,"name":"Bag","slots":2}]'
        db.session.add(Party(id=1, owner=2, name='Party', members='[1]', items='[]', containers=containers))
        db.session.add(Character(id=1, owner=1, name='Test', url_name='test', background='Test', party_id=1,
                                 containers=containers, items=json.dumps([
                                     dict(id='item', name='Shield', location=3, tags=['1 Armor'], armor_active=False)])))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    data = dict(edit_item_name='Updated shield', edit_item_tags='2 Armor,uses',
                edit_item_uses='2', edit_item_charges='', edit_item_max_charges='',
                edit_item_description='Edited before moving', edit_item_armor_active='on',
                edit_item_container='party:3')
    return app, client, data


def test_editor_has_one_container_selector_with_ownership_labels(editor):
    _, client, _ = editor
    html = client.get(EDIT_URL).get_data(as_text=True)
    assert html.count('name="edit_item_container"') == 1
    assert 'name="party_container"' not in html
    assert 'Party Storage' not in html
    assert 'Main (Personal)' in html
    assert '<option value="party:0">Main (Party)</option>' in html


def test_save_edits_and_transfer_to_selected_party_container(editor):
    app, client, data = editor
    response = client.post(EDIT_URL + '/save', data=data)
    assert response.status_code == 200
    assert response.headers['HX-Trigger'] == 'refresh-stats'
    with app.app_context():
        assert json.loads(db.session.get(Character, 1).items) == []
        item = json.loads(db.session.get(Party, 1).items)[0]
        assert item['id'] == 'item'
        assert item['location'] == 3
        assert item['name'] == data['edit_item_name']
        assert item['description'] == data['edit_item_description']
        assert item['tags'] == ['2 Armor', 'uses']
        assert item['uses'] == 2
        assert item['armor_active'] is True


@pytest.mark.parametrize('failure', ['full', 'missing', 'left', 'collision'])
def test_failed_transfer_leaves_both_inventories_unchanged(editor, failure):
    app, client, data = editor
    with app.app_context():
        party = db.session.get(Party, 1)
        if failure == 'full':
            # Capacity must use the edited bulky tag, not the original item.
            party.items = '[{"id":"other","name":"Rope","location":3,"tags":[]}]'
            data['edit_item_tags'] = 'bulky'
        elif failure == 'missing':
            data['edit_item_container'] = 'party:99'
        elif failure == 'left':
            party.members = '[]'
        else:
            party.items = '[{"id":"item","name":"Other","location":0,"tags":[]}]'
        db.session.commit()
        original_character = db.session.get(Character, 1).items
        original_party = party.items
    response = client.post(EDIT_URL + '/save', data=data)
    assert response.headers['HX-Retarget'] == '#add-edit-item-modal-error-text'
    with app.app_context():
        assert db.session.get(Character, 1).items == original_character
        assert db.session.get(Party, 1).items == original_party


def test_personal_container_save_does_not_transfer(editor):
    app, client, data = editor
    data['edit_item_container'] = '0'
    assert client.post(EDIT_URL + '/save', data=data).status_code == 200
    with app.app_context():
        item = json.loads(db.session.get(Character, 1).items)[0]
        assert item['location'] == 0
        assert item['name'] == data['edit_item_name']
        assert db.session.get(Party, 1).items == '[]'


def test_nonowner_cannot_save_and_transfer(editor):
    app, client, data = editor
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert client.post(EDIT_URL + '/save', data=data).status_code == 403
    with app.app_context():
        assert json.loads(db.session.get(Character, 1).items)[0]['name'] == 'Shield'
        assert db.session.get(Party, 1).items == '[]'


def test_stale_party_membership_hides_party_containers(editor):
    app, client, _ = editor
    with app.app_context():
        db.session.get(Party, 1).members = '[]'
        db.session.commit()
    html = client.get(EDIT_URL).get_data(as_text=True)
    assert 'Main (Personal)' in html
    assert 'value="party:' not in html

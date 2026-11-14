"""Who may read and change a party's shared storage."""
import json

import pytest

from app.models import Character, Party, User, db

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'
ITEM = dict(id='gear', name='Rope', tags=['uses'], uses=3, location=0)
WARDEN, CO_OWNER, MEMBER, OUTSIDER = 1, 2, 3, 4


@pytest.fixture
def storage(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=i, username=f'user{i}') for i in range(1, 5)])
        db.session.add(Party(id=1, owner=WARDEN, owner_username='user1', name='Expedition', party_url='expedition',
                             members='[1, 2]', subowners=f'[{CO_OWNER}]', items=json.dumps([ITEM]), containers=CONTAINERS))
        for character_id, owner in ((1, CO_OWNER), (2, MEMBER)):
            db.session.add(Character(id=character_id, name=f'Hero{character_id}', owner=owner, owner_username=f'user{owner}',
                                     url_name=f'hero{character_id}', background='Prowler', party_id=1,
                                     items='[]', containers=CONTAINERS))
        db.session.commit()
    clients = {}
    for user_id in range(1, 5):
        client = app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
        clients[user_id] = client
    return app, clients


# Each request changes storage, or opens a dialog that does.
CHANGES = [
    ('get', '/party/inventory/1/0', None),
    ('get', '/party/inventory/1/item-edit/None?mode=create', None),
    ('get', '/party/inventory/1/item-edit/gear', None),
    ('get', '/party/inventory/1/item-edit/gear/amount?action=minus&property=uses', None),
    ('get', '/party/inventory/1/0/item-delete/gear', None),
    ('get', '/party/inventory/1/container-edit/0', None),
    ('post', '/party/inventory/1/container-edit/None/save',
     dict(mode='create', name='Cart', slots='5', carried_by='', load='')),
    ('post', '/party/inventory/1/container-edit/0/delete', {'delete-items': 'true'}),
    ('get', '/party/inventory/1/item-transfer/0/gear', None),
    ('post', '/party/inventory/1/item-transfer/0/gear/transfer', dict(member='')),
    ('post', '/party/inventory/1/item-edit/gear/save',
     dict(edit_item_name='Rope', edit_item_tags='', edit_item_uses='', edit_item_charges='',
          edit_item_max_charges='', edit_item_container='0', edit_item_description='')),
]


def unchanged(app):
    with app.app_context():
        party = db.session.get(Party, 1)
        return json.loads(party.items) == [ITEM] and party.containers == CONTAINERS


@pytest.mark.parametrize('method,url,data', CHANGES)
@pytest.mark.parametrize('user_id', [MEMBER, OUTSIDER])
def test_only_the_warden_and_co_owners_change_storage(storage, method, url, data, user_id):
    app, clients = storage
    response = getattr(clients[user_id], method)(url, data=data)
    assert response.status_code == 403
    assert unchanged(app)


@pytest.mark.parametrize('method,url,data', CHANGES)
def test_logged_out_visitors_are_sent_to_login(storage, method, url, data):
    app, _ = storage
    response = getattr(app.test_client(), method)(url, data=data)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
    assert unchanged(app)


@pytest.mark.parametrize('user_id', [WARDEN, CO_OWNER])
def test_warden_and_co_owner_can_change_storage(storage, user_id):
    app, clients = storage
    response = clients[user_id].get('/party/inventory/1/item-edit/gear/amount?action=minus&property=uses')
    assert response.status_code == 200
    with app.app_context():
        assert json.loads(db.session.get(Party, 1).items)[0]['uses'] == 2


def test_switching_tabs_shows_editors_the_editable_view(storage):
    _, clients = storage
    url = '/party/inventory-select-container/1/0'
    for user_id in (WARDEN, CO_OWNER):
        assert 'Marketplace' in clients[user_id].get(url).get_data(as_text=True)
    page = clients[MEMBER].get(url)
    assert page.status_code == 200
    assert 'Rope' in page.get_data(as_text=True)
    assert 'Marketplace' not in page.get_data(as_text=True)


@pytest.mark.parametrize('user_id', [MEMBER, OUTSIDER])
def test_edit_party_is_limited_to_the_warden_and_co_owners(storage, user_id):
    app, clients = storage
    assert clients[user_id].get('/party/edit/user1/expedition').status_code == 403
    assert clients[user_id].post('/party/edit/user1/expedition/save',
                                 data=dict(name='Renamed', description='')).status_code == 403
    with app.app_context():
        assert db.session.get(Party, 1).name == 'Expedition'


def test_empty_storage_explains_itself(storage):
    app, clients = storage
    with app.app_context():
        db.session.get(Party, 1).items = '[]'
        db.session.commit()
    for user_id in (WARDEN, MEMBER):
        page = clients[user_id].get('/party/inventory-select-container/1/0').get_data(as_text=True)
        assert 'Nothing stored here yet.' in page
        assert 'storage-slots hidden' in page


def test_over_capacity_is_called_out(storage):
    app, clients = storage
    with app.app_context():
        db.session.get(Party, 1).items = json.dumps(
            [dict(id=f'r{i}', name='Rations', tags=['uses'], uses=3, location=0) for i in range(12)])
        db.session.commit()
    page = clients[MEMBER].get('/party/inventory-select-container/1/0').get_data(as_text=True)
    assert 'Over capacity: 12 of 10 slots used.' in page

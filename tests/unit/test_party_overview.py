import json
import re

import pytest

from app import socketio
from app.models import Character, Party, User, db


@pytest.fixture
def overview(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=i, username=f'user{i}') for i in range(1, 5)])
        db.session.add(Party(id=1, owner=1, name='Party', party_url='party', members='[1, 2]',
                             subowners='[2, 3]', items='[]', containers='[{"id":0,"name":"Main","slots":10}]'))
        for i in (1, 2):
            db.session.add(Character(
                id=i, owner=i + 1, owner_username=f'user{i + 1}', url_name=f'hero{i}',
                name=f'Hero{i}', background='Test', party_id=1, items='[]',
                containers='[{"id":0,"name":"Main","slots":10}]',
                hp=6, hp_max=8, strength=12, strength_max=14,
                dexterity=10, dexterity_max=12, willpower=9, willpower_max=11,
            ))
        db.session.commit()
    clients = {}
    sockets = {}
    for i in range(1, 5):
        client = app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
        clients[i] = client
        sockets[i] = socketio.test_client(app, flask_test_client=client)
    yield app, clients, sockets
    for socket in sockets.values():
        socket.disconnect()


STAT_URL = '/party/1/members/1/stat'


@pytest.mark.parametrize('user_id', [1, 2])
@pytest.mark.parametrize('stat,value', [('hp', 0), ('strength', 8), ('dexterity', 7), ('willpower', 6)])
def test_warden_and_character_owner_can_edit(overview, user_id, stat, value):
    app, clients, sockets = overview
    assert clients[user_id].post(STAT_URL, data={'stat': stat, 'value': value}).status_code == 204
    with app.app_context():
        character = db.session.get(Character, 1)
        assert getattr(character, stat) == value
        assert character.hp_max == 8
        assert db.session.get(Character, 2).hp == 6
    for recipient in (1, 2, 3):
        assert sockets[recipient].get_received() == [
            {'name': 'party_members_changed', 'args': [{'party_id': 1}], 'namespace': '/'},
        ]
    assert sockets[4].get_received() == []


def test_other_players_and_outsiders_cannot_edit(overview):
    app, clients, sockets = overview
    assert app.test_client().post(STAT_URL, data={'stat': 'hp', 'value': 0}).status_code == 302
    for user_id in (3, 4):
        assert clients[user_id].post(STAT_URL, data={'stat': 'hp', 'value': 0}).status_code == 403
    assert clients[1].get(STAT_URL).status_code == 405
    with app.app_context():
        assert db.session.get(Character, 1).hp == 6
    assert all(socket.get_received() == [] for socket in sockets.values())


@pytest.mark.parametrize('data', [
    {'stat': 'hp', 'value': -1}, {'stat': 'hp', 'value': 9},
    {'stat': 'hp', 'value': '1.5'}, {'stat': 'hp', 'value': ''},
    {'stat': 'hp'}, {'stat': 'hp_max', 'value': 20},
    {'stat': 'owner', 'value': 1}, {'stat': 'dead', 'value': 1},
])
def test_invalid_stats_do_not_write_or_broadcast(overview, data):
    app, clients, sockets = overview
    assert clients[1].post(STAT_URL, data=data).status_code == 400
    with app.app_context():
        assert db.session.get(Character, 1).hp == 6
        assert db.session.get(Character, 1).hp_max == 8
    assert all(socket.get_received() == [] for socket in sockets.values())


@pytest.mark.parametrize('path,user_id,snapshot', [
    (STAT_URL, 1, '/party/1/members'),
    ('/charedit/user2/hero1/stat', 2, '/charedit/user2/hero1/stats'),
])
def test_csrf_is_required_and_valid_token_works(overview, path, user_id, snapshot):
    app, clients, _ = overview
    app.config['WTF_CSRF_ENABLED'] = True
    assert clients[user_id].post(path, data={'stat': 'hp', 'value': 0}).status_code == 400
    html = clients[user_id].get(snapshot).get_data(as_text=True)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    assert clients[user_id].post(path, data={'stat': 'hp', 'value': 0, 'csrf_token': token}).status_code == 204


def test_stale_membership_cannot_edit_or_display_character(overview):
    app, clients, sockets = overview
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert clients[1].post(STAT_URL, data={'stat': 'hp', 'value': 0}).status_code == 404
    assert b'Hero1' not in clients[1].get('/party/1/members').data
    assert sockets[2].get_received() == []
    assert sockets[1].get_received()[0]['name'] == 'party_members_changed'


def test_member_snapshot_and_controls(overview):
    app, clients, _ = overview
    assert app.test_client().get('/party/1/members').status_code == 302
    for user_id, count in ((1, 8), (2, 4), (3, 4), (4, 0)):
        response = clients[user_id].get('/party/1/members')
        assert response.status_code == 200
        assert response.headers['Cache-Control'] == 'no-store'
        assert response.data.count(b'class="quick-stat-form"') == count
    page = clients[1].get('/users/user1/parties/party/').get_data(as_text=True)
    assert 'id="party-members" class="party-compact"' in page
    assert 'data-party-layout="cards"' in page
    edit = clients[1].get('/party/edit/user1/party').get_data(as_text=True)
    assert 'src="/static/images/portraits/default-portrait.webp"' in edit


def test_rest_and_inventory_changes_refresh_overview(overview):
    app, clients, sockets = overview
    assert clients[2].get('/charedit/rest/user2/hero1').status_code == 200
    assert sockets[1].get_received()[0]['name'] == 'party_members_changed'
    assert b'value="8"' in clients[1].get('/party/1/members').data
    with app.app_context():
        db.session.get(Character, 1).items = json.dumps([{'name': 'Shield', 'tags': ['1 Armor'], 'location': 0}])
        db.session.commit()
    assert sockets[1].get_received()[0]['name'] == 'party_members_changed'
    assert b'Armor</span><span>1' in clients[1].get('/party/1/members').data


def test_rollback_does_not_broadcast_or_leak_into_next_commit(overview):
    app, _, sockets = overview
    with app.app_context():
        db.session.get(Character, 1).hp = 0
        db.session.flush()
        db.session.rollback()
        db.session.get(User, 1).username = 'renamed'
        db.session.commit()
    assert all(socket.get_received() == [] for socket in sockets.values())


@pytest.mark.parametrize('stat', ['hp', 'strength', 'dexterity', 'willpower'])
def test_character_sheet_quick_edit_is_owner_only_and_broadcasts(overview, stat):
    app, clients, sockets = overview
    path = '/charedit/user2/hero1/stat'
    data = {'stat': stat, 'value': 0}
    assert app.test_client().post(path, data=data).status_code == 302
    for user_id in (1, 3, 4):
        assert clients[user_id].post(path, data=data).status_code == 403
    assert clients[2].post(path, data=data).status_code == 204
    with app.app_context():
        assert getattr(db.session.get(Character, 1), stat) == 0
    assert sockets[1].get_received()[0]['name'] == 'party_members_changed'
    assert sockets[4].get_received() == []


def test_character_quick_edit_also_works_without_a_party(overview):
    app, clients, _ = overview
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert clients[2].post('/charedit/user2/hero1/stat', data={'stat': 'hp', 'value': 3}).status_code == 204
    page = clients[2].get('/users/user2/characters/hero1/').get_data(as_text=True)
    assert page.count('class="sheet-stat-form"') == 12
    assert 'id="character-quick-hp"' in page
    for client in (app.test_client(), clients[1]):
        page = client.get('/users/user2/characters/hero1/').get_data(as_text=True)
        assert 'class="quick-stat-form"' not in page
        assert 'id="hp-view-text"' in page


def test_character_snapshot_preserves_effective_hp_and_rest_editor(overview):
    app, clients, _ = overview
    with app.app_context():
        db.session.get(Character, 1).panicked = True
        db.session.commit()
    snapshot = clients[2].get('/charedit/user2/hero1/stats')
    assert snapshot.headers['Cache-Control'] == 'no-store'
    assert b'Available HP: 0' in snapshot.data
    assert b'value="6"' in snapshot.data
    assert clients[1].get('/charedit/rest/user2/hero1').status_code == 403
    rest = clients[2].get('/charedit/rest/user2/hero1')
    assert rest.data.count(b'class="sheet-stat-form"') == 12
    assert b'/charedit/user2/hero1/stats' in rest.data
    assert b'value="8"' in rest.data

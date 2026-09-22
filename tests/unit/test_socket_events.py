import json

import pytest

from app import socketio
from app.models import Character, Party, PartyRoll, User, db


@pytest.fixture
def socket_party(app):
    with app.app_context():
        db.session.add_all([
            User(id=2, username='outsider'), User(id=12, username='player'),
            User(id=20, username='warden'), User(id=30, username='departing'),
        ])
        db.session.add(Party(id=1, owner=20, name='Party', members='[1, 2]', subowners='[12, 30]'))
        db.session.add_all([
            Character(id=1, owner=12, name='Player', background='Test', party_id=1),
            Character(id=2, owner=30, name='Departing', background='Test', party_id=1),
        ])
        db.session.commit()
    clients = {}
    for user_id in (2, 12, 20, 30):
        http = app.test_client()
        with http.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
        clients[user_id] = socketio.test_client(app, flask_test_client=http)
    yield clients
    for client in clients.values():
        if client.is_connected():
            client.disconnect()


def roll(client, **kwargs):
    client.emit('roll_dice', dict(character_id=1, party_id=1, roll=4, **kwargs))


def test_exact_membership_and_warden_receive_roll(socket_party):
    roll(socket_party[12])
    assert socket_party[2].get_received() == []
    for user_id in (12, 20, 30):
        events = socket_party[user_id].get_received()
        assert events[0]['name'] == 'dice_rolled'
        assert events[1] == {'name': 'roll_history_changed', 'args': [{'party_id': 1}], 'namespace': '/'}


def test_departed_member_stops_receiving_without_reconnecting(app, socket_party):
    with app.app_context():
        db.session.get(Character, 2).party_id = None
        db.session.get(Party, 1).members = '[1]'
        # Even stale subowners metadata must not deliver another roll.
        db.session.commit()
    roll(socket_party[12])
    assert socket_party[30].get_received() == []
    assert [event['name'] for event in socket_party[20].get_received()] == [
        'party_members_changed', 'dice_rolled', 'roll_history_changed',
    ]


def test_cannot_roll_another_users_character(socket_party):
    roll(socket_party[2])
    assert all(client.get_received() == [] for client in socket_party.values())


def test_anonymous_connection_rejected(app):
    assert not socketio.test_client(app).is_connected()


@pytest.mark.parametrize('data', [None, [], {}, {'character_id': 'bad'}, {'character_id': 1, 'party_id': 1, 'roll': {'html': 'bad'}}])
def test_malformed_roll_ignored(socket_party, data):
    socket_party[12].emit('roll_dice', data)
    assert all(client.get_received() == [] for client in socket_party.values())


def test_roll_limit_is_shared_between_connections(app, socket_party):
    app.config['SOCKET_EVENT_LIMIT'] = 2
    for _ in range(3):
        roll(socket_party[12])
    assert len(socket_party[20].get_received()) == 4
    assert socket_party[12].get_received()[-1]['name'] == 'rate_limited'
    socket_party[12].disconnect()
    http = app.test_client()
    with http.session_transaction() as session:
        session['_user_id'] = '12'
    socket_party[12] = socketio.test_client(app, flask_test_client=http)
    roll(socket_party[12])
    assert socket_party[20].get_received() == []


def history_client(app, user_id):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
    return client


def test_roll_persisted_with_original_name_and_escaped_result(app, socket_party):
    socket_party[12].emit('roll_dice', {'character_id': 1, 'party_id': 1, 'roll': '<img src=x onerror=alert(1)>'})
    with app.app_context():
        db.session.get(Character, 1).name = 'Renamed'
        db.session.commit()
        saved = PartyRoll.query.one()
        assert saved.character_name == 'Player'
        assert saved.created_at is not None
    response = history_client(app, 20).get('/party/1/roll-history')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert b'Player' in response.data and b'Renamed' not in response.data
    assert b'&lt;img' in response.data and b'<img' not in response.data


def test_history_latest_twenty_and_party_isolation(app, socket_party):
    with app.app_context():
        db.session.add(Party(id=2, owner=2, name='Other'))
        db.session.add_all([PartyRoll(party_id=1, character_name='Player', result=f'roll-{i:02}') for i in range(25)])
        db.session.add(PartyRoll(party_id=2, character_name='Other', result='secret'))
        db.session.commit()
    response = history_client(app, 12).get('/party/1/roll-history')
    html = response.get_data(as_text=True)
    assert html.count('data-roll-id=') == 20
    assert 'roll-04' not in html and 'secret' not in html
    assert html.index('roll-24') < html.index('roll-05')


def test_history_access_rechecked_after_leaving(app, app_with_babel, socket_party):
    assert app.test_client().get('/party/1/roll-history').status_code == 302
    assert history_client(app, 2).get('/party/1/roll-history').status_code == 403
    member = history_client(app, 30)
    assert member.get('/party/1/roll-history').status_code == 200
    with app.app_context():
        db.session.get(Character, 2).party_id = None
        db.session.commit()
    assert member.get('/party/1/roll-history').status_code == 403


def test_clear_history_owner_only_and_broadcasts_to_current_members(app, socket_party):
    roll(socket_party[12])
    for client in socket_party.values():
        client.get_received()
    with app.app_context():
        db.session.add(Party(id=2, owner=2, name='Other'))
        db.session.add(PartyRoll(party_id=2, character_name='Other', result='keep'))
        db.session.get(Character, 2).party_id = None
        db.session.commit()
    # Membership changes now also refresh the party overview.
    for client in socket_party.values():
        client.get_received()
    path = '/party/1/roll-history/clear'
    assert app.test_client().post(path).status_code == 302
    for user_id in (2, 12, 30):
        assert history_client(app, user_id).post(path).status_code == 403
    with app.app_context():
        assert PartyRoll.query.filter_by(party_id=1).count() == 1
    assert history_client(app, 20).get(path).status_code == 405
    assert history_client(app, 20).post(path).status_code == 204
    with app.app_context():
        assert PartyRoll.query.filter_by(party_id=1).count() == 0
        assert PartyRoll.query.filter_by(party_id=2).count() == 1
    for user_id in (12, 20):
        assert socket_party[user_id].get_received()[0]['name'] == 'roll_history_changed'
    for user_id in (2, 30):
        assert socket_party[user_id].get_received() == []


def test_clear_history_requires_csrf(app, socket_party):
    app.config['WTF_CSRF_ENABLED'] = True
    roll(socket_party[12])
    assert history_client(app, 20).post('/party/1/roll-history/clear').status_code == 400
    with app.app_context():
        assert PartyRoll.query.count() == 1


def test_rejected_rolls_are_not_saved(app, socket_party):
    roll(socket_party[2])
    socket_party[12].emit('roll_dice', {'character_id': 1, 'party_id': 999, 'roll': 3})
    with app.app_context():
        assert PartyRoll.query.count() == 0

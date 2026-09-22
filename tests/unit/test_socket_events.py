import json

import pytest

from app import socketio
from app.models import Character, Party, User, db


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
        assert socket_party[user_id].get_received()[0]['name'] == 'dice_rolled'


def test_departed_member_stops_receiving_without_reconnecting(app, socket_party):
    with app.app_context():
        db.session.get(Character, 2).party_id = None
        db.session.get(Party, 1).members = '[1]'
        # Even stale subowners metadata must not deliver another roll.
        db.session.commit()
    roll(socket_party[12])
    assert socket_party[30].get_received() == []
    assert len(socket_party[20].get_received()) == 1


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
    assert len(socket_party[20].get_received()) == 2
    assert socket_party[12].get_received()[-1]['name'] == 'rate_limited'
    socket_party[12].disconnect()
    http = app.test_client()
    with http.session_transaction() as session:
        session['_user_id'] = '12'
    socket_party[12] = socketio.test_client(app, flask_test_client=http)
    roll(socket_party[12])
    assert socket_party[20].get_received() == []

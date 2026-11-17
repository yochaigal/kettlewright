"""Large rosters: Wardens can filter the party to players who are connected (#424)."""
import pytest

import app.lib.presence as presence_module
from app import socketio
from app.lib.presence import TTL, Presence
from app.models import Character, Party, User, db


@pytest.fixture
def table(app_with_babel):
    """Warden (1) with their own character, and three players (2, 3, 4) with one each."""
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=i, username=name) for i, name in
                            [(1, 'warden'), (2, 'ana'), (3, 'bo'), (4, 'cy'), (5, 'stranger')]])
        db.session.add(Party(id=1, owner=1, owner_username='warden', name='Marches', party_url='marches',
                             members='[1, 2, 3, 4]', items='[]', containers='[{"id":0,"name":"Main","slots":10}]'))
        for i, (owner, name) in enumerate([(1, 'Ward'), (2, 'Ash'), (3, 'Birch'), (4, 'Cedar')], 1):
            db.session.add(Character(id=i, owner=owner, owner_username=['warden', 'ana', 'bo', 'cy'][owner - 1],
                                     url_name=name.lower(), name=name, background='Test', party_id=1, hp=4, hp_max=6,
                                     items='[]', containers='[{"id":0,"name":"Main","slots":10}]'))
        db.session.commit()
    return app


def http_for(app, user_id):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return client


def online_marks(page):
    import re
    return {int(cid): flag == '1' for cid, flag in re.findall(r'data-character-id="(\d+)" data-online="([01])"', page)}


# ----- The presence store -----

def test_presence_expires_after_the_ttl(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(presence_module, 'monotonic', lambda: clock[0])
    store = Presence()
    assert store.touch(7) is True and store.touch(7) is False  # touch() reports whether they just came online.
    assert store.online([7, 8]) == {7}
    clock[0] += TTL - 1
    assert store.online([7]) == {7}  # A reload or brief drop does not flicker offline...
    clock[0] += 2
    assert store.online([7]) == set()  # ...but a closed app does.
    assert store.touch(7) is True


def test_presence_failure_counts_nobody_as_connected(table, monkeypatch):
    monkeypatch.setattr(presence_module._presence, 'online', lambda ids: (_ for _ in ()).throw(ConnectionError()))
    with table.test_request_context():
        assert presence_module.online_user_ids({2}) == set()


# ----- The Warden's members list -----

def test_warden_sees_who_is_connected(table, fresh_presence):
    fresh_presence.touch(2)
    page = http_for(table, 1).get('/party/1/members').get_data(as_text=True)
    # The Warden's own character counts as connected: they are looking at the page.
    assert online_marks(page) == {1: True, 2: True, 3: False, 4: False}
    assert page.count('party-presence is-online') == 2 and 'Not connected' in page


def test_players_never_see_presence(table, fresh_presence):
    fresh_presence.touch(3)
    for user in (2, 3):
        page = http_for(table, user).get('/party/1/members').get_data(as_text=True)
        assert 'data-online' not in page and 'party-presence' not in page and 'Ash' in page


def test_party_page_offers_the_connected_filter_to_the_warden_only(table):
    warden = http_for(table, 1).get('/users/warden/parties/marches/').get_data(as_text=True)
    assert 'data-connected-only aria-pressed="false"' in warden and 'Connected only' in warden
    assert 'party-presence-summary' in warden and 'data-online="0"' in warden
    assert 'data-template="%(connected)s connected · %(hidden)s not connected (hidden)"' in warden
    player = http_for(table, 2).get('/users/warden/parties/marches/').get_data(as_text=True)
    assert 'data-connected-only' not in player and 'data-online' not in player


# ----- Heartbeats over Socket.IO -----

def test_connecting_and_heartbeats_mark_presence_without_pushing_events(table, fresh_presence):
    warden = socketio.test_client(table, flask_test_client=http_for(table, 1))
    warden.get_received()
    player = socketio.test_client(table, flask_test_client=http_for(table, 3))  # Connecting is a heartbeat.
    assert fresh_presence.online([3]) == {3}
    player.emit('presence')
    assert fresh_presence.online([3]) == {3}
    # The Warden's page re-checks on its own; no event reaches other sockets.
    assert warden.get_received() == []
    page = http_for(table, 1).get('/party/1/members').get_data(as_text=True)
    assert online_marks(page)[3] is True
    player.disconnect()
    warden.disconnect()


def test_presence_needs_no_database_change():
    from app.models import Party
    assert not {'away', 'present', 'online'} & set(Party.__table__.columns.keys())


def test_connected_filter_outranks_both_member_layouts():
    """The hide rule must beat '.party-compact #party-members-content .party-member { display: grid }'."""
    scss = open('app/static/src/scss/party.scss').read()
    assert ('#party-members.party-connected-only #party-members-content .party-member[data-online="0"] '
            '{ display: none; }') in scss

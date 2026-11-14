"""Dungeon actions (Search, Rest) and Dungeon Events are recorded for the whole party."""
import json
from unittest.mock import patch

import pytest

from app.models import Character, Party, PartyRoll, User, db

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'
ACTION = '/party/1/dungeon'
EVENT = '/party/1/dungeon/event'


@pytest.fixture
def party(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all(User(id=i, username=f'user{i}') for i in range(1, 4))
        db.session.add(Party(id=1, owner=1, owner_username='user1', name='Party', party_url='party',
                             members='[1, 2, 3]', subowners='[]', items='[]', containers=CONTAINERS))
        for i, name, hp in ((1, 'Aldous', 2), (2, 'Wren', 6), (3, 'Ysolde', 1)):
            db.session.add(Character(id=i, owner=2 if i < 3 else 3, owner_username='user2', name=name, url_name=f'hero{i}',
                                     background='Test', party_id=1, containers=CONTAINERS, hp=hp, hp_max=6,
                                     items=json.dumps([dict(id=f'f{i}', name='Fatigue', tags=[], location=0)])))
        db.session.commit()
    clients = {}
    for i in range(1, 4):
        clients[i] = app.test_client()
        with clients[i].session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
    return app, clients


def act(clients, action, participants=('1',), **extra):
    return clients[1].post(ACTION, data={'action': action, 'participants': list(participants), 'version': '0', **extra})


def last_entry(app):
    with app.app_context():
        return PartyRoll.query.order_by(PartyRoll.id.desc()).first().result


def test_search_records_who_searched_what(party):
    app, clients = party
    assert act(clients, 'search', ('1', '2'), target='  the   altar ').status_code == 302
    assert last_entry(app) == 'Search by Aldous, Wren: the altar.'


def test_search_without_a_target(party):
    app, clients = party
    act(clients, 'search')
    assert last_entry(app) == 'Search by Aldous.'


def test_rest_restores_hp_but_not_fatigue_and_not_for_the_deprived(party):
    app, clients = party
    with app.app_context():
        db.session.get(Character, 3).deprived = True
        db.session.commit()
    assert act(clients, 'rest', ('1', '2', '3')).status_code == 302
    assert last_entry(app) == ('Rest by Aldous, Wren, Ysolde. HP restored: Aldous (2 → 6). '
                               'Already at full HP: Wren. Deprived, no HP recovered: Ysolde.')
    with app.app_context():
        assert [db.session.get(Character, i).hp for i in (1, 2, 3)] == [6, 6, 1]
        # Only Make Camp removes Fatigue.
        assert all(json.loads(db.session.get(Character, i).items)[0]['name'] == 'Fatigue' for i in (1, 2, 3))


def test_dungeon_actions_need_a_participant_and_a_known_action(party):
    app, clients = party
    response = clients[1].post(ACTION, data={'action': 'rest', 'version': '0'})
    assert response.status_code == 302
    with clients[1].session_transaction() as session:
        assert ('dungeon', 'You need to select a PC first') in session['_flashes']
    assert act(clients, 'supply').status_code == 400
    with app.app_context():
        assert PartyRoll.query.count() == 0


def test_a_second_submission_is_refused(party):
    app, clients = party
    act(clients, 'rest')
    with app.app_context():
        db.session.get(Character, 1).hp = 1
        db.session.commit()
    act(clients, 'rest')  # Same version: refused, nothing changes.
    with app.app_context():
        assert db.session.get(Character, 1).hp == 1
        assert PartyRoll.query.count() == 1


def test_dungeon_event_is_rolled_once(party):
    app, clients = party
    with patch('app.lib.wilderness.secrets.randbelow', return_value=0):
        assert clients[1].post(EVENT, data={'night': 'on'}).status_code == 302
    assert last_entry(app) == 'Dungeon event (d6: 1): Encounter: Roll on an encounter table. Possibly hostile. (See Reactions.)'
    assert 'Dungeon event (d6: 1)' in clients[3].get('/party/1/roll-history').get_data(as_text=True)


@pytest.mark.parametrize('user_id', [2, 3])
def test_only_the_warden_takes_dungeon_actions(party, user_id):
    app, clients = party
    assert clients[user_id].post(ACTION, data={'action': 'rest', 'participants': '1', 'version': '0'}).status_code == 403
    assert clients[user_id].post(EVENT).status_code == 403
    with app.app_context():
        assert db.session.get(Character, 1).hp == 2
        assert PartyRoll.query.count() == 0


def test_dungeon_section_comes_before_wilderness_for_the_warden_only(party):
    _, clients = party
    page = clients[1].get('/users/user1/parties/party/').get_data(as_text=True)
    assert page.index('Dungeon actions') < page.index('Wilderness actions')
    assert 'Dungeon actions' not in clients[3].get('/users/user1/parties/party/').get_data(as_text=True)

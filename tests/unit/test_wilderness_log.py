"""Wilderness actions record who did what in the party's roll history (#305, #306)."""
import json
from unittest.mock import patch

import pytest

from app.models import Character, Party, PartyRoll, User, db

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'
ACTION = '/party/1/wilderness'


@pytest.fixture
def party(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all(User(id=i, username=f'user{i}') for i in range(1, 4))
        db.session.add(Party(id=1, owner=1, owner_username='user1', name='Party', party_url='party',
                             members='[1, 2]', subowners='[]', items='[]', containers=CONTAINERS))
        for i, name in ((1, 'Aldous'), (2, 'Wren')):
            db.session.add(Character(id=i, owner=i + 1, owner_username=f'user{i + 1}', name=name, url_name=f'hero{i}',
                                     background='Test', party_id=1, items='[]', containers=CONTAINERS, hp=3, hp_max=6))
        db.session.commit()
    clients = {}
    for i in range(1, 4):
        clients[i] = app.test_client()
        with clients[i].session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
    return app, clients


def act(clients, action, version=0, **extra):
    data = {'action': action, 'participants': ['1', '2'], 'version': str(version), **extra}
    return clients[1].post(ACTION, data=data)


def last_entry(app):
    with app.app_context():
        return PartyRoll.query.order_by(PartyRoll.id.desc()).first().result


def test_supply_names_the_foragers_and_die_steps(party):
    app, clients = party
    with patch('app.lib.wilderness.secrets.randbelow', return_value=2):
        assert act(clients, 'supply', bonus='1').status_code == 302
    assert last_entry(app) == ('Supply by Aldous, Wren (+1 die steps): d8 → 3 Rations (3 uses each), '
                               'added to party storage.')


def test_make_camp_is_recorded_with_its_details(party):
    app, clients = party
    with app.app_context():
        aldous, wren = db.session.get(Character, 1), db.session.get(Character, 2)
        aldous.items = json.dumps([dict(id='f', name='Fatigue', tags=[], location=0),
                                   dict(id='r', name='Rations', tags=['uses'], uses=3, location=0)])
        wren.items = json.dumps([dict(id='g', name='Fatigue', tags=[], location=0)])
        wren.deprived = True
        db.session.get(Party, 1).items = json.dumps([dict(id='s', name='Rations', tags=['uses'], uses=3, location=0)])
        db.session.commit()
    assert act(clients, 'camp').status_code == 302
    entry = last_entry(app)
    assert entry == ('Make Camp: Aldous, Wren rested. Ration uses: 1 from their own packs, 1 from party storage. '
                     'Fatigue removed: Aldous. Still deprived, Fatigue kept: Wren.')
    # Players see it too, not only the Warden (user3 plays Wren).
    assert 'Fatigue removed: Aldous.' in clients[3].get('/party/1/roll-history').get_data(as_text=True)
    with app.app_context():
        assert PartyRoll.query.filter_by(party_id=1).one().private_user_id is None


@pytest.mark.parametrize('path,roll,expected', [
    ('road', None, 'Travel by Road (Aldous, Wren): no risk of getting lost.'),
    ('trail', 1, 'Travel by Trail (Aldous, Wren): rolled 2 on d6 and got lost. Recovering may take another action.'),
    ('trail', 2, 'Travel by Trail (Aldous, Wren): rolled 3 on d6 and stayed on course.'),
    ('wilderness', 2, 'Travel by Wilderness (Aldous, Wren): rolled 3 on d6 and got lost. Recovering may take another action.'),
])
def test_travel_rolls_to_stay_on_course(party, path, roll, expected):
    app, clients = party
    with patch('app.lib.wilderness.secrets.randbelow', return_value=roll if roll is not None else 0) as rolled:
        assert act(clients, 'travel', path=path).status_code == 302
    assert last_entry(app) == expected
    assert rolled.called == (path != 'road')


def test_travel_rejects_an_unknown_path(party):
    _, clients = party
    assert act(clients, 'travel', path='teleport').status_code == 400


def test_explore_is_recorded(party):
    app, clients = party
    assert act(clients, 'explore').status_code == 302
    assert last_entry(app) == 'Explore by Aldous, Wren: searched the area for hidden features.'


def test_wilderness_event_follows_the_action_only_when_asked(party):
    app, clients = party
    with patch('app.lib.wilderness.secrets.randbelow', return_value=2):
        act(clients, 'explore', version=0, wilderness_event='on')
    assert last_entry(app) == ('Explore by Aldous, Wren: searched the area for hidden features. '
                               'Wilderness event (d6: 3): Environment: A shift in weather or terrain.')
    act(clients, 'explore', version=1)
    assert 'Wilderness event' not in last_entry(app)


def test_long_name_lists_stay_within_the_history_limit(party):
    app, clients = party
    with app.app_context():
        ids = []
        for i in range(3, 13):
            db.session.add(Character(id=i, owner=2, owner_username='user2', name='N' * 90 + str(i), url_name=f'h{i}',
                                     background='Test', party_id=1, items='[]', containers=CONTAINERS))
            ids.append(i)
        db.session.get(Party, 1).members = json.dumps([1, 2, *ids])
        db.session.commit()
    data = {'action': 'explore', 'participants': [str(i) for i in (1, 2, *ids)], 'version': '0', 'wilderness_event': 'on'}
    assert clients[1].post(ACTION, data=data).status_code == 302
    entry = last_entry(app)
    assert len(entry) <= 500
    assert 'and 8 more' in entry

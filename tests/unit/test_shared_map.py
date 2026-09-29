import json
import re

import pytest

from app import socketio
from app.models import Character, Party, PartyMap, User, db

URL = '/party/1/shared-map/scene'
DRAWING = {'elements': [{'id': 'token', 'type': 'ellipse', 'x': 20, 'y': 40,
                         'width': 40, 'height': 40}], 'files': {}}


@pytest.fixture
def shared(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all(User(id=i, username=f'map{i}') for i in range(1, 5))
        db.session.add_all([
            Party(id=1, owner=1, owner_username='map1', party_url='party', name='Party', members='[1]', subowners='[2,3]', items='[]', containers='[]'),
            Party(id=2, owner=4, name='Other', members='[]'),
            Character(id=1, owner=2, name='Player', background='Test', party_id=1),
        ])
        db.session.commit()
    clients, sockets = {}, {}
    for i in range(1, 5):
        clients[i] = app.test_client()
        with clients[i].session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
        sockets[i] = socketio.test_client(app, flask_test_client=clients[i])
    yield app, clients, sockets
    for client in sockets.values():
        client.disconnect()


def test_empty_map_and_access(shared):
    app, clients, _ = shared
    for i in (1, 2):
        result = clients[i].get(URL)
        assert result.json == {'version': 0, 'drawing': {'elements': [], 'files': {}}}
        assert result.headers['Cache-Control'] == 'no-store'
        html = clients[i].get('/party/1/shared-map').get_data(as_text=True)
        assert 'Shared Map' in html
        assert 'data-library=' not in html
    for i in (3, 4):
        assert clients[i].get(URL).status_code == 403
        assert clients[i].get('/party/1/shared-map').status_code == 403
    assert app.test_client().get(URL).status_code == 302
    with app.app_context():
        assert PartyMap.query.count() == 0


def test_save_persists_and_notifies_only_current_party(shared):
    app, clients, sockets = shared
    for i in (2, 3, 4):
        assert clients[i].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 403
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).json == {'version': 1}
    saved = clients[2].get(URL).json
    assert saved['drawing']['elements'][0]['x'] == 20
    assert saved['version'] == 1
    assert clients[4].get('/party/2/shared-map/scene').json['version'] == 0
    for i in (1, 2):
        assert sockets[i].get_received() == [{'name': 'shared_map_changed', 'args': [{'party_id': 1, 'version': 1}], 'namespace': '/'}]
    for i in (3, 4):
        assert sockets[i].get_received() == []
    assert clients[1].post(URL, json={'version': 1, 'drawing': {'elements': [], 'files': {}}}).json == {'version': 2}
    assert clients[2].get(URL).json['drawing']['elements'] == []


@pytest.mark.parametrize('version', [0, 1, 99])
def test_stale_tabs_cannot_overwrite(shared, version):
    _, clients, _ = shared
    for v in (0, 1):
        assert clients[1].post(URL, json={'version': v, 'drawing': DRAWING}).status_code == 200
    assert clients[1].post(URL, json={'version': version, 'drawing': {'elements': [], 'files': {}}}).status_code == 409
    assert clients[2].get(URL).json['drawing']['elements'][0]['id'] == 'token'


def test_departed_player_loses_read_and_live_updates(shared):
    app, clients, sockets = shared
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    for client in sockets.values():
        client.get_received()
    assert clients[2].get(URL).status_code == 403
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 200
    assert sockets[2].get_received() == []


def test_csrf_and_valid_token(shared):
    app, clients, _ = shared
    app.config['WTF_CSRF_ENABLED'] = True
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 400
    html = clients[1].get('/party/1/shared-map').get_data(as_text=True)
    config = json.loads(re.search(r'id="shared-map-config" type="application/json">(.*?)</script>', html, re.S)[1])
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING, 'csrf_token': config['csrfToken']}).status_code == 200


@pytest.mark.parametrize('payload', [[], {}, {'version': True, 'drawing': DRAWING},
    {'version': -1, 'drawing': DRAWING}, {'version': 0, 'drawing': {'elements': [{'id': 'bad', 'type': 'iframe'}], 'files': {}}}])
def test_invalid_payload_rejected(shared, payload):
    app, clients, sockets = shared
    assert clients[1].post(URL, json=payload).status_code == 400
    with app.app_context():
        assert PartyMap.query.count() == 0
    assert all(client.get_received() == [] for client in sockets.values())


def test_background_frames_and_curated_libraries(shared):
    from pathlib import Path
    from app.lib.map_drawing import validate_drawing
    app, clients, _ = shared
    scene = {'elements': [{'id': 'frame', 'type': 'frame', 'x': 0, 'y': 0, 'width': 100, 'height': 100},
                          {**DRAWING['elements'][0], 'frameId': 'frame'}],
             'files': {}, 'appState': {'viewBackgroundColor': '#ddeeff', 'collaborators': 'ignored'}}
    assert clients[1].post(URL, json={'version': 0, 'drawing': scene}).status_code == 200
    saved = clients[2].get(URL).json['drawing']
    assert saved['appState'] == {'viewBackgroundColor': '#ddeeff'}
    assert saved['elements'][1]['frameId'] == 'frame'
    with app.test_request_context():
        for path in Path('app/static/vendor/excalidraw-libraries').glob('*.excalidrawlib'):
            for item in json.loads(path.read_text())['libraryItems']:
                assert validate_drawing({'elements': item['elements'], 'files': {}}, allow_frames=True)['elements']

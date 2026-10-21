from whiteboard_helpers import post_scene, post_import, post_fog, scene_payload
import json
import re
from copy import deepcopy

import pytest

from app import socketio
from app.models import Character, Party, PartyMap, User, db

URL = '/party/1/shared-map/scene'
DRAWING = {'elements': [{'id': 'token', 'type': 'ellipse', 'x': 20, 'y': 40,
                         'width': 40, 'height': 40}], 'files': {}}


@pytest.fixture
def image_drawing():
    import base64
    import io
    from PIL import Image
    image = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(image, format='PNG')
    return {'elements': [{'id': 'photo', 'type': 'image', 'fileId': 'photo-file', 'x': 0, 'y': 0}],
            'files': {'photo-file': {'id': 'photo-file', 'mimeType': 'image/png',
                      'dataURL': 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode()}}}


def test_scene_revision_check_returns_no_body_and_revalidates_access(shared):
    app, clients, _ = shared
    initial = clients[2].get(URL).json
    revisions = {key: initial[key] for key in ('version', 'generation', 'fog_version', 'tokens_version', 'encounter_version', 'markers_version', 'activation_version', 'view_revision')}
    response = clients[2].get(URL, query_string=revisions)
    assert response.status_code == 204 and response.data == b''
    assert response.headers['Cache-Control'] == 'no-store'
    assert post_scene(clients[1], json={'version': 0, 'drawing': DRAWING}).status_code == 200
    assert clients[2].get(URL, query_string=revisions).json['version'] == 1
    revisions['version'] = 1
    assert clients[2].get(URL, query_string=revisions).status_code == 204
    assert clients[2].get(URL, query_string={**revisions, 'fog_version': 1}).status_code == 200
    assert clients[2].get(URL, query_string={**revisions, 'generation': 2}).status_code == 200
    assert clients[2].get(URL, query_string={'version': 1}).status_code == 200
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert clients[2].get(URL, query_string=revisions).status_code == 403


def test_move_reuses_saved_image_without_upload_or_redecoding(shared, image_drawing, monkeypatch):
    _, clients, sockets = shared
    assert post_scene(clients[1], json={'version': 0, 'drawing': image_drawing}).status_code == 200
    for socket in sockets.values():
        socket.get_received()
    moved = deepcopy(image_drawing)
    moved['files'] = {}
    moved['elements'][0]['x'] = 200
    def unexpected_decode(*args, **kwargs):
        pytest.fail('An unchanged server-owned image must not be decoded again')
    monkeypatch.setattr('app.lib.map_drawing.Image.open', unexpected_decode)
    assert post_scene(clients[2], json={'version': 1, 'drawing': moved, 'reuse_files': ['photo-file']}).status_code == 200
    saved = clients[2].get(URL).json
    assert saved['drawing']['elements'][0]['x'] == 200
    assert saved['drawing']['files']['photo-file']['dataURL'] == image_drawing['files']['photo-file']['dataURL']
    events = [event for event in sockets[1].get_received() if event['name'] == 'shared_map_changed']
    assert events[0]['args'][0]['update']['drawing']['files'] == {}
    # An old revision cannot resolve references against a newer scene.
    assert post_scene(clients[2], json={'version': 1, 'drawing': moved, 'reuse_files': ['photo-file']}).status_code == 409


@pytest.mark.parametrize('references', [['unknown'], ['photo-file', 'photo-file'], 'photo-file', [1], [{}]])
def test_invalid_image_references_do_not_modify_scene(shared, image_drawing, references):
    _, clients, _ = shared
    assert post_scene(clients[1], json={'version': 0, 'drawing': image_drawing}).status_code == 200
    before = clients[1].get(URL).json
    drawing = {**image_drawing, 'files': {}}
    assert post_scene(clients[2], json={'version': 1, 'drawing': drawing, 'reuse_files': references}).status_code == 400
    assert clients[1].get(URL).json == before


def test_references_cannot_read_other_boards_or_bypass_new_image_validation(shared, image_drawing):
    app, clients, _ = shared
    with app.app_context():
        db.session.add(PartyMap(party_id=2, drawing=image_drawing))
        db.session.commit()
    assert post_scene(clients[1], json={'version': 0, 'drawing': {**image_drawing, 'files': {}}, 'reuse_files': ['photo-file']}).status_code == 400
    broken = deepcopy(image_drawing)
    broken['files']['photo-file']['dataURL'] = 'data:image/png;base64,AAAA'
    assert post_scene(clients[1], json={'version': 0, 'drawing': broken}).status_code == 400


def test_references_preserve_warden_image_locks(shared, image_drawing):
    _, clients, _ = shared
    image_drawing['elements'][0]['locked'] = True
    assert post_scene(clients[1], json={'version': 0, 'drawing': image_drawing}).status_code == 200
    drawing = clients[1].get(URL).json['drawing']
    drawing['files'] = {}
    assert post_scene(clients[2], json={'version': 1, 'drawing': drawing, 'reuse_files': ['photo-file']}).status_code == 200
    drawing['elements'][0]['x'] = 200
    assert post_scene(clients[2], json={'version': 2, 'drawing': drawing, 'reuse_files': ['photo-file']}).status_code == 400


@pytest.fixture
def shared(app_with_babel):
    app = app_with_babel
    app.config.update(LOCAL_FEATURE_ACCESS=False, FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
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
        assert result.json['version'] == 0 and result.json['drawing'] == {'elements': [], 'files': {}}
        assert result.json['protocol'] == 2 and result.json['scene_id'] > 0
        assert result.headers['Cache-Control'] == 'no-store'
        html = clients[i].get('/party/1/shared-map').get_data(as_text=True)
        assert 'Whiteboard' in html
        config = json.loads(re.search(r'id="shared-map-config" type="application/json">(.*?)</script>', html, re.S)[1])
        assert config['editing'] is True
        assert config['canLoadMaps'] is (i == 1)
        if i == 1:
            assert config['sourcesUrl'] == '/party/1/shared-map/sources'
            assert config['importUrl'] == '/party/1/shared-map/import'
            assert 'id="load-map"' in html and 'id="map-import"' in html
        else:
            assert config['sourcesUrl'] is None and config['importUrl'] is None
            assert 'id="load-map"' not in html and 'id="map-import"' not in html
        assert 'data-library=' not in html
        assert clients[i].get('/campaigns/').status_code == 200
        assert clients[i].get('/party/1/materials/').status_code == 200
    for i in (3, 4):
        assert clients[i].get(URL).status_code == 403
        assert clients[i].get('/party/1/shared-map').status_code == 403
    assert app.test_client().get(URL).status_code == 302
    with app.app_context():
        assert PartyMap.query.count() == 1


def test_save_persists_and_notifies_only_current_party(shared):
    app, clients, sockets = shared
    for i in (3, 4):
        assert post_scene(clients[i], json={'version': 0, 'drawing': DRAWING}).status_code == 403
    assert post_scene(clients[2], json={'version': 0, 'drawing': DRAWING}).json == {'version': 1}
    saved = clients[2].get(URL).json
    assert saved['drawing']['elements'][0]['x'] == 20
    assert saved['version'] == 1
    assert clients[4].get('/party/2/shared-map/scene').json['version'] == 0
    for i in (1, 2):
        events = sockets[i].get_received()
        assert len(events) == 1 and events[0]['name'] == 'shared_map_changed'
        event = events[0]['args'][0]
        assert {key: event[key] for key in ('party_id', 'version', 'generation', 'fog_version')} == {'party_id': 1, 'version': 1, 'generation': 1, 'fog_version': 0}
        assert event['update']['drawing']['elements'] == saved['drawing']['elements']
        assert event['update']['drawing']['base_version'] == 0
    for i in (3, 4):
        assert sockets[i].get_received() == []
    assert post_scene(clients[1], json={'version': 1, 'drawing': {'elements': [], 'files': {}}}).json == {'version': 2}
    assert clients[2].get(URL).json['drawing']['elements'] == []


def test_party_page_shows_whiteboard_and_campaign_for_all_members(shared):
    app, clients, _ = shared
    with app.app_context():
        for model in (Party, Character):
            entity = db.session.get(model, 1)
            entity.containers = '[{"id":0,"name":"Main","slots":10}]'
            entity.items = '[]'
        character = db.session.get(Character, 1)
        character.owner_username = 'map2'
        character.url_name = 'player'
        db.session.commit()
    for user_id in (1, 2):
        response = clients[user_id].get('/users/map1/parties/party/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'href="/party/1/shared-map"' in html
        assert 'href="/campaigns/"' in html
        assert 'id="campaign-details-tab"' in html
        assert ('Create and show' in html) is (user_id == 1)


@pytest.mark.parametrize('version', [0, 1, 99])
def test_stale_tabs_cannot_overwrite(shared, version):
    _, clients, _ = shared
    for v in (0, 1):
        assert post_scene(clients[1], json={'version': v, 'drawing': DRAWING}).status_code == 200
    assert post_scene(clients[1], json={'version': version, 'drawing': {'elements': [], 'files': {}}}).status_code == 409
    assert clients[2].get(URL).json['drawing']['elements'][0]['id'] == 'token'


def test_departed_player_loses_read_and_live_updates(shared):
    app, clients, sockets = shared
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    for client in sockets.values():
        client.get_received()
    assert clients[2].get(URL).status_code == 403
    assert post_scene(clients[2], json={'version': 0, 'drawing': DRAWING}).status_code == 403
    assert post_scene(clients[1], json={'version': 0, 'drawing': DRAWING}).status_code == 200
    assert sockets[2].get_received() == []


@pytest.mark.parametrize('user_id', [1, 2])
def test_csrf_and_valid_token(shared, user_id):
    app, clients, _ = shared
    app.config['WTF_CSRF_ENABLED'] = True
    assert post_scene(clients[user_id], json={'version': 0, 'drawing': DRAWING}).status_code == 400
    html = clients[user_id].get('/party/1/shared-map').get_data(as_text=True)
    config = json.loads(re.search(r'id="shared-map-config" type="application/json">(.*?)</script>', html, re.S)[1])
    assert post_scene(clients[user_id], json={'version': 0, 'drawing': DRAWING, 'csrf_token': config['csrfToken']}).status_code == 200


@pytest.mark.parametrize('payload', [[], {}, {'version': True, 'drawing': DRAWING},
    {'version': -1, 'drawing': DRAWING}, {'version': 0, 'drawing': {'elements': [{'id': 'bad', 'type': 'iframe'}], 'files': {}}}])
def test_invalid_payload_rejected(shared, payload):
    app, clients, sockets = shared
    assert post_scene(clients[1], json=payload).status_code == 400
    with app.app_context():
        assert PartyMap.query.count() == (0 if isinstance(payload, list) else 1)
    assert all(client.get_received() == [] for client in sockets.values())


def test_background_frames_and_curated_libraries(shared):
    from pathlib import Path
    from app.lib.map_drawing import validate_drawing
    app, clients, _ = shared
    scene = {'elements': [{'id': 'frame', 'type': 'frame', 'x': 0, 'y': 0, 'width': 100, 'height': 100},
                          {**DRAWING['elements'][0], 'frameId': 'frame'}],
             'files': {}, 'appState': {'viewBackgroundColor': '#ddeeff', 'collaborators': 'ignored'}}
    assert post_scene(clients[1], json={'version': 0, 'drawing': scene}).status_code == 200
    saved = clients[2].get(URL).json['drawing']
    assert saved['appState'] == {'viewBackgroundColor': '#ddeeff'}
    assert saved['elements'][1]['frameId'] == 'frame'
    with app.test_request_context():
        for path in Path('app/static/vendor/excalidraw-libraries').glob('*.excalidrawlib'):
            library = json.loads(path.read_text())
            assert library['type'] == 'excalidrawlib', path.name
            assert library['version'] in (1, 2), path.name
            drawings = (library['library'] if library['version'] == 1
                        else [item['elements'] for item in library['libraryItems']])
            assert drawings, path.name
            for elements in drawings:
                assert validate_drawing({'elements': elements, 'files': {}}, allow_frames=True)['elements'], path.name


@pytest.mark.parametrize('pressure', [0, 0.5, 1])
def test_legacy_freehand_points_are_normalized_without_mutating_input(shared, pressure):
    from app.lib.map_drawing import validate_drawing
    app, _, _ = shared
    drawing = {'elements': [{'id': 'legacy', 'type': 'freedraw',
                            'points': [[0, 0], [10, 20, pressure]]}], 'files': {}}
    with app.test_request_context():
        saved = validate_drawing(drawing)
    assert saved['elements'][0]['points'] == [[0, 0], [10, 20]]
    assert drawing['elements'][0]['points'][1] == [10, 20, pressure]


@pytest.mark.parametrize('kind, point', [
    ('freedraw', [1, 2, True]), ('freedraw', [1, 2, '0.5']),
    ('freedraw', [1, 2, -0.1]), ('freedraw', [1, 2, 1.1]),
    ('freedraw', [1, 2, float('nan')]), ('freedraw', [True, 2, 0.5]),
    ('freedraw', [1, 2, 0.5, 0]), ('line', [1, 2, 0.5]),
    ('arrow', [1, 2, 0.5]),
])
def test_invalid_legacy_points_are_rejected(shared, kind, point):
    from app.lib.map_drawing import validate_drawing
    from werkzeug.exceptions import BadRequest
    app, _, _ = shared
    with app.test_request_context(), pytest.raises(BadRequest):
        validate_drawing({'elements': [{'id': 'invalid', 'type': kind,
                                       'points': [[0, 0], point]}], 'files': {}})

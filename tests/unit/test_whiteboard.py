from copy import deepcopy

import pytest
from app.models import Campaign, ContentEntry, PointcrawlMap, MapNode, MapEdge, PartyMap, db
from test_shared_map import shared, DRAWING, URL

BASE = '/party/1/shared-map'


@pytest.fixture
def sources(shared):
    app, clients, sockets = shared
    app.config.update(FEATURE_TEST_USER_IDS={1}, FEATURE_TEST_PARTY_IDS={1})
    with app.app_context():
        campaign = Campaign(owner_id=1, name='Campaign')
        root = ContentEntry(owner_id=1, campaign=campaign, category='geography', title='Region', body='ROOT SECRET')
        first = ContentEntry(owner_id=1, campaign=campaign, category='location', title='Town', body='TOWN SECRET')
        second = ContentEntry(owner_id=1, campaign=campaign, category='location', title='Cave', body='CAVE SECRET')
        path = ContentEntry(owner_id=1, campaign=campaign, category='path', title='Path', body='PATH SECRET', path_type='hidden')
        board = PointcrawlMap(id=101, entry=root, kind='region', drawing=deepcopy(DRAWING))
        a = MapNode(map=board, entry=first, number=1, x=10, y=20)
        b = MapNode(map=board, entry=second, number=2, x=200, y=100)
        db.session.add_all([board, a, b])
        db.session.flush()
        db.session.add(MapEdge(map=board, entry=path, source_id=a.id, target_id=b.id))
        db.session.add_all([
            PointcrawlMap(id=102, entry=ContentEntry(owner_id=1, category='dungeon', title='Unfiled dungeon'), drawing=deepcopy(DRAWING)),
            PointcrawlMap(id=103, entry=ContentEntry(owner_id=4, category='dungeon', title='Other owner'), drawing=deepcopy(DRAWING))])
        db.session.commit()
    return shared


def load(clients, source_id=101, **overrides):
    scene = clients[1].get(URL).json
    preview = clients[1].get(f'{BASE}/sources/{source_id}').json
    payload = {key: scene[key] for key in ('version', 'generation', 'fog_version')}
    payload.update(source_id=source_id, digest=preview['digest'], cover=True)
    payload.update(overrides)
    return clients[1].post(f'{BASE}/import', json=payload)


def fog(clients, operation, **overrides):
    scene = clients[1].get(URL).json
    payload = {key: scene[key] for key in ('generation', 'fog_version')}
    payload.update(operation=operation)
    payload.update(overrides)
    return clients[1].post(f'{BASE}/fog', json=payload)


def test_owned_sources_and_visual_snapshot(sources):
    _, clients, _ = sources
    html = clients[1].get(BASE).get_data(as_text=True)
    assert 'id="load-map"' in html and 'id="map-import"' in html
    maps = clients[1].get(f'{BASE}/sources').json['maps']
    assert {m['id'] for m in maps} == {101, 102}
    assert {m['campaign'] for m in maps} == {'Campaign', None}
    preview = clients[1].get(f'{BASE}/sources/101')
    assert 'SECRET' not in preview.text
    elements = preview.json['drawing']['elements']
    assert len(elements) == 6
    assert not any(e['id'].startswith('kw-') or e.get('customData') or e.get('link') for e in elements)
    assert any(e.get('text') == '1. Town' for e in elements)
    assert any(e.get('strokeStyle') == 'dashed' for e in elements)
    assert clients[1].get(f'{BASE}/sources/103').status_code == 403
    for user_id in (2, 3, 4):
        assert clients[user_id].get(f'{BASE}/sources').status_code == 403
        assert clients[user_id].get(f'{BASE}/sources/101').status_code == 403
        assert clients[user_id].post(f'{BASE}/import', json={}).status_code == 403
        assert clients[user_id].post(f'{BASE}/fog', json={}).status_code == 403


@pytest.mark.parametrize('source_id', [101, 102])
def test_import_atomic_replacement_and_independent_original(sources, source_id):
    app, clients, _ = sources
    result = load(clients, source_id)
    assert result.status_code == 200
    scene = result.json
    assert scene['generation'] == 2 and scene['version'] == 1 and scene['fog_version'] == 1
    assert scene['fog']['enabled'] is True
    assert clients[2].get(URL).json == scene
    for generation in (None, 1):
        payload = {'drawing': DRAWING, 'version': 1}
        if generation is not None:
            payload['generation'] = generation
        assert clients[2].post(URL, json=payload).json == {'reason': 'replaced'}
    assert clients[2].post(URL, json={'generation': 2, 'version': 1, 'drawing': DRAWING}).status_code == 200
    assert clients[2].get(URL).json['fog'] == scene['fog']
    with app.app_context():
        assert db.session.get(PointcrawlMap, source_id).drawing == DRAWING


def test_import_detects_changed_source_or_board(sources):
    app, clients, _ = sources
    preview = clients[1].get(f'{BASE}/sources/101').json
    with app.app_context():
        db.session.get(PointcrawlMap, 101).nodes[0].entry.title = 'Renamed'
        db.session.commit()
    assert load(clients, digest=preview['digest']).json == {'reason': 'source_changed'}
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 200
    assert load(clients, version=0).status_code == 409
    assert clients[1].get(URL).json['generation'] == 1


def test_fog_lazy_creation_idempotency_and_independent_versions(shared):
    _, clients, _ = shared
    result = fog(clients, {'id': 'enable', 'type': 'hide_all'})
    assert result.status_code == 200
    assert result.json['fog_version'] == 1
    assert clients[2].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 200
    stroke = {'id': 'stroke', 'type': 'reveal', 'radius': 25, 'points': [[0, 0], [50, 0]]}
    assert fog(clients, stroke).json['fog_version'] == 2
    assert fog(clients, stroke, fog_version=1).json['fog_version'] == 2
    assert clients[2].get(URL).json['version'] == 1
    assert fog(clients, {'id': 'undo', 'type': 'undo'}).json['fog']['strokes'] == []
    assert fog(clients, {'id': 'all', 'type': 'reveal_all'}).json['fog']['base'] == 'clear'
    assert fog(clients, {'id': 'off', 'type': 'disable'}).json['fog']['enabled'] is False
    assert fog(clients, {'id': 'stale', 'type': 'hide_all'}, fog_version=0).status_code == 409


def test_replacement_rejects_old_fog_queue(sources):
    _, clients, _ = sources
    load(clients)
    assert fog(clients, {'id': 'old', 'type': 'reveal_all'}, generation=1).json == {'reason': 'replaced'}
    assert clients[2].get(URL).json['fog']['base'] == 'covered'


@pytest.mark.parametrize('operation', [None, {}, {'id': 'a', 'type': 'arbitrary'},
    {'id': 'disabled-stroke', 'type': 'reveal', 'radius': 10, 'points': [[0, 0]]},
    {'id': 'a', 'type': 'reveal', 'radius': True, 'points': [[0, 0]]},
    {'id': 'a', 'type': 'cover', 'radius': 10, 'points': [[float('inf'), 0]]}])
def test_invalid_fog_does_not_mutate(shared, operation):
    app, clients, _ = shared
    assert fog(clients, operation).status_code == 400
    with app.app_context():
        assert PartyMap.query.count() == 0


def test_campaign_gate_and_csrf_cover_import_routes(sources):
    app, clients, _ = sources
    app.config['WTF_CSRF_ENABLED'] = True
    assert clients[1].post(f'{BASE}/import', json={}).status_code == 400
    assert clients[1].post(f'{BASE}/fog', json={}).status_code == 400
    app.config['FEATURE_TEST_PARTY_IDS'] = set()
    for path in ('sources', 'sources/101'):
        assert clients[1].get(f'{BASE}/{path}').status_code == 404
    assert clients[1].post(f'{BASE}/import', json={}).status_code == 404
    assert clients[1].post(f'{BASE}/fog', json={}).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = False
    assert fog(clients, {'id': 'public-board', 'type': 'hide_all'}).status_code == 200
    app.config['FEATURE_TEST_PARTY_IDS'] = {1}
    app.config['FEATURE_TEST_USER_IDS'] = set()
    for path in ('sources', 'sources/101'):
        assert clients[1].get(f'{BASE}/{path}').status_code == 404
    assert clients[1].post(f'{BASE}/import', json={}).status_code == 404


def test_import_keeps_images_groups_and_bindings(sources):
    import base64
    import io
    from PIL import Image
    app, clients, _ = sources
    image = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(image, format='PNG')
    url = 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode()
    drawing = {'elements': [
        {'id': 'box', 'type': 'rectangle', 'x': 0, 'y': 0, 'width': 100, 'height': 80,
         'groupIds': ['group'], 'boundElements': [{'id': 'label', 'type': 'text'}]},
        {'id': 'label', 'type': 'text', 'text': 'Label', 'containerId': 'box', 'groupIds': ['group']},
        {'id': 'photo', 'type': 'image', 'fileId': 'file', 'x': 150, 'y': 0, 'width': 40, 'height': 40},
    ], 'files': {'file': {'id': 'file', 'mimeType': 'image/png', 'dataURL': url}}}
    with app.app_context():
        db.session.get(PointcrawlMap, 102).drawing = drawing
        db.session.commit()
    result = load(clients, 102, cover=False).json
    box, label, photo = result['drawing']['elements']
    assert box['id'] != 'box' and label['id'] != 'label'
    assert label['containerId'] == box['id']
    assert box['boundElements'][0]['id'] == label['id']
    assert box['groupIds'] == label['groupIds'] != ['group']
    assert photo['fileId'] != 'file'
    assert result['drawing']['files'][photo['fileId']]['dataURL'] == url
    assert result['fog']['enabled'] is False


def test_party_tokens_use_current_roster_and_membership(shared):
    from app.models import Character
    app, clients, _ = shared
    path = '/party/1/shared-map/tokens'
    for user in (1, 2):
        result = clients[user].get(path)
        assert result.headers['Cache-Control'] == 'no-store'
        assert result.json['tokens'] == [{'id': 1, 'name': 'Player',
            'portrait': '/static/images/portraits/default-portrait.webp'}]
    assert clients[3].get(path).status_code == 403
    assert clients[4].get(path).status_code == 403
    with app.app_context():
        character = db.session.get(Character, 1)
        character.custom_image = True
        character.image_url = 'javascript:alert(1)'
        db.session.commit()
    assert clients[1].get(path).json['tokens'][0]['portrait'] is None
    with app.app_context():
        character = db.session.get(Character, 1)
        character.party_id = None
        db.session.commit()
    assert clients[1].get(path).json == {'tokens': []}
    assert clients[2].get(path).status_code == 403
    app.config['FEATURE_TEST_PARTY_IDS'] = set()
    assert clients[1].get(path).status_code == 200


def test_party_tokens_include_pets_hirelings_and_their_pets(shared):
    from app.models import Character, Companion
    app, clients, _ = shared
    with app.app_context():
        db.session.add_all([
            Companion(id=1, kind='pet', character_id=1, name='Moss', notes='Private pet notes'),
            Companion(id=2, kind='hireling', party_id=1, name='Ada', shared=False, notes='Private hireling notes'),
            Companion(id=3, kind='pet', hireling_id=2, name='Pip'),
            Companion(id=4, kind='hireling', party_id=2, name='Other hireling'),
            Companion(id=5, kind='pet', hireling_id=4, name='Other pet'),
            Character(id=2, owner=3, name='Not on roster', background='Test', party_id=1),
            Companion(id=6, kind='pet', character_id=2, name='Unlisted pet'),
        ])
        db.session.commit()
    path = BASE + '/tokens'
    for user in (1, 2):
        tokens = clients[user].get(path).json['tokens']
        assert [token['name'] for token in tokens] == ['Player', 'Moss', 'Ada', 'Pip']
        assert len({token['id'] for token in tokens}) == 4
        assert tokens[1:] == [
            {'id': 'companion:1', 'name': 'Moss', 'portrait': None, 'kind': 'pet', 'parent': 'Player'},
            {'id': 'companion:2', 'name': 'Ada', 'portrait': None, 'kind': 'hireling', 'parent': 'Party'},
            {'id': 'companion:3', 'name': 'Pip', 'portrait': None, 'kind': 'pet', 'parent': 'Ada'},
        ]
    with app.app_context():
        db.session.get(Companion, 1).image_url = 'default-portrait.webp'
        hireling = db.session.get(Companion, 2)
        hireling.image_url = 'https://example.com/ada.png'
        hireling.custom_image = True
        db.session.commit()
    tokens = clients[1].get(path).json['tokens']
    assert tokens[1]['portrait'] == '/static/images/portraits/default-portrait.webp'
    assert tokens[2]['portrait'] == 'https://example.com/ada.png'
    with app.app_context():
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert [t['name'] for t in clients[1].get(path).json['tokens']] == ['Ada', 'Pip']
    assert clients[2].get(path).status_code == 403


def test_laser_only_reaches_current_party_and_does_not_save(shared):
    app, clients, sockets = shared
    packet = {'party_id': 1, 'generation': 1, 'pointer': {'x': 10, 'y': 20, 'tool': 'laser'}, 'button': 'down'}
    sockets[2].emit('whiteboard_laser', packet)
    received = sockets[1].get_received()
    assert len(received) == 1 and received[0]['name'] == 'whiteboard_laser'
    assert received[0]['args'][0]['pointer'] == packet['pointer']
    assert received[0]['args'][0]['username'] == 'map2'
    assert all(sockets[i].get_received() == [] for i in (2, 3, 4))
    with app.app_context():
        assert PartyMap.query.count() == 0
    sockets[3].emit('whiteboard_laser', packet)
    sockets[2].emit('whiteboard_laser', {**packet, 'generation': 9})
    sockets[2].emit('whiteboard_laser', {**packet, 'pointer': {'x': float('nan'), 'y': 0, 'tool': 'laser'}})
    assert sockets[1].get_received() == []
    app.config['WTF_CSRF_ENABLED'] = True
    sockets[2].emit('whiteboard_laser', packet)
    assert sockets[1].get_received() == []
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        from app.models import Character
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    for sock in sockets.values(): sock.get_received()
    sockets[2].emit('whiteboard_laser', packet)
    assert sockets[1].get_received() == []
    sockets[1].emit('whiteboard_laser', packet)
    assert sockets[2].get_received() == []


def test_laser_has_its_own_bounded_rate(shared):
    _, _, sockets = shared
    packet = {'party_id': 1, 'generation': 1, 'pointer': {'x': 1, 'y': 2, 'tool': 'laser'}, 'button': 'down'}
    # Pin the limiter clock so a test cannot straddle its one-second window.
    from unittest.mock import patch
    with patch('app.lib.socket_rate_limit.monotonic', return_value=100):
        for _ in range(45): sockets[2].emit('whiteboard_laser', packet)
    assert len(sockets[1].get_received()) == 40



def test_socket_delta_omits_unchanged_images_and_preserves_order():
    from app.lib.whiteboard import board_update
    from copy import deepcopy
    image = {'id': 'image', 'type': 'image', 'x': 0, 'fileId': 'f'}
    before = {'generation': 1, 'version': 1, 'fog_version': 0, 'fog': {},
              'drawing': {'elements': [image, {'id': 'removed'}], 'files': {'f': {'dataURL': 'large image'}}}}
    after = deepcopy(before); after['version'] = 2
    after['drawing']['elements'] = [{**image, 'x': 240}]
    delta = board_update(before, after)['drawing']
    assert delta['files'] == {} and delta['order'] == ['image']
    assert delta['elements'][0]['x'] == 240 and delta['base_version'] == 1
    after['generation'] = 2
    assert board_update(before, after) == {'state': after}

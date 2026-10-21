"""Whiteboard v2: access, save races and private viewer projections."""
from copy import deepcopy
import pytest
from app import socketio
from app.models import db, Character, Companion, WhiteboardScene, WhiteboardToken, Party, PartyMap, ContentEntry, PartyPresentation, PointcrawlMap, MapNode
from test_shared_map import shared, DRAWING, image_drawing

BASE = '/party/1/shared-map'


def snapshot(client, scene_id=None):
    response = client.get(BASE + '/scene', query_string={'scene_id': scene_id} if scene_id else {})
    assert response.status_code == 200, response.text
    return response.json


def payload(state, **values):
    return {**{key: state[key] for key in ('protocol', 'scene_id', 'activation_version', 'generation')}, **values}


def post(client, path, state, **values):
    return client.post(BASE + path, json=payload(state, **values))


def test_scene_preparation_switch_and_stale_writes(shared):
    app, clients, sockets = shared
    a = snapshot(clients[1])
    assert post(clients[2], '/scene', a, version=0, drawing=DRAWING).status_code == 200
    b = post(clients[1], '/scenes', a, action='create', name='SECRET ROOM').json
    assert b['scene_id'] != a['scene_id']
    assert snapshot(clients[2])['drawing']['elements'][0]['x'] == 20
    assert clients[2].get(BASE + '/scenes').status_code == 403
    assert clients[2].get(BASE + '/scene', query_string={'scene_id': b['scene_id']}).status_code == 409
    assert clients[2].get(BASE + '/scene', query_string={'scene_id': 999999}).json == {'reason': 'active_changed'}
    for client in sockets.values(): client.get_received()
    assert post(clients[1], '/scene', b, version=0, drawing=DRAWING).status_code == 200
    assert sockets[2].get_received() == []
    activated = post(clients[1], '/scenes', b, action='activate').json
    assert snapshot(clients[2])['scene_id'] == b['scene_id']
    assert post(clients[2], '/scene', a, version=1, drawing={'elements': [], 'files': {}}).json == {'reason': 'active_changed'}
    a2 = post(clients[1], '/scenes', snapshot(clients[1], a['scene_id']), action='activate').json
    assert a2['activation_version'] == 2
    assert post(clients[2], '/scene', a, version=1, drawing=DRAWING).status_code == 409
    assert post(clients[1], '/scenes', a2, action='delete').json == {'reason': 'active_scene'}
    assert post(clients[1], '/scenes', snapshot(clients[1], b['scene_id']), action='delete').status_code == 200


def test_protocol_revisions_and_fog_are_independent(shared):
    _, clients, _ = shared
    client = clients[1]
    state = snapshot(client)
    assert client.post(BASE + '/scene', json={'version': 0, 'drawing': DRAWING}).json == {'reason': 'reload_required'}
    assert post(client, '/scene', state, version=0, drawing=DRAWING).status_code == 200
    assert post(client, '/fog', state, fog_version=0, operation={'id': 'fog', 'type': 'hide_all'}).status_code == 200
    assert post(client, '/fog', state, fog_version=0, operation={'id': 'fog', 'type': 'hide_all'}).status_code == 200
    final = snapshot(client)
    assert final['version'] == 1 and final['fog_version'] == 1
    assert final['drawing']['elements'][0]['x'] == 20
    query = {key: final[key] for key in ('scene_id', 'version', 'generation', 'fog_version', 'tokens_version', 'encounter_version', 'markers_version', 'activation_version')}
    query['view_revision'] = final['view_revision']
    assert client.get(BASE + '/scene', query_string=query).status_code == 204
    assert post(client, '/scene', state, version=0, drawing=DRAWING).status_code == 409


def test_showing_current_scene_does_not_switch_players_again(shared):
    _, clients, sockets = shared
    state = snapshot(clients[1])
    for client in sockets.values():
        client.get_received()
    response = post(clients[1], '/scenes', state, action='activate')
    assert response.status_code == 200
    assert response.json['activation_version'] == state['activation_version']
    assert snapshot(clients[2])['scene_id'] == state['scene_id']
    assert all(client.get_received() == [] for client in sockets.values())
    assert post(clients[2], '/scene', state, version=0, drawing=DRAWING).status_code == 200
    assert post(clients[1], '/scenes', {**state, 'activation_version': 999}, action='activate').json == {'reason': 'active_changed'}


def create_token(client, state, image, actor, suffix='one'):
    drawing = deepcopy(image)
    token_id = f'actor-{actor.replace(":", "-")}-{suffix}'
    drawing['elements'][0]['id'] = token_id
    result = post(client, '/placed-tokens', state, tokens_version=state['tokens_version'],
        operations=[dict(action='create', id=token_id, actor_id=actor, drawing=drawing)])
    assert result.status_code == 200, result.text
    return result.json, token_id


def test_tokens_hidden_and_ownership_enforced_on_server(shared, image_drawing):
    app, clients, sockets = shared
    with app.app_context():
        db.session.add(Companion(id=10, kind='monster', party_id=1, name='SECRET MONSTER', notes='SECRET NOTES', role='Goblin', shared=False, hp=4, hp_max=4))
        db.session.add(Companion(id=11, kind='monster', party_id=1, name='SECOND MONSTER', role='Goblin', shared=False, hp=6, hp_max=6))
        db.session.commit()
    state = snapshot(clients[1])
    state, monster = create_token(clients[1], state, image_drawing, 'companion:10')
    player = snapshot(clients[2])
    assert player['tokens'] == [] and player['drawing']['files'] == {}
    assert 'SECRET' not in str(player)
    assert clients[2].get(BASE + '/actors').json['portraits'] == []
    assert clients[2].get(BASE + '/actors/10').status_code == 404
    assert 'SECRET' not in str(sockets[2].get_received())
    forged = post(clients[2], '/placed-tokens', player, tokens_version=player['tokens_version'],
        operations=[dict(action='update', id=monster, geometry={'x': 300})])
    assert forged.status_code == 403
    assert snapshot(clients[1])['tokens_version'] == state['tokens_version']
    result = post(clients[1], '/placed-tokens', state, tokens_version=state['tokens_version'], operations=[dict(action='update', id=monster, visible=True, numbered=True)])
    assert result.status_code == 200
    player = snapshot(clients[2]); assert player['tokens'][0]['name'] == 'Monster 1'
    assert player['tokens'][0]['sheet_url'] is None
    state, own = create_token(clients[2], player, image_drawing, '1')
    assert post(clients[2], '/placed-tokens', state, tokens_version=state['tokens_version'], operations=[dict(action='update', id=own, geometry={'x': 444})]).status_code == 200
    state = snapshot(clients[1])
    assert post(clients[1], '/placed-tokens', state, tokens_version=state['tokens_version'], operations=[dict(action='update', id=own, geometry={'x': 555})]).status_code == 200
    forged_drawing = deepcopy(image_drawing); forged_drawing['elements'][0]['id'] = monster
    assert post(clients[2], '/scene', snapshot(clients[2]), version=0, drawing=forged_drawing).status_code == 400


def test_encounter_per_scene_permissions_and_duplicate(shared, image_drawing):
    _, clients, _ = shared
    state, token = create_token(clients[2], snapshot(clients[2]), image_drawing, '1')
    state = post(clients[1], '/encounter', state, encounter_version=0, action='add', actor_id='1').json
    assert post(clients[2], '/encounter', state, encounter_version=1, action='next_round').status_code == 403
    state = post(clients[2], '/encounter', state, encounter_version=1, action='acted', actor_id='1', acted=True).json
    assert state['encounter']['participants'][0]['acted'] is True
    duplicate = post(clients[1], '/scenes', state, action='duplicate', name='Copy').json
    assert duplicate['tokens'][0]['actor_id'] == '1'
    assert duplicate['encounter']['round'] == 1 and duplicate['encounter']['participants'][0]['acted'] is False
    assert snapshot(clients[1], state['scene_id'])['encounter']['participants'][0]['acted'] is True
    assert post(clients[2], '/encounter', state, encounter_version=1, action='acted', actor_id='1', acted=False).status_code == 409


def test_readding_an_encounter_actor_preserves_their_turn_and_round(shared):
    _, clients, _ = shared
    state = snapshot(clients[1])
    for action, values in [('add', {'actor_id': '1'}), ('next_round', {}), ('acted', {'actor_id': '1', 'acted': True})]:
        response = post(clients[1], '/encounter', state, encounter_version=state['encounter_version'], action=action, **values)
        assert response.status_code == 200
        state = response.json
    before = deepcopy(state['encounter'])
    assert before['round'] == 2 and before['participants'][0]['acted'] is True
    response = post(clients[1], '/encounter', state, encounter_version=state['encounter_version'], action='add', actor_id='1')
    assert response.status_code == 200
    assert response.json['encounter'] == before


def test_material_projections_and_import_do_not_bake_private_titles(shared):
    app, clients, _ = shared
    with app.app_context():
        room = ContentEntry(owner_id=1, category='location', title='PRIVATE TITLE', body='PRIVATE BODY')
        root = ContentEntry(owner_id=1, category='dungeon', title='Dungeon')
        source = PointcrawlMap(id=100, entry=root, drawing=deepcopy(DRAWING))
        db.session.add_all([source, MapNode(map=source, entry=room, number=1, x=10, y=20)])
        db.session.commit(); room_id = room.id
    a = snapshot(clients[1])
    preview = clients[1].get(BASE + '/sources/100').json
    imported = post(clients[1], '/import', a, source_id=100, digest=preview['digest'], cover=True).json
    assert imported['scene_id'] != a['scene_id']
    assert imported['markers'][0]['title'] == 'PRIVATE TITLE'
    assert 'PRIVATE' not in str(imported['drawing'])
    active = post(clients[1], '/scenes', imported, action='activate').json
    assert snapshot(clients[2])['markers'] == []
    with app.app_context():
        db.session.add(PartyPresentation(entry=db.session.get(ContentEntry, room_id), party_id=1, title='Known room', body='Known prose', published=True))
        db.session.commit()
    player = snapshot(clients[2]); assert player['markers'][0]['title'] == 'Known room'
    assert 'PRIVATE' not in str(player)
    assert f'party_id=1' in active['markers'][0]['reveal_url']
    with app.app_context():
        db.session.query(PartyPresentation).filter_by(entry_id=room_id).one().published = False
        db.session.commit()
    assert snapshot(clients[2])['markers'] == []
    # Replacing is explicit and refuses changes made since the preview.
    assert post(clients[1], '/import', active, mode='replace', version=99, fog_version=0, tokens_version=0,
        markers_version=0, encounter_version=0, source_id=100, digest=preview['digest'], cover=False).status_code == 409


def test_presence_multitab_visibility_scope_and_membership(shared):
    app, clients, sockets = shared
    state = snapshot(clients[2])
    def join(socket, visible):
        return socket.emit('whiteboard_presence', dict(party_id=1, visible=visible, **payload(state)), callback=True)
    assert join(sockets[2], True) == {'ok': True}
    assert join(sockets[3], True) == {'error': 'access_denied'}
    assert clients[1].get(BASE + '/presence').json['members'][0]['visible'] is True
    second = socketio.test_client(app, flask_test_client=clients[2])
    try:
        assert join(second, False) == {'ok': True}
        assert len(clients[1].get(BASE + '/presence').json['members']) == 1
        join(sockets[2], False)
        assert clients[1].get(BASE + '/presence').json['members'][0]['visible'] is False
        second.disconnect()
        assert len(clients[1].get(BASE + '/presence').json['members']) == 1
        draft = post(clients[1], '/scenes', state, action='create', name='PRIVATE').json
        assert clients[1].get(BASE + '/presence', query_string={'scene_id': draft['scene_id']}).json['members'] == []
        with app.app_context():
            db.session.get(Character, 1).party_id = None; db.session.commit()
        assert clients[1].get(BASE + '/presence').json['members'] == []
    finally:
        if second.is_connected(): second.disconnect()


def test_private_scene_laser_only_reaches_warden(shared):
    _, clients, sockets = shared
    draft = post(clients[1], '/scenes', snapshot(clients[1]), action='create', name='Draft').json
    for client in sockets.values(): client.get_received()
    sockets[1].emit('whiteboard_laser', dict(party_id=1, pointer={'x': 1, 'y': 2, 'tool': 'laser'}, button='down', **payload(draft)))
    assert sockets[2].get_received() == []


def test_actor_actions_update_real_sheets_and_preserve_permissions(shared, image_drawing):
    app, clients, _ = shared
    with app.app_context():
        char = db.session.get(Character, 1)
        char.hp = char.hp_max = 6
        db.session.add_all([Companion(id=10, kind='monster', party_id=1, name='Wolf 1', hp=4, hp_max=4, shared=False),
                            Companion(id=11, kind='monster', party_id=1, name='Wolf 2', hp=7, hp_max=7, shared=False)])
        db.session.commit()
    state = snapshot(clients[1])
    def stat(user, key, field, value, **extra):
        return clients[user].post(BASE + '/actor-stat', data={**payload(state), 'actor_id': key, 'stat': field, 'value': value, **extra})
    assert stat(2, '1', 'hp', 3).status_code == 204
    assert stat(1, '1', 'deprived', 1).status_code == 204
    assert stat(2, 'companion:10', 'hp', 1).status_code == 403
    assert stat(1, 'companion:10', 'hp', 1).status_code == 204
    assert stat(2, '1', 'hp', 99).status_code == 400
    assert stat(2, '1', 'notes', 'forged').status_code == 400
    assert stat(1, '1', 'hp', 1, generation='bad').status_code == 400
    with app.app_context():
        assert db.session.get(Character, 1).hp == 3 and db.session.get(Character, 1).deprived is True
        assert db.session.get(Companion, 10).hp == 1 and db.session.get(Companion, 11).hp == 7


def test_markers_move_and_follow_revoked_publications_even_with_revision_poll(shared):
    app, clients, _ = shared
    with app.app_context():
        entry = ContentEntry(owner_id=1, category='location', title='Secret title', body='secret')
        db.session.add(entry); db.session.commit(); key = entry.id
    state = snapshot(clients[1])
    result = post(clients[1], '/markers', state, markers_version=0, action='create', entry_id=key, x=5, y=8)
    assert result.status_code == 200
    marker = result.json['markers'][0]
    assert post(clients[2], '/markers', snapshot(clients[2]), markers_version=1, action='update', id=marker['id'], x=10, y=10).status_code == 403
    updated = post(clients[1], '/markers', result.json, markers_version=1, action='update', id=marker['id'], x=100, y=200).json
    assert (updated['markers'][0]['x'], updated['markers'][0]['y']) == (100, 200)
    with app.app_context():
        db.session.add(PartyPresentation(entry=db.session.get(ContentEntry,key), party_id=1, title='Public title', body='Public prose', published=True))
        db.session.commit()
    before = snapshot(clients[2])
    assert before['markers'][0]['title'] == 'Public title'
    with app.app_context():
        db.session.query(PartyPresentation).one().published = False; db.session.commit()
    query = {key: before[key] for key in ('scene_id', 'version', 'generation', 'fog_version', 'tokens_version', 'encounter_version', 'markers_version', 'activation_version', 'view_revision')}
    changed = clients[2].get(BASE + '/scene', query_string=query)
    assert changed.status_code == 200 and changed.json['markers'] == []
    assert 'Secret title' not in changed.text


def test_missing_context_csrf_and_cross_party_access_fail_closed(shared):
    app, clients, _ = shared
    state = snapshot(clients[1])
    for path in ('/placed-tokens','/encounter','/markers','/scenes','/import','/fog'):
        assert clients[1].post(BASE+path,json={}).status_code == 409
        assert clients[3].post(BASE+path,json=payload(state)).status_code == 403
    with app.app_context():
        other = WhiteboardScene(party_id=2,name='OTHER PARTY SECRET');db.session.add(other);db.session.commit(); scene_id=other.id
    assert clients[1].get(BASE+'/scene',query_string={'scene_id':scene_id}).status_code == 404
    app.config['WTF_CSRF_ENABLED'] = True
    for path in ('/placed-tokens','/encounter','/markers','/scenes','/import','/fog'):
        assert clients[1].post(BASE+path,json=payload(state)).status_code == 400


def test_unplaced_owned_encounter_participant_can_act(shared):
    _, clients, _ = shared
    state=post(clients[1],'/encounter',snapshot(clients[1]),encounter_version=0,action='add',actor_id='1').json
    assert post(clients[2],'/encounter',state,encounter_version=1,action='acted',actor_id='1',acted=True).status_code == 200


def test_committed_changes_survive_notification_outage(shared, monkeypatch):
    app, clients, _ = shared
    state = snapshot(clients[1])
    def unavailable(*args, **kwargs):
        raise RuntimeError('transport unavailable')
    monkeypatch.setattr(socketio, 'emit', unavailable)
    created = post(clients[1], '/scenes', state, action='create', name='Saved during outage')
    assert created.status_code == 200
    assert post(clients[1], '/scenes', created.json, action='activate').status_code == 200
    assert snapshot(clients[2])['name'] == 'Saved during outage'

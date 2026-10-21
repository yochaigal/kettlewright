"""Version 2 Whiteboard APIs. Private state is always projected per viewer."""
from copy import deepcopy
from uuid import uuid4
import math
import json
import re

from flask import Blueprint, abort, current_app, jsonify, request, url_for
from flask_login import current_user, login_required
from app.models import db, PartyMap, WhiteboardScene, WhiteboardToken, WhiteboardMarker, Character, ContentEntry
from app.lib.whiteboard import board_state, board_update, drawing_value, protect_locked_elements, integer, empty_fog, fog_operation
from app.lib.whiteboard_scenes import (context, claim, commit_scene, conflict, projection,
    actor_map, can_control, can_edit, imported_snapshot, viewer_revision)

whiteboard = Blueprint('whiteboard', __name__)
BASE = '/party/<int:party_id>/shared-map'


@whiteboard.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@whiteboard.errorhandler(409)
def changed(error):
    db.session.rollback()
    return jsonify(reason=error.description), 409


def data():
    from app.blueprints.party import _board_data
    return _board_data()


def validate_scene_size(scene, drawing=None):
    from app.lib.map_drawing import MAX_DRAWING_BYTES
    drawing = scene.drawing if drawing is None else drawing
    remaining = [token for token in scene.tokens if token not in db.session.deleted]
    if len(drawing['elements']) + len(remaining) > 2000 or len(scene.markers) > 2000:
        abort(400, 'A scene supports up to 2000 drawing elements and tokens.')
    files = dict(drawing['files'])
    for token in remaining:
        for key, value in token.files.items():
            if key in files and any(files[key].get(field) != value.get(field) for field in ('mimeType', 'dataURL')):
                abort(400, 'Conflicting drawing image ID.')
            files[key] = value
    if len(json.dumps({'elements': drawing['elements'], 'files': files})) + sum(len(json.dumps(t.element)) for t in remaining) > MAX_DRAWING_BYTES:
        abort(400, 'Scene exceeds 12 MB.')


def emit_update(event, payload, recipients):
    from app import socketio
    for user_id in recipients:
        try:
            socketio.emit(event, payload, room=f'user_{user_id}')
        except Exception:
            current_app.logger.exception('Unable to publish Whiteboard update')


def notify_catalog(party):
    emit_update('whiteboard_scenes_changed', {'party_id': party.id}, {party.owner})


def state(party_id):
    payload = data() if request.method == 'POST' else None
    party, board, scene = context(party_id, payload, write=payload is not None)
    if payload is None:
        revisions = {'version': scene.version, 'generation': scene.generation, 'fog_version': scene.fog_version,
            'tokens_version': scene.tokens_version, 'encounter_version': scene.encounter_version,
            'markers_version': scene.markers_version, 'activation_version': board.activation_version}
        if request.args.get('view_revision') == viewer_revision(party, scene) and all(request.args.get(key, type=int) == value for key, value in revisions.items()):
            return '', 204
        return jsonify(projection(party, board, scene))
    version = integer(payload, 'version')
    drawing = drawing_value(payload.get('drawing'), stored_files=scene.drawing['files'], reuse_files=payload.get('reuse_files'))
    if 'drawing' not in payload or any(e['id'].startswith(('actor-', 'wb-token-', 'wb-marker-')) for e in drawing['elements']):
        abort(400, 'Use the token API for managed tokens.')
    if current_user.id != party.owner:
        protect_locked_elements(scene.drawing, drawing)
    validate_scene_size(scene, drawing)
    before = board_state(scene)
    claim(scene, 'version', version)
    scene.drawing = drawing
    after = {**before, 'version': version + 1, 'drawing': drawing}
    commit_scene(scene, drawing_update=board_update(before, after))
    return jsonify(version=version + 1)


@whiteboard.route(BASE + '/scenes', methods=['GET', 'POST'])
@login_required
def scenes(party_id):
    payload = data() if request.method == 'POST' else None
    party, board, scene = context(party_id, payload, owner=True, write=payload is not None)
    if payload is None:
        return jsonify(active_scene_id=board.active_scene_id, activation_version=board.activation_version,
            scenes=[{'id': row.id, 'name': row.name} for row in WhiteboardScene.query.filter_by(party_id=party.id).order_by(WhiteboardScene.id)])
    action = payload.get('action')
    if action in ('create', 'rename', 'duplicate'):
        name = payload.get('name', scene.name + ' (copy)' if action == 'duplicate' else '')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
            abort(400, 'Enter a scene name (up to 100 characters).')
        if action == 'rename':
            scene.name = name.strip()
        else:
            new = WhiteboardScene(party_id=party.id, name=name.strip())
            if action == 'duplicate':
                new.drawing, new.fog = deepcopy(scene.drawing), deepcopy(scene.fog)
                new.encounter = {'round': 1, 'participants': [{**p, 'acted': False} for p in scene.encounter['participants']]}
            db.session.add(new)
            db.session.flush()
            if action == 'duplicate':
                for token in scene.tokens:
                    db.session.add(WhiteboardToken(scene=new, id=token.id, actor_key=token.actor_key,
                        element=deepcopy(token.element), files=deepcopy(token.files), visible=token.visible, numbered=token.numbered))
                for marker in scene.markers:
                    db.session.add(WhiteboardMarker(scene=new, id=marker.id, entry_id=marker.entry_id,
                        x=marker.x, y=marker.y, number=marker.number))
            scene = new
    elif action == 'delete':
        # Lock the registry against concurrent activation/deletion.
        if not PartyMap.query.filter(PartyMap.party_id == party.id, PartyMap.active_scene_id != scene.id).update(
                {'activation_version': PartyMap.activation_version}, synchronize_session=False):
            conflict('active_scene')
        if WhiteboardScene.query.filter_by(party_id=party.id).count() <= 1:
            conflict('last_scene')
        db.session.delete(scene)
        db.session.commit()
        notify_catalog(party)
        return jsonify(deleted=True)
    elif action == 'activate':
        expected = integer(payload, 'activation_version')
        db.session.refresh(board)
        if expected != board.activation_version:
            conflict('active_changed')
        if board.active_scene_id == scene.id:
            return jsonify(projection(party, board, scene))
        if not PartyMap.query.filter_by(party_id=party.id, activation_version=expected).update(
                {'active_scene_id': scene.id, 'activation_version': expected + 1}, synchronize_session=False):
            conflict('active_changed')
    else:
        abort(400)
    scene = commit_scene(scene)
    notify_catalog(party)
    if action == 'activate':
        from app.socket_events import party_recipient_ids
        emit_update('whiteboard_active_changed', {'party_id': party.id}, party_recipient_ids(party))
    return jsonify(projection(party, db.session.get(PartyMap, party.id), scene))


def fog(party_id):
    payload = data()
    party, board, scene = context(party_id, payload, owner=True, write=True)
    operation = payload.get('operation')
    value, applied = fog_operation(scene.fog, operation)
    if applied:
        version = integer(payload, 'fog_version')
        claim(scene, 'fog_version', version)
        scene.fog = value
        commit_scene(scene, drawing_update={'fog': value})
    return jsonify(fog=scene.fog, fog_version=scene.fog_version, generation=scene.generation)


def import_map(party_id):
    from app.blueprints.party import _board_source
    payload = data()
    party, board, scene = context(party_id, payload, owner=True, write=True)
    source = _board_source(integer(payload, 'source_id'))
    drawing, digest, markers = imported_snapshot(source)
    if payload.get('digest') != digest:
        conflict('source_changed')
    if type(payload.get('cover')) is not bool or payload.get('mode', 'new') not in ('new', 'replace'):
        abort(400)
    if payload.get('mode', 'new') == 'new':
        scene = WhiteboardScene(party_id=party.id, name=source.entry.title[:100] or 'Map')
        db.session.add(scene)
        db.session.flush()
    else:
        expected = {key: integer(payload, key) for key in ('version', 'fog_version', 'tokens_version', 'markers_version', 'encounter_version')}
        if not WhiteboardScene.query.filter_by(id=scene.id, **expected).update(
                {'generation': scene.generation + 1, 'version': scene.version + 1,
                 'fog_version': scene.fog_version + 1, 'tokens_version': scene.tokens_version + 1,
                 'markers_version': scene.markers_version + 1, 'encounter_version': scene.encounter_version + 1}, synchronize_session=False):
            conflict()
        for item in list(scene.tokens) + list(scene.markers):
            db.session.delete(item)
        scene.encounter = {'round': 1, 'participants': []}
    scene.drawing, scene.fog = drawing, {**empty_fog(), 'enabled': payload['cover']}
    for marker in markers:
        db.session.add(WhiteboardMarker(scene=scene, **marker))
    scene = commit_scene(scene)
    notify_catalog(party)
    return jsonify(projection(party, board, scene))


@whiteboard.post(BASE + '/placed-tokens')
@login_required
def tokens(party_id):
    payload = data()
    party, board, scene = context(party_id, payload, write=True)
    operations = payload.get('operations')
    if not isinstance(operations, list) or not 1 <= len(operations) <= 200:
        abort(400)
    actors = actor_map(party)
    claim(scene, 'tokens_version', integer(payload, 'tokens_version'))
    for operation in operations:
        if not isinstance(operation, dict):
            abort(400)
        token_id, action = operation.get('id'), operation.get('action')
        if not isinstance(token_id, str) or not re.fullmatch(r'actor-(?:companion-)?\d+-[a-zA-Z0-9_-]{1,140}', token_id):
            abort(400)
        token = db.session.get(WhiteboardToken, (scene.id, token_id))
        if action == 'create':
            if token or len(scene.tokens) >= 2000:
                conflict()
            key = str(operation.get('actor_id'))
            actor = actors.get(key)
            if actor is None or not can_control(party, actor):
                abort(403)
            prefix = 'actor-' + key.replace(':', '-') + '-'
            if not token_id.startswith(prefix):
                abort(400)
            clean = drawing_value(operation.get('drawing'))
            if len(clean['elements']) != 1 or clean['elements'][0]['type'] != 'image' or clean['elements'][0]['id'] != token_id:
                abort(400)
            element = clean['elements'][0]
            # Control/visibility are server-owned; no client-provided customData.
            element['locked'] = False
            token = WhiteboardToken(scene=scene, id=token_id, actor_key=key, element=element,
                files=clean['files'], visible=getattr(actor, 'kind', '') != 'monster')
            db.session.add(token)
        elif action in ('update', 'delete'):
            if token is None:
                conflict()
            actor = actors.get(token.actor_key)
            if actor is None or not can_control(party, actor) or not token.visible and party.owner != current_user.id:
                abort(403)
            if action == 'delete':
                db.session.delete(token)
                continue
            element = deepcopy(token.element)
            geometry = operation.get('geometry', {})
            if not isinstance(geometry, dict) or set(geometry) - {'x', 'y', 'width', 'height', 'angle'}:
                abort(400)
            element.update(geometry)
            element['version'] = element.get('version', 1) + 1
            token.element = drawing_value({'elements': [element], 'files': token.files}, stored_files=token.files)['elements'][0]
            for field in ('visible', 'numbered'):
                if field in operation:
                    if party.owner != current_user.id:
                        abort(403)
                    if type(operation[field]) is not bool:
                        abort(400)
                    setattr(token, field, operation[field])
        else:
            abort(400)
    validate_scene_size(scene)
    scene = commit_scene(scene)
    return jsonify(projection(party, board, scene))


@whiteboard.route(BASE + '/encounter', methods=['POST'])
@login_required
def encounter(party_id):
    payload = data()
    party, board, scene = context(party_id, payload, write=True)
    actors = actor_map(party)
    value = deepcopy(scene.encounter)
    action, key = payload.get('action'), payload.get('actor_id')
    warden = party.owner == current_user.id
    if action in ('add', 'remove', 'next_round', 'reset') and not warden:
        abort(403)
    if action in ('add', 'remove'):
        if key not in actors:
            abort(400)
        if action == 'remove':
            value['participants'] = [item for item in value['participants'] if item['actor_id'] != key]
        elif not any(item['actor_id'] == key for item in value['participants']):
            value['participants'].append({'actor_id': key, 'acted': False})
    elif action == 'acted':
        actor = actors.get(key)
        if actor is None or not can_control(party, actor) or type(payload.get('acted')) is not bool:
            abort(403)
        placements = [t for t in scene.tokens if t.actor_key == key]
        if not warden and placements and not any(t.visible for t in placements):
            abort(403)
        item = next((p for p in value['participants'] if p['actor_id'] == key), None)
        if item is None:
            abort(404)
        item['acted'] = payload['acted']
    elif action in ('next_round', 'reset'):
        value['round'] = value['round'] + 1 if action == 'next_round' else 1
        for item in value['participants']:
            item['acted'] = False
    else:
        abort(400)
    claim(scene, 'encounter_version', integer(payload, 'encounter_version'))
    scene.encounter = value
    scene = commit_scene(scene)
    return jsonify(projection(party, board, scene))


@whiteboard.route(BASE + '/markers', methods=['GET', 'POST'])
@login_required
def markers(party_id):
    payload = data() if request.method == 'POST' else None
    party, board, scene = context(party_id, payload, owner=True, write=payload is not None)
    if payload is None:
        campaign_ids = [link.campaign_id for link in party.campaign_links]
        entries = ContentEntry.query.filter(ContentEntry.owner_id == party.owner,
            db.or_(ContentEntry.campaign_id.is_(None), ContentEntry.campaign_id.in_(campaign_ids))).order_by(ContentEntry.title)
        return jsonify(entries=[{'id': e.id, 'title': e.title} for e in entries])
    claim(scene, 'markers_version', integer(payload, 'markers_version'))
    action = payload.get('action')
    if action == 'create':
        if len(scene.markers) >= 2000:
            abort(400, 'A scene supports up to 2000 material markers.')
        entry = db.get_or_404(ContentEntry, integer(payload, 'entry_id'))
        if entry.owner_id != party.owner or entry.campaign_id and entry.campaign_id not in {link.campaign_id for link in party.campaign_links}:
            abort(403)
        x, y = payload.get('x'), payload.get('y')
        if any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1000000 for n in (x, y)):
            abort(400)
        db.session.add(WhiteboardMarker(scene=scene, id=uuid4().hex, entry_id=entry.id, x=x, y=y, number=''))
    elif action in ('delete', 'update'):
        marker = db.session.get(WhiteboardMarker, (scene.id, payload.get('id')))
        if marker is None:
            abort(404)
        if action == 'delete':
            db.session.delete(marker)
        else:
            x, y = payload.get('x'), payload.get('y')
            if any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1000000 for n in (x, y)):
                abort(400)
            marker.x, marker.y = x, y
    else:
        abort(400)
    scene = commit_scene(scene)
    return jsonify(projection(party, board, scene))


@whiteboard.post(BASE + '/actor-stat')
@login_required
def actor_stat(party_id):
    from flask_wtf import FlaskForm
    from app.lib.quick_stats import save_character_stat, save_current_stat
    if not FlaskForm().validate_on_submit():
        abort(400)
    party, board, scene = context(party_id, dict(request.form, protocol=2,
        scene_id=request.form.get('scene_id'), activation_version=request.form.get('activation_version', type=int),
        generation=request.form.get('generation', type=int)), write=True)
    actor = actor_map(party).get(request.form.get('actor_id'))
    if actor is None or not can_edit(actor):
        abort(403)
    result = save_character_stat(actor) if isinstance(actor, Character) else save_current_stat(actor)
    from app.socket_events import party_recipient_ids
    emit_update('party_actors_changed', {'party_id': party.id}, party_recipient_ids(party))
    return result


@whiteboard.get(BASE + '/presence')
@login_required
def presence(party_id):
    from app.models import User
    from app.blueprints.party import party_characters
    from app.socket_events import party_recipient_ids
    party, board, scene = context(party_id)
    store = current_app.extensions['whiteboard_presence']
    members, characters = {}, party_characters(party)
    allowed = party_recipient_ids(party)
    for record in store.records():
        if record['party_id'] != party.id or record['scene_id'] != scene.id or record['user_id'] not in allowed:
            continue
        user_id = record['user_id']
        members[user_id] = members.get(user_id, False) or record['visible']
    result = []
    for user_id, visible in sorted(members.items(), key=lambda item: (item[0] != party.owner, item[0])):
        user = db.session.get(User, user_id)
        if user is None:
            continue
        owned = [c for c in characters if c.owner == user_id]
        portrait = None
        if owned and user_id != party.owner:
            c = owned[0]
            portrait = c.image_url if c.custom_image else url_for('static', filename='images/portraits/' + (c.image_url or 'default-portrait.webp'))
            from urllib.parse import urlsplit
            try:
                parsed = urlsplit(portrait or '')
                if parsed.scheme not in ('', 'https', 'http') or parsed.username or parsed.password:
                    portrait = None
            except ValueError:
                portrait = None
        result.append({'id': user_id, 'username': user.username, 'characters': [c.name for c in owned],
            'warden': user_id == party.owner, 'portrait': portrait, 'visible': visible})
    return jsonify(members=result)

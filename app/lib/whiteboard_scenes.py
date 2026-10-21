"""Scene authorization, viewer projections and versioned Whiteboard writes."""
from copy import deepcopy
import hashlib
import json
import re
from uuid import uuid4

from flask import abort, current_app, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.models import (db, Party, PartyMap, Character, Companion, WhiteboardScene,
                        WhiteboardToken, WhiteboardMarker, ContentEntry)
from app.lib.whiteboard import board_state, integer
from app.lib.map_drawing import EMPTY_DRAWING
from app.socket_events import party_recipient_ids

PROTOCOL = 2


def conflict(reason='changed'):
    abort(409, description=reason)


def actor_map(party):
    from app.blueprints.party import party_characters
    actors = {}
    for character in party_characters(party):
        actors[str(character.id)] = character
        actors.update((f'companion:{pet.id}', pet) for pet in character.pets)
    for companion in party.party_companions:
        actors[f'companion:{companion.id}'] = companion
        if companion.kind == 'hireling':
            actors.update((f'companion:{pet.id}', pet) for pet in companion.pets)
    return actors


def can_control(party, actor):
    from app.lib.companions import can_manage
    return party.owner == current_user.id or (actor.owner == current_user.id if isinstance(actor, Character) else can_manage(actor))


def can_edit(actor):
    from app.lib.character_permissions import can_edit_character
    from app.lib.companions import can_manage
    return can_edit_character(actor) if isinstance(actor, Character) else can_manage(actor)


def ensure_board(party):
    board = db.session.get(PartyMap, party.id)
    if board is not None and board.active_scene_id:
        return board
    # Existing installations are migrated in Alembic. Also support parties that
    # have never opened Whiteboard, and legacy fixture/import-created rows.
    try:
        if board is None:
            board = PartyMap(party_id=party.id, drawing=deepcopy(EMPTY_DRAWING), version=0)
            db.session.add(board)
        db.session.flush()
        scene = WhiteboardScene(party_id=party.id, name='Whiteboard', **board_state(board))
        db.session.add(scene)
        db.session.flush()
        actors, drawing, retained = actor_map(party), deepcopy(scene.drawing), []
        for element in drawing['elements']:
            match = re.match(r'^actor-(companion-)?(\d+)-', element['id'])
            key = ('companion:' if match[1] else '') + match[2] if match else None
            if key in actors and element.get('type') == 'image':
                file_id = element.get('fileId')
                db.session.add(WhiteboardToken(scene=scene, id=element['id'], actor_key=key,
                    element=element, files={file_id: drawing['files'][file_id]} if file_id in drawing['files'] else {}, visible=True))
            else:
                if match:
                    element['id'] = 'orphan-' + element['id']
                retained.append(element)
        used = {e.get('fileId') for e in retained}
        drawing.update(elements=retained, files={k: v for k, v in drawing['files'].items() if k in used})
        scene.drawing, board.active_scene_id = drawing, scene.id
        board.drawing = deepcopy(EMPTY_DRAWING)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        board = db.session.get(PartyMap, party.id)
        if not board or not board.active_scene_id:
            raise
    return board


def context(party_id, data=None, *, owner=False, write=False):
    party = db.get_or_404(Party, party_id)
    if current_user.id not in party_recipient_ids(party) or owner and party.owner != current_user.id:
        abort(403)
    board = ensure_board(party)
    values = data if data is not None else request.args
    raw = values.get('scene_id', board.active_scene_id)
    if isinstance(raw, bool) or not str(raw).isdigit():
        abort(400)
    scene_id = int(raw)
    if write:
        if values.get('protocol') != PROTOCOL or 'scene_id' not in values:
            conflict('reload_required')
        if party.owner == current_user.id:
            PartyMap.query.filter_by(party_id=party.id).update(
                {'activation_version': PartyMap.activation_version}, synchronize_session=False)
        else:
            # Lock the activation row through commit, so a switch cannot race a
            # player write (including A -> B -> A with an old save queue).
            revision = integer(values, 'activation_version')
            if not PartyMap.query.filter_by(party_id=party.id, active_scene_id=scene_id,
                    activation_version=revision).update({'activation_version': revision}, synchronize_session=False):
                conflict('active_changed')
    if party.owner != current_user.id and scene_id != board.active_scene_id:
        conflict('active_changed')
    scene = db.get_or_404(WhiteboardScene, scene_id)
    if scene.party_id != party.id:
        abort(404)
    if write and integer(values, 'generation') != scene.generation:
        conflict('replaced')
    return party, board, scene


def claim(scene, field, expected):
    if not WhiteboardScene.query.filter_by(id=scene.id, **{field: expected}).update(
            {field: expected + 1}, synchronize_session=False):
        conflict()


def commit_scene(scene, *, drawing_update=None):
    scene_id, party_id = scene.id, scene.party_id
    db.session.commit()
    db.session.expire_all()
    scene = db.session.get(WhiteboardScene, scene_id)
    notify_scene(scene, drawing_update=drawing_update)
    return scene


def notify_scene(scene, *, drawing_update=None):
    from app import socketio
    party = db.session.get(Party, scene.party_id)
    board = db.session.get(PartyMap, scene.party_id)
    recipients = party_recipient_ids(party) if board.active_scene_id == scene.id else {party.owner}
    event = {'party_id': party.id, 'scene_id': scene.id, 'generation': scene.generation,
        'version': scene.version, 'fog_version': scene.fog_version,
        'tokens_version': scene.tokens_version, 'encounter_version': scene.encounter_version,
        'markers_version': scene.markers_version, 'activation_version': board.activation_version}
    if drawing_update is not None:
        event['update'] = drawing_update
    for user_id in recipients:
        try:
            socketio.emit('shared_map_changed', event, room=f'user_{user_id}')
        except Exception:
            current_app.logger.exception('Unable to publish scene update')


def visible_tokens(scene, party, actors=None):
    actors = actor_map(party) if actors is None else actors
    return [token for token in scene.tokens if token.actor_key in actors and
            (party.owner == current_user.id or token.visible)]


def actor_details(party, key, actor, *, numbered=False, actors=None):
    warden = party.owner == current_user.id
    kind = 'character' if isinstance(actor, Character) else actor.kind
    public = kind != 'monster' or warden or actor.shared
    name = actor.name if public else 'Monster'
    if numbered and kind == 'monster':
        peers = sorted(a.id for a in (actors or actor_map(party)).values() if isinstance(a, Companion)
                       and a.kind == 'monster' and a.role == actor.role)
        name += f' {peers.index(actor.id) + 1}'
    sheet_url = url_for('party.shared_map_character', party_id=party.id, character_id=actor.id) if kind == 'character' else (
        url_for('party.shared_map_actor', party_id=party.id, companion_id=actor.id) if public else None)
    return {'id': key, 'name': name, 'kind': kind, 'can_control': can_control(party, actor),
            'can_edit': can_edit(actor), 'sheet_url': sheet_url}


def viewer_revision(party, scene):
    from app.models import PartyPresentation
    actors = actor_map(party)
    grants = [(key, actor.name, getattr(actor, 'kind', 'character'), getattr(actor, 'shared', True),
               can_control(party, actor), can_edit(actor)) for key, actor in sorted(actors.items())]
    publications = db.session.query(PartyPresentation.entry_id, PartyPresentation.version, PartyPresentation.published).filter_by(party_id=party.id).order_by(PartyPresentation.entry_id).all()
    return hashlib.sha256(json.dumps([grants, [list(p) for p in publications]]).encode()).hexdigest()[:24]


def projection(party, board, scene):
    from app.lib.campaigns import known_entries
    actors = actor_map(party)
    tokens = visible_tokens(scene, party, actors)
    result = {**board_state(scene), 'protocol': PROTOCOL, 'scene_id': scene.id, 'name': scene.name,
              'active_scene_id': board.active_scene_id, 'activation_version': board.activation_version,
              'tokens_version': scene.tokens_version, 'encounter_version': scene.encounter_version,
              'markers_version': scene.markers_version, 'view_revision': viewer_revision(party, scene)}
    result['tokens'] = [{**actor_details(party, token.actor_key, actors[token.actor_key], numbered=token.numbered, actors=actors),
        'id': token.id, 'actor_id': token.actor_key, 'element': token.element, 'files': token.files,
        'visible': token.visible, 'numbered': token.numbered} for token in tokens]
    placed = {token.actor_key for token in tokens}
    all_placed = {token.actor_key for token in scene.tokens}
    numbered = {token.actor_key for token in tokens if token.numbered}
    warden = party.owner == current_user.id
    result['encounter'] = {'round': scene.encounter['round'], 'participants': [
        {**actor_details(party, item['actor_id'], actors[item['actor_id']], numbered=item['actor_id'] in numbered, actors=actors), 'acted': item['acted']}
        for item in scene.encounter['participants'] if item['actor_id'] in actors and
        (warden or (item['actor_id'] not in all_placed and getattr(actors[item['actor_id']], 'kind', '') != 'monster') or item['actor_id'] in placed)]}
    known = known_entries(party.id) if scene.markers and not warden else {}
    result['markers'] = []
    for marker in scene.markers:
        entry = db.session.get(ContentEntry, marker.entry_id)
        if entry is None or entry.owner_id != party.owner or not warden and marker.entry_id not in known:
            continue
        title = entry.title if warden else known[entry.id]['title']
        result['markers'].append({'id': marker.id, 'x': marker.x, 'y': marker.y, 'number': marker.number,
            'entry_id': entry.id, 'title': title,
            'url': url_for('campaigns.edit_entry', entry_id=entry.id) if warden else url_for('campaigns.party_entry', party_id=party.id, entry_id=entry.id),
            'reveal_url': url_for('campaigns.reveal', entry_id=entry.id, party_id=party.id) if warden else None})
    return result


def imported_snapshot(source):
    from uuid import NAMESPACE_URL, uuid5
    from app.lib.whiteboard import source_snapshot
    drawing, digest = source_snapshot(source)
    namespace = uuid5(NAMESPACE_URL, f'whiteboard-source:{source.id}')
    managed = {uuid5(namespace, f'kw-{kind}-{node.id}').hex for node in source.nodes for kind in ('node', 'label')}
    drawing['elements'] = [element for element in drawing['elements'] if element['id'] not in managed]
    markers = [dict(id=uuid4().hex, entry_id=node.entry_id, x=node.x, y=node.y, number=str(node.number)) for node in source.nodes]
    return drawing, digest, markers

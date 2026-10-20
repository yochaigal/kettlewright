from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response, abort
from flask_login import login_required, current_user
from app.lib import *
from app.models import db, User, Character, Party, PartyRoll, PartyMap
from app.socket_events import party_recipient_ids, notify_roll_history_changed
from app.lib.quick_stats import save_current_stat
from app.lib.feature_access import require_party_features, user_features_enabled, party_features_enabled
from app.lib.companions import save_item_to_companion, finish_companion_transfers, can_transfer_from
from flask_wtf import FlaskForm
from app.forms import *
import json
from flask_babel import _

party = Blueprint('party', __name__)


def _board_party(party_id, owner=False):
    target = db.get_or_404(Party, party_id)
    if current_user.id not in party_recipient_ids(target) or owner and current_user.id != target.owner:
        abort(403)
    return target


def _board_campaign_access(party_id):
    require_party_features(party_id)
    if not user_features_enabled():
        abort(404)


def _board_data():
    from app.lib.map_drawing import MAX_DRAWING_BYTES
    request.max_content_length = MAX_DRAWING_BYTES + 65536
    if not FlaskForm().validate_on_submit():
        abort(400)
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)
    return data


def _board_json(data):
    response = make_response(data)
    response.headers['Cache-Control'] = 'no-store'
    return response


def _board_conflict(reason='changed'):
    response = _board_json({'reason': reason})
    response.status_code = 409
    return response


def _board_write(target, row, conditions, values):
    from sqlalchemy.exc import IntegrityError
    from app.lib.whiteboard import board_state, board_update
    previous = board_state(row)
    try:
        if row is None:
            db.session.add(PartyMap(party_id=target.id, **{**board_state(None), **values}))
        elif not PartyMap.query.filter_by(party_id=target.id, **conditions).update(values, synchronize_session=False):
            db.session.rollback()
            return False
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False
    # Expire the earlier read before publishing versions after the atomic update.
    db.session.expire_all()
    saved = db.session.get(PartyMap, target.id)
    from app import socketio
    from flask import current_app
    state = board_state(saved)
    event = {'party_id': target.id, 'version': saved.version, 'generation': saved.generation,
             'fog_version': saved.fog_version, 'update': board_update(previous, state)}
    for user_id in party_recipient_ids(target):
        try:
            socketio.emit('shared_map_changed', event, room=f'user_{user_id}')
        except Exception:
            current_app.logger.exception('Unable to publish whiteboard update')
    return True


@party.route('/party/<int:party_id>/shared-map')
@login_required
def shared_map(party_id):
    from flask_wtf.csrf import generate_csrf
    target = _board_party(party_id)
    response = make_response(render_template('main/shared_map.html', party=target,
        editing=True, warden=current_user.id == target.owner,
        can_load_maps=current_user.id == target.owner and user_features_enabled() and party_features_enabled(party_id),
        csrf_token=generate_csrf(), roll_form=FlaskForm()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.route('/party/<int:party_id>/shared-map/scene', methods=['GET', 'POST'])
@login_required
def shared_map_scene(party_id):
    from app.lib.whiteboard import board_state, drawing_value, integer
    target = _board_party(party_id)
    if request.method == 'GET' and request.args:
        # Check small revision columns before loading the embedded image JSON.
        revision = db.session.query(PartyMap.version, PartyMap.generation, PartyMap.fog_version).filter_by(party_id=party_id).first()
        values = revision if revision else (0, 1, 0)
        if all(request.args.get(key, type=int) == value for key, value in zip(('version', 'generation', 'fog_version'), values)):
            return _board_json(('', 204))
    saved = db.session.get(PartyMap, party_id)
    state = board_state(saved)
    if request.method == 'GET':
        return _board_json(state)
    data = _board_data()
    version, generation = integer(data, 'version'), integer(data, 'generation', 1)
    if generation != state['generation']:
        return _board_conflict('replaced')
    if version != state['version']:
        return _board_conflict()
    if 'drawing' not in data:
        abort(400)
    drawing = drawing_value(data['drawing'], stored_files=state['drawing']['files'], reuse_files=data.get('reuse_files'))
    if current_user.id != target.owner:
        from app.lib.whiteboard import protect_locked_elements
        protect_locked_elements(state['drawing'], drawing)
    if not _board_write(target, saved, {'version': version, 'generation': generation},
                        {'drawing': drawing, 'version': version + 1}):
        return _board_conflict()
    return _board_json({'version': version + 1})


@party.route('/party/<int:party_id>/shared-map/tokens')
@login_required
def shared_map_tokens(party_id):
    from urllib.parse import urlsplit
    from app.lib.companions import can_manage
    target = _board_party(party_id)
    warden = current_user.id == target.owner
    tokens = []
    def companion_token(companion, parent):
        return {'id': f'companion:{companion.id}', 'name': companion.name,
                'portrait': companion.portrait_src if companion.image_url or companion.kind == 'monster' else None, 'kind': companion.kind, 'parent': parent}

    for character in party_characters(target):
        if not warden and character.owner != current_user.id:
            continue
        portrait = character.image_url if character.custom_image else url_for(
            'static', filename='images/portraits/' + (character.image_url or 'default-portrait.webp'))
        # No server-side fetching of user-controlled URLs.
        try:
            parsed = urlsplit(portrait or '')
            if parsed.scheme not in ('', 'http', 'https') or parsed.username or parsed.password:
                portrait = None
        except ValueError:
            portrait = None
        tokens.append({'id': character.id, 'name': character.name, 'portrait': portrait})
        tokens.extend(companion_token(pet, character.name) for pet in character.pets)
    for hireling in target.hirelings:
        if not warden and not can_manage(hireling):
            continue
        tokens.append(companion_token(hireling, target.name))
        tokens.extend(companion_token(pet, hireling.name) for pet in hireling.pets)
    if warden:
        tokens.extend(companion_token(monster, target.name) for monster in target.monsters)
    return _board_json({'tokens': tokens})


@party.get('/party/<int:party_id>/shared-map/portraits')
@login_required
def shared_map_portraits(party_id):
    """Current artwork for linked tokens, without exposing private monster sheets."""
    return _board_json({'portraits': _board_portraits(_board_party(party_id))})


def _board_portraits(target):
    import re
    from urllib.parse import urlsplit
    from app.lib.whiteboard import board_state
    warden = target.owner == current_user.id
    placed = set()
    for element in board_state(db.session.get(PartyMap, target.id))['drawing']['elements']:
        match = re.match(r'^actor-(companion-)?(\d+)-', element['id'])
        if match:
            placed.add(('companion:' if match[1] else '') + match[2])
    portraits = []

    def add(actor, kind='character'):
        key = str(actor.id) if kind == 'character' else f'companion:{actor.id}'
        if key not in placed:
            return
        if kind == 'character':
            portrait = actor.image_url if actor.custom_image else url_for(
                'static', filename='images/portraits/' + (actor.image_url or 'default-portrait.webp'))
        else:
            portrait = actor.portrait_src if actor.image_url or kind == 'monster' else None
        try:
            parsed = urlsplit(portrait or '')
            if parsed.scheme not in ('', 'http', 'https') or parsed.username or parsed.password:
                portrait = None
        except ValueError:
            portrait = None
        # A placed monster's artwork is already shared, but its private name/stats are not.
        name = '' if kind == 'monster' and not warden and not actor.shared else actor.name
        portraits.append(dict(id=key, name=name, kind=kind, portrait=portrait))

    for character in party_characters(target):
        add(character)
        for pet in character.pets:
            add(pet, pet.kind)
    for hireling in target.hirelings:
        add(hireling, hireling.kind)
        for pet in hireling.pets:
            add(pet, pet.kind)
    for monster in target.monsters:
        add(monster, monster.kind)
    return portraits


@party.get('/party/<int:party_id>/shared-map/stats')
@login_required
def shared_map_stats(party_id):
    """Viewer-specific live stats; never put private sheets into the shared scene."""
    return _board_json({'actors': _board_stats(_board_party(party_id))})


def _board_stats(target):
    warden = current_user.id == target.owner
    actors = []

    def add(actor, kind='character'):
        if kind == 'monster' and not warden and not actor.shared:
            return
        stats = {field: [getattr(actor, field), getattr(actor, field + '_max')]
                 for field in ('hp', 'strength', 'dexterity', 'willpower')
                 if getattr(actor, field) is not None}
        if kind == 'character' and 'hp' in stats:
            stats['hp'] = actor.hpValue()
        if not stats:
            return
        data = {'id': str(actor.id) if kind == 'character' else f'companion:{actor.id}',
                'name': actor.name, 'kind': kind, 'stats': stats, 'armor': actor.armorValue()}
        if kind != 'character':
            data['attack'] = actor.attack
        if kind == 'monster':
            data['shared'] = actor.shared
        actors.append(data)

    for character in party_characters(target):
        add(character)
        for pet in character.pets:
            add(pet, pet.kind)
    for hireling in target.hirelings:
        add(hireling, hireling.kind)
        for pet in hireling.pets:
            add(pet, pet.kind)
    for monster in target.monsters:
        add(monster, monster.kind)
    return actors


@party.route('/party/<int:party_id>/shared-map/monsters/<int:companion_id>/visibility', methods=['GET', 'POST'])
@login_required
def shared_map_monster_visibility(party_id, companion_id):
    from app.models import Companion
    target = _board_party(party_id, owner=True)
    c = db.get_or_404(Companion, companion_id)
    if c.kind != 'monster' or c.party_id != target.id:
        abort(404)
    if request.method == 'POST':
        data = _board_data()
        shared, notes = data.get('shared'), data.get('public_notes', c.public_notes)
        if type(shared) is not bool or not isinstance(notes, str) or len(notes) > 10000:
            abort(400)
        c.shared, c.public_notes = shared, notes
        db.session.commit()
        from app import socketio
        from flask import current_app
        for user_id in party_recipient_ids(target):
            try:
                socketio.emit('party_actors_changed', {'party_id': target.id}, room=f'user_{user_id}')
            except Exception:
                current_app.logger.exception('Unable to publish monster visibility change')
    return _board_json({'id': c.id, 'name': c.name, 'shared': c.shared, 'public_notes': c.public_notes})


@party.get('/party/<int:party_id>/shared-map/actors/<int:companion_id>')
@login_required
def shared_map_actor(party_id, companion_id):
    from app.models import Companion
    target = _board_party(party_id)
    c = db.get_or_404(Companion, companion_id)
    ids = {companion.id for parent in party_characters(target) for companion in parent.pets}
    ids.update(companion.id for companion in target.party_companions)
    ids.update(pet.id for hireling in target.hirelings for pet in hireling.pets)
    if c.id not in ids:
        abort(403)
    if c.kind == 'monster' and current_user.id != target.owner:
        if not c.shared:
            response = make_response(render_template('main/monster_public.html', c=None), 403)
            response.headers['Cache-Control'] = 'no-store'
            return response
        response = make_response(render_template('main/monster_public.html', c=c))
        response.headers['Cache-Control'] = 'no-store'
        return response
    return redirect(url_for('companions.sheet', companion_id=c.id))


@party.get('/party/<int:party_id>/shared-map/characters/<int:character_id>')
@login_required
def shared_map_character(party_id, character_id):
    target = _board_party(party_id)
    character = next((c for c in party_characters(target) if c.id == character_id), None)
    if character is None:
        abort(403)
    return redirect(url_for('main.character', username=character.owner_username, url_name=character.url_name))


@party.get('/party/<int:party_id>/shared-map/roll-actors')
@login_required
def shared_map_roll_actors(party_id):
    return _board_json({'actors': _board_roll_actors(_board_party(party_id))})


def _board_roll_actors(target):
    if target.owner == current_user.id:
        actors = [dict(id=f'companion:{c.id}', name=c.name, kind='monster',
                       stats={field: getattr(c, field) for field in ('strength', 'dexterity', 'willpower')},
                       damage=c.attack_dice) for c in target.monsters]
    else:
        actors = [dict(id=str(c.id), name=c.name, kind='character')
                  for c in party_characters(target) if c.owner == current_user.id]
    return actors


@party.get('/party/<int:party_id>/shared-map/actors')
@login_required
def shared_map_actors(party_id):
    target = _board_party(party_id)
    return _board_json({'stats': _board_stats(target), 'portraits': _board_portraits(target),
                        'rollActors': _board_roll_actors(target)})


@party.post('/party/<int:party_id>/shared-map/roll')
@login_required
def shared_map_roll(party_id):
    from app.lib.character_rolls import parse_dice, publish_roll
    from app.models import Companion
    import secrets
    target = db.get_or_404(Party, party_id)
    if current_user.id not in party_recipient_ids(target):
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    c = None
    character_id = request.form.get('character_id')
    if character_id and request.form.get('companion_id'):
        abort(400)
    if character_id:
        c = db.get_or_404(Character, request.form.get('character_id', type=int))
        if c.owner != current_user.id or c.party_id != target.id or c.id not in json.loads(target.members or '[]'):
            abort(403)
    if request.form.get('companion_id'):
        c = db.get_or_404(Companion, request.form.get('companion_id', type=int))
        if c.kind != 'monster' or c.party_id != target.id or target.owner != current_user.id:
            abort(403)
    public = bool(character_id) or request.form.get('public_roll') == 'on'
    try:
        sides = parse_dice(request.form.get('dice'))
    except ValueError as error:
        return _board_json({'error': str(error)}), 400
    save = request.form.get('save')
    if save and (c is None or save not in ('strength', 'dexterity', 'willpower') or sides != [20] or getattr(c, save) is None):
        abort(400)
    values = [secrets.randbelow(side) + 1 for side in sides]
    result = f'{", ".join(map(str, values))} ({"+".join(f"d{side}" for side in sides)})'
    if save:
        label = {'strength': 'STR', 'dexterity': 'DEX', 'willpower': 'WIL'}[save]
        result += f' · {label} {getattr(c, save)} · ' + (_('Success') if values[0] <= getattr(c, save) else _('Failure'))
    name = c.name if c else _('Warden') if current_user.id == target.owner else current_user.username
    db.session.add(PartyRoll(party_id=target.id, character_name=name, result=result,
                             private_user_id=None if public else current_user.id))
    db.session.commit()
    if public:
        publish_roll(target, name, result)
    return _board_json({'result': result, 'values': values})


@party.route('/party/<int:party_id>/shared-map/sources')
@login_required
def shared_map_sources(party_id):
    _board_party(party_id, owner=True)
    _board_campaign_access(party_id)
    from app.models import ContentEntry, PointcrawlMap
    maps = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == current_user.id).all()
    return _board_json({'maps': [{'id': item.id, 'title': item.entry.title,
        'campaign': item.entry.campaign.name if item.entry.campaign else None,
        'campaign_id': item.entry.campaign_id} for item in maps]})


def _board_source(source_id):
    from app.models import PointcrawlMap
    item = db.get_or_404(PointcrawlMap, source_id)
    if item.entry.owner_id != current_user.id:
        abort(403)
    return item


@party.route('/party/<int:party_id>/shared-map/sources/<int:source_id>')
@login_required
def shared_map_preview(party_id, source_id):
    _board_party(party_id, owner=True)
    _board_campaign_access(party_id)
    from app.lib.whiteboard import source_snapshot
    item = _board_source(source_id)
    drawing, digest = source_snapshot(item)
    return _board_json({'source_id': item.id, 'title': item.entry.title, 'drawing': drawing, 'digest': digest})


@party.route('/party/<int:party_id>/shared-map/import', methods=['POST'])
@login_required
def shared_map_import(party_id):
    from app.lib.whiteboard import board_state, source_snapshot, empty_fog, integer
    target = _board_party(party_id, owner=True)
    _board_campaign_access(party_id)
    data = _board_data()
    saved = db.session.get(PartyMap, party_id)
    state = board_state(saved)
    conditions = {key: integer(data, key) for key in ('generation', 'version', 'fog_version')}
    if any(state[key] != value for key, value in conditions.items()):
        return _board_conflict('changed')
    source = _board_source(integer(data, 'source_id'))
    drawing, digest = source_snapshot(source)
    if data.get('digest') != digest:
        return _board_conflict('source_changed')
    if type(data.get('cover')) is not bool:
        abort(400)
    fog = empty_fog()
    fog['enabled'] = data['cover']
    values = {'drawing': drawing, 'version': state['version'] + 1,
              'generation': state['generation'] + 1, 'fog': fog, 'fog_version': state['fog_version'] + 1}
    if not _board_write(target, saved, conditions, values):
        return _board_conflict()
    return _board_json(board_state(db.session.get(PartyMap, party_id)))


@party.route('/party/<int:party_id>/shared-map/fog', methods=['POST'])
@login_required
def shared_map_fog(party_id):
    from app.lib.whiteboard import board_state, fog_operation, integer
    target = _board_party(party_id, owner=True)
    data = _board_data()
    saved = db.session.get(PartyMap, party_id)
    state = board_state(saved)
    generation, version = integer(data, 'generation'), integer(data, 'fog_version')
    if generation != state['generation']:
        return _board_conflict('replaced')
    operation = data.get('operation')
    # Retries of an acknowledged operation are harmless even with an old version.
    if isinstance(operation, dict) and operation.get('id') in state['fog']['applied']:
        return _board_json({'fog': state['fog'], 'fog_version': state['fog_version'], 'generation': generation})
    if version != state['fog_version']:
        return _board_conflict()
    fog, _ = fog_operation(state['fog'], operation)
    if not _board_write(target, saved, {'generation': generation, 'fog_version': version},
                        {'fog': fog, 'fog_version': version + 1}):
        return _board_conflict()
    return _board_json({'fog': fog, 'fog_version': version + 1, 'generation': generation})


def party_characters(target_party):
    members = json.loads(target_party.members) if target_party.members and target_party.members.strip() else []
    by_id = {character.id: character for character in Character.query.filter(
        Character.id.in_(members), Character.party_id == target_party.id
    ).all()}
    return [by_id[member_id] for member_id in members if member_id in by_id]


@party.route('/party/<int:party_id>/members', methods=['GET'])
@login_required
def members(party_id):
    target_party = db.get_or_404(Party, party_id)
    response = make_response(render_template(
        'partial/partyview/members.html', party=target_party,
        characters=party_characters(target_party), stat_form=FlaskForm()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.route('/party/<int:party_id>/members/<int:character_id>/stat', methods=['POST'])
@login_required
def update_member_stat(party_id, character_id):
    target_party = db.get_or_404(Party, party_id)
    character = db.get_or_404(Character, character_id)
    if character.party_id != target_party.id or character.id not in json.loads(target_party.members or '[]'):
        abort(404)
    if current_user.id not in (target_party.owner, character.owner):
        abort(403)
    return save_current_stat(character)


def get_party_data(ownername, party_url):
    owner = User.query.filter_by(username=ownername).first_or_404()
    party = Party.query.filter_by(
        owner=owner.id, party_url=party_url).first_or_404()
    join_code = None
    is_owner = False
    is_subowner = False
    if current_user.is_authenticated:
        if party.owner == current_user.id:
            join_code = party.join_code
            is_owner = True
    subowners_list = json.loads(
        party.subowners) if party.subowners and party.subowners.strip() else []

    if current_user.is_authenticated:
        is_subowner = current_user.id in subowners_list
    characters = party_characters(party)
    for character in characters:
        character.portrait_src = character.image_url if character.custom_image else url_for(
            'static', filename='images/portraits/' + (character.image_url or 'default-portrait.webp'))
    
    inventory = Inventory(party)
    inventory.select(0)
    inventory.setItemsWithRolls(False)
    inventory.decorate()

    return party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party


# Route: view party page
@party.route('/users/<ownername>/parties/<party_url>/', methods=['GET'])
def party_view(ownername, party_url):
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    from app.lib.monsters import monster_catalog
    can_view_rolls = current_user.id in party_recipient_ids(party)
    from app.lib.feature_access import party_features_enabled, user_features_enabled
    from app.lib.campaigns import party_knowledge_tree, CATEGORIES
    from app.lib.rich_content import content_excerpt
    campaign_enabled = can_view_rolls and party_features_enabled(party.id)
    campaign_entries, campaign_hierarchy = party_knowledge_tree(party.id) if campaign_enabled else ([], [])
    campaign_preview = is_owner and request.args.get('preview') == '1'
    response = make_response(render_template('main/party_view.html', party_url=party_url, characters=characters, join_code=join_code, is_owner=is_owner,
                           is_subowner=is_subowner, party_id=party.id, ownername=ownername, inventory=inventory, party=party,
                           can_view_rolls=can_view_rolls, roll_form=FlaskForm(), stat_form=FlaskForm(),
                           templates=monster_catalog() if is_owner else {}, form=FlaskForm(),
                           campaign_enabled=campaign_enabled, campaign_entries=campaign_entries,
                           campaign_hierarchy=campaign_hierarchy, campaign_preview=campaign_preview,
                           campaign_editing=is_owner and user_features_enabled() and not campaign_preview,
                           content_categories=CATEGORIES, content_excerpt=content_excerpt,
                           rolls=PartyRoll.latest(party.id, current_user.id) if can_view_rolls else [],
                           wilderness_mounts=wilderness_mounts(party, characters)))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.post('/warden/roll')
@login_required
def warden_roll():
    from app.lib.warden_rolls import roll_warden
    from app.lib.character_rolls import publish_roll
    if not FlaskForm().validate_on_submit():
        abort(400)
    raw_party = request.form.get('party_id')
    target = None
    if raw_party:
        try:
            party_id = int(raw_party)
        except ValueError:
            abort(400)
        target = db.get_or_404(Party, party_id)
    public = request.form.get('public_roll') == 'on'
    try:
        result = roll_warden(current_user, target, request.form.get('kind'), request.form.get('dice'), public=public)
    except PermissionError:
        abort(403)
    except ValueError as error:
        return _board_json({'error': str(error)}), 400
    db.session.commit()
    publish_roll(target, _('Warden'), result['result'], None if public else current_user.id)
    return _board_json(result)


@party.route('/party/<int:party_id>/roll-history', methods=['GET'])
@login_required
def roll_history(party_id):
    target_party = db.get_or_404(Party, party_id)
    if current_user.id not in party_recipient_ids(target_party):
        abort(403)
    response = make_response(render_template('partial/partyview/roll_history_entries.html',
                                            party=target_party, rolls=PartyRoll.latest(party_id, current_user.id)))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.route('/party/<int:party_id>/roll-history/clear', methods=['POST'])
@login_required
def clear_roll_history(party_id):
    target_party = db.get_or_404(Party, party_id)
    if target_party.owner != current_user.id:
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    PartyRoll.query.filter_by(party_id=party_id).delete(synchronize_session=False)
    db.session.commit()
    notify_roll_history_changed(target_party)
    return '', 204


# Route: redirect to character view
@party.route('/party/show-user/<username>/<url_name>', methods=['GET'])
def party_show_user(username, url_name):
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name+"/"
    return response


# Route: edit party
@party.route('/party/edit/<ownername>/<party_url>', methods=['GET'])
def party_edit(ownername, party_url):
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    form = PartyEditForm(obj=party) 
    render =  render_template('main/party_edit.html', party_url=party_url, characters = characters, join_code = join_code, is_owner=is_owner, is_subowner=is_subowner,ownername=ownername, inventory=inventory, party=party, form=form)
    response = make_response(render)
    response.headers["HX-Trigger-After-Settle"] = "party-edit"
    return response
    

# Route: edit party cancel
@party.route('/party/edit/<ownername>/<party_url>/cancel', methods=['GET','POST'])
def party_edit_cancel(ownername, party_url):
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    if not can_transfer_from(party):
        abort(403)
    data = request.form
    from app.lib.ground_items import preserve_ground
    restored_items, restored_containers = preserve_ground(party,
        json.loads(data.get('old_items') or '[]'), json.loads(data.get('old_containers') or '[]'))
    changed = False
    # restore some data
    if data['old_items'] != None:
        finish_companion_transfers(party, restored_items)
        party.items = json.dumps(restored_items)
        changed = True
    if data['old_containers'] != None:
        party.containers = json.dumps(restored_containers)
        changed = True
    if changed:
        db.session.commit()
    inventory.remove_items_from_characters(json.loads(party.items))
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+ownername+"/parties/"+party_url+"/"
    return response


# Route: edit party save
@party.route('/party/edit/<ownername>/<party_url>/save', methods=['POST'])
def party_edit_save(ownername, party_url):
    fields_to_update = ['name','description']
    party = get_party_by_owner(ownername, party_url)
    form = PartyEditForm(obj=party) 
    for field in fields_to_update:
        setattr(party, field, sanitize_data(getattr(form, field).data))
    # Backward compatibility: update item ids
    items = json.loads(party.items)
    result = []
    for it in items:
        if isinstance(it["id"], int):
            it["id"] = uuid.uuid4().hex
        result.append(it)
    party.items = json.dumps(result)
    finish_companion_transfers(party)
    db.session.commit()
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+ownername+"/parties/"+party_url+"/"
    return response

# Route: remove character from party
@party.route('/party/remove-char/<character_id>/<ownername>/<party_url>', methods=['POST'])
@login_required
def party_remove_char(character_id, ownername, party_url):
    target_party = get_party_by_owner(ownername, party_url)
    if target_party is None:
        abort(404)
    if target_party.owner != current_user.id:
        abort(403)
    character = get_character(character_id)
    if character is None or character.party_id != target_party.id:
        abort(404)
    remove_character_from_party(character)
    db.session.commit()
    response = make_response("")
    response.headers["HX-Redirect"] = "/party/edit/"+ownername+"/"+party_url
    return response

# Route: delete party
@party.route('/party/delete/<party_id>', methods=['POST'])
@login_required
def party_delete(party_id):
    party = get_party_by_id(party_id)
    if party is None:
        abort(404)
    if party.owner != current_user.id:
        abort(403)

    # remove party from all characters in the party
    characters = Character.query.filter_by(party_id=party.id).all()
    for character in characters:
        character.party_id = None
        character.party_code = None

    PartyRoll.query.filter_by(party_id=party.id).delete(synchronize_session=False)
    PartyMap.query.filter_by(party_id=party.id).delete(synchronize_session=False)
    db.session.delete(party)
    db.session.commit()
    
    response = make_response("redirect")
    response.headers["HX-Redirect"] = "/users/"+current_user.username+"/parties/"
    return response


# --- PARTY INVENTORY ---

# Route: edit inventory
@party.route('/party/inventory/<party_id>/<container_id>', methods=['GET'])
def party_inventory_edit(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    if container_id != "None":
        inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)        
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)

# Route: edit container dialog
@party.route('/party/inventory/<party_id>/container-edit/<container_id>', methods=['GET'])
def party_inventory_container_edit(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        container = inventory.get_container(container_id)
    else:
        container = None
    render =  render_template('partial/modal/edit_container_party.html', party=party, inventory=inventory, container=container, mode=mode)
    response = make_response(render)
    response.headers['HX-Trigger-After-Settle'] = "container-edit"
    return response

# Route: edit container dialog save
@party.route('/party/inventory/<party_id>/container-edit/<container_id>/save', methods=['POST'])
def party_inventory_container_edit_save(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    data = request.form
    slots = 1
    if "slots" in data and data["slots"] != "":
        slots = data["slots"]
    if data["mode"] == "edit":
        inventory.update_container(container_id,data["name"],slots,data["carried_by"],data["load"])
        inventory.select(int(container_id))
        container = inventory.get_container(container_id)
    else:
        id = inventory.add_container(data["name"],slots,data["carried_by"],data["load"])
        inventory.select(id)
        container = inventory.get_container(id)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)


# Route: select inventory container
@party.route('/party/inventory-select-container/<party_id>/<container_id>', methods=['GET'])
def party_inventory_select_container(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.select(int(container_id))
    if inventory.selected_container.get('on_the_ground'):
        return redirect(url_for('ground.view', party_id=party.id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    tpl = 'partial/partyview/inventory.html'
    mode = request.args.get('mode')
    if mode != None and mode == "edit":
        tpl = 'partial/partyedit/inventory.html'
    return render_template(tpl, party=party, inventory=inventory)

# Route: delete container
@party.route('/party/inventory/<party_id>/container-edit/<container_id>/delete', methods=['POST'])
def party_inventory_container_delete(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    data = request.form
    inventory.delete_container(container_id, data["delete-items"])
    inventory.select(0)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)

# Route: edit item dialog
@party.route('/party/inventory/<party_id>/item-edit/<item_id>', methods=['GET'])
def party_inventory_item_edit(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    characters = []
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        item = inventory.get_item(item_id)
        members_list = json.loads(
        party.members) if party.members and party.members.strip() else []
        for member_id in members_list:
            character = Character.query.filter_by(id=member_id).first()
            if character:
                characters.append(character)
    else:
        item = None
    render = render_template('partial/modal/edit_item_party.html', characters=characters, party=party, inventory=inventory, item=item, mode=mode, library=Market().buy([it["name"] for it in load_market()]))
    response = make_response(render)
    response.headers['HX-Trigger-After-Settle'] = "item-edit"
    return response

# Route: edit item save
@party.route('/party/inventory/<party_id>/item-edit/<item_id>/save', methods=['POST'])
def party_inventory_item_edit_save(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    data = request.form
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if data["edit_item_container"].startswith('companion:'):
        if mode != 'edit':
            abort(400)
        from werkzeug.exceptions import HTTPException
        try:
            save_item_to_companion(inventory, item_id, data["edit_item_container"])
        except HTTPException as error:
            db.session.rollback()
            response = make_response(render_template('partial/inventory_error.html', message=error.description))
            response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
            return response
    elif mode == "edit":
        item = inventory.update_item(item_id,data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on")
        inventory.select(int(item["location"]))
    else:
        item = inventory.create_item(data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on")
        inventory.select(int(item["location"]))
    inventory.decorate()
    render = render_template('partial/partyedit/inventory.html', party=party,inventory=inventory)    
    response = make_response(render)
    return response



# Route: remove inventory item
@party.route('/party/inventory/<party_id>/<container_id>/item-delete/<item_id>', methods=['GET'])
def party_inventory_delete_item(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.delete_item(container_id, item_id)
    inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    render =  render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)
    response = make_response(render)
    return response

# Route: change some amount property in item
@party.route('/party/inventory/<party_id>/item-edit/<item_id>/amount', methods=['GET'])
def party_inventory_item_edit_amount(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    prop = request.args.get('property')
    action = request.args.get('action')
    item = inventory.change_amount(item_id, action, prop)
    inventory.select(item["location"])
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)  


# Route: transfer item dialog
@party.route('/party/inventory/<party_id>/item-transfer/<container_id>/<item_id>', methods=['GET'])
def party_inventory_item_transfer(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    item = inventory.get_item(item_id)
    members_list = json.loads(
        party.members) if party.members and party.members.strip() else []
    characters = []
    for member_id in members_list:
        character = Character.query.filter_by(id=member_id).first()
        if character:
            characters.append(character)
    return render_template('partial/modal/transfer_item.html', characters=characters,party=party, inventory=inventory, item=item, container_id=container_id)

# Route: transfer item dialog accept
@party.route('/party/inventory/<party_id>/item-transfer/<container_id>/<item_id>/transfer', methods=['POST'])
def party_inventory_item_transfer_accept(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    data = request.form
    inventory = Inventory(party)
    if data['member'] and data['member'] != "":
        item = inventory.move_item_to_user(item_id, int(data['member']))
        inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)  

      
    


def wilderness_mounts(target_party, characters):
    return [pet for parent in [*characters, *target_party.hirelings] for pet in parent.pets
            if any(int(c.get('slots', 0)) > 0 for c in json.loads(pet.containers or '[]'))]


@party.post('/party/<int:party_id>/wilderness')
@login_required
def wilderness_action(party_id):
    from app.lib.wilderness import supply, make_camp
    target = db.get_or_404(Party, party_id)
    if target.owner != current_user.id:
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    characters = party_characters(target)
    selected = request.form.getlist('participants')
    by_id = {str(c.id): c for c in characters if not c.dead}
    if not selected:
        flash(_('You need to select a PC first'), 'wilderness')
        return redirect(url_for('party.party_view', ownername=target.owner_username, party_url=target.party_url))
    if len(set(selected)) != len(selected) or any(i not in by_id for i in selected):
        abort(400)
    participants = [by_id[i] for i in selected]
    action = request.form.get('action')
    try:
        # Compare-and-swap prevents a second submission from spending or awarding twice.
        version = int(request.form.get('version', ''))
    except ValueError:
        abort(400)
    changed = Party.query.filter_by(id=target.id, version=version).update(
        {Party.version: Party.version + 1}, synchronize_session=False)
    if not changed:
        db.session.rollback()
        flash(_('The party changed. Review its current resources and try again.'), 'wilderness')
        return redirect(url_for('party.party_view', ownername=target.owner_username, party_url=target.party_url))
    try:
        if action == 'supply':
            try:
                bonus = int(request.form.get('bonus', '0'))
            except ValueError:
                abort(400)
            if not 0 <= bonus <= 4:
                abort(400)
            sides, amount = supply(target, participants, bonus)
            result = _('Supply: d%(sides)s → %(amount)s Rations (3 uses each), added to party storage.', sides=sides, amount=amount)
            db.session.add(PartyRoll(party_id=target.id, character_name=current_user.username, result=result))
        elif action == 'camp':
            allowed_mounts = {str(c.id): c for c in wilderness_mounts(target, characters)}
            mount_ids = request.form.getlist('mounts')
            if len(set(mount_ids)) != len(mount_ids) or any(i not in allowed_mounts for i in mount_ids):
                abort(400)
            make_camp(target, participants, [allowed_mounts[i] for i in mount_ids],
                      resolve_deprivation=request.form.get('resolve_deprivation') == 'on')
            result = _('Camp complete: one Ration use consumed per selected character or mount; Fatigue removed where recovery is possible.')
        else:
            abort(400)
        db.session.commit()
        if action == 'supply':
            notify_roll_history_changed(target)
        flash(result, 'wilderness')
    except ValueError as error:
        db.session.rollback()
        flash(_(str(error)), 'wilderness')
    return redirect(url_for('party.party_view', ownername=target.owner_username, party_url=target.party_url))

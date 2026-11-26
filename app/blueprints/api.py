from kettlewright import system
from flask import Blueprint, jsonify, abort
from flask_login import current_user
from app.models import User, Character, Party
import os
import sys
from flask_babel import _

api = Blueprint('api', __name__)

base_url = os.environ.get('BASE_URL')
print('base_url:', base_url, file=sys.stderr)


def character_to_dict(character):
    return {
        'name': character.name,
        'url_name': character.url_name,
        'background': character.background,
        'description': character.description,
        'traits': character.traits,
        'bonds': character.bonds,
        'scars': character.scars,
        'omens': character.omens,
        'portrait': character.image_url if character.custom_image else f'{base_url}/static/images/portraits/{character.image_url}',
        # Its game system's stats and their maximums, then its conditions (kettlewright): STR, DEX, WIL and HP,
        # then Deprived, Panicked and Dead in Cairn.
        **{field: character.get_stat(field) for stat in system().sheet_stats
           for field in (stat.key, stat.key + '_max')},
        **{key: getattr(character, key, None) for key in system().condition_keys},
        'gold': character.gold,
        'notes': character.notes,
        'items': character.items,
        'containers': character.containers,
    }


@api.route('/api/users/<username>/characters/<url_name>/')
def get_character(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()

    party = Party.query.filter_by(id=character.party_id).first()

    character_data = character_to_dict(character)

    if party:
        owner = User.query.filter_by(id=party.owner).first()
        character_data['party'] = {
            'name': party.name,
            'url': f'users/{owner.username}/parties/{party.party_url}/',
            'description': party.description
        }

    return jsonify(character_data)


# --- Public API v1 (#137) -------------------------------------------------
# Read-only access to the public Tools. No login: nothing here reads or
# changes user data. Documented in docs/api.md.
from flask import request, url_for
from werkzeug.exceptions import HTTPException
import json


@api.errorhandler(HTTPException)
def api_error(error):
    if not request.path.startswith('/api/v1'):
        return error
    response = jsonify(error=error.description or error.name, status=error.code)
    response.status_code = error.code
    return response


def _absolute_portrait(path):
    return url_for('static', filename='images/portraits/' + path, _external=True) if path else None


@api.route('/api/v1/')
def v1_index():
    from app.lib.tool_tables import ROLLS
    return jsonify(
        version=1,
        documentation='https://github.com/yochaigal/kettlewright/blob/main/docs/api.md',
        endpoints={
            'backgrounds': url_for('api.v1_backgrounds', _external=True),
            'random_character': url_for('api.v1_random_character', _external=True),
            'monsters': url_for('api.v1_monsters', _external=True),
            'tables': url_for('api.v1_tables', _external=True),
            'rolls': {name: {'url': url_for('api.v1_roll', table=name, _external=True), 'description': description}
                      for name, (description, _roller) in ROLLS.items()},
        })


@api.route('/api/v1/backgrounds')
def v1_backgrounds():
    from app.lib.data import load_backgrounds
    from kettlewright.web import plugin
    gear_packages = plugin().gear_packages  # The system's (kettlewright): Cairn's Barebones packages.
    backgrounds = [{'name': name, 'description': _(background.get('background_description', ''))}
                   for name, background in load_backgrounds().items()]
    return jsonify(backgrounds=backgrounds, barebones_packages=gear_packages())


@api.route('/api/v1/characters/random')
def v1_random_character():
    background = (request.args.get('background') or '').strip()
    # The system makes it (kettlewright): Cairn's quick generator, or its Barebones tables.
    from kettlewright.web import plugin
    try:
        _genchar, data = plugin().random_character(background or None)
    except KeyError:
        if background == 'barebones' or background.startswith('barebones:'):
            abort(404, description=f"Unknown Barebones package '{background.partition(':')[2]}'. See /api/v1/backgrounds.")
        abort(404, description=f"Unknown background '{background}'. See /api/v1/backgrounds.")
    character = json.loads(data)
    character['image_url'] = _absolute_portrait(character.get('image_url'))
    return jsonify(character)


@api.route('/api/v1/monsters')
def v1_monsters():
    from app.lib.monsters import monster_catalog
    return jsonify(monsters=[dict(monster, key=key, image_url=_absolute_portrait(monster.get('image_url')))
                             for key, monster in sorted(monster_catalog().items())])


@api.route('/api/v1/monsters/<key>')
def v1_monster(key):
    from app.lib.monsters import monster_catalog
    monster = monster_catalog().get(key)
    if monster is None:
        abort(404, description=f"Unknown monster '{key}'. See /api/v1/monsters.")
    return jsonify(dict(monster, key=key, image_url=_absolute_portrait(monster.get('image_url'))))


@api.route('/api/v1/tables')
def v1_tables():
    from app.lib.tool_tables import load_tables
    return jsonify(load_tables())


@api.route('/api/v1/roll/<table>')
def v1_roll(table):
    from app.lib.tool_tables import ROLLS, roll
    if table not in ROLLS:
        abort(404, description=f"Unknown table '{table}'. Tables: {', '.join(ROLLS)}.")
    try:
        return jsonify(roll(table, request.args))
    except ValueError as error:
        abort(400, description=str(error))


@api.route('/api/v1/<path:unknown>')
def v1_not_found(unknown):
    abort(404, description='Unknown endpoint. See /api/v1/ for the list.')

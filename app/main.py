from app.lib.translation_contexts import (
    _EVENTS_UNTRANSLATED_KEYS, _EVENTS_UNTRANSLATED_PATHS, _EVENTS_TRANSLATION_CONTEXTS,
)
from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request, make_response, send_file, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from .models import User, Character, Party
from .models.character import EDITIONS, EDITION_SECOND
from . import db
from .forms import CharacterForm, CharacterEditForm, CharacterJSONForm, PartyForm, PartyEditForm
from app.lib import load_scars, character_portrait_link, Inventory, sanitize_data, sanitize_json_content, load_version, load_backgrounds, load_traits, load_bonds, load_omens
import sys
import json
from urllib.parse import quote
import re
from slugify import slugify
import os
import bleach
from flask_htmx import HTMX
from flask_babel import _
from app.lib.translations import translate_term
from app.lib.character_permissions import can_edit_character
import datetime
import urllib.parse


main = Blueprint('main', __name__)
htmx = HTMX(main)

base_url = os.environ.get('BASE_URL')
print('base_url:', base_url, file=sys.stderr)

# The system's tables (kettlewright).
from kettlewright import system as _system
omens_data = _system().content.load('omens')
scars_data = _system().content.load('scars')




@main.route('/')
def index():
    # Discord opens an Activity at "/" with its launch parameters (#423). Shown here, not
    # redirected: Discord's proxy follows redirects itself, so the page stays at "/" anyway.
    if request.args.get('frame_id') and request.args.get('instance_id'):
        from app.blueprints.activity import launch
        return launch()
    if current_user.is_authenticated:
        return redirect(url_for('main.characters', username=current_user.username))
    else:
        return redirect(url_for('auth.login'))


@main.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html', username=current_user.username)


@main.route('/users/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if username == current_user.username:
        return render_template('main/profile.html', username=current_user.username)
    else:
        return redirect(url_for('main.index'))


@main.route('/about')
def about():
    version = load_version()
    return render_template('main/about.html', version=version)


# Linked from sign-up, the About and Discord pages, and Discord's app settings (#455).
@main.route('/terms')
def terms():
    return render_template('main/terms.html')


@main.route('/privacy')
def privacy():
    return render_template('main/privacy.html')


@main.route('/users/<username>/characters/')
@login_required
def characters(username):
    user = User.query.filter_by(username=username).first_or_404()
    characters = Character.query.filter_by(owner=user.id).all()
    characters_sorted = sorted(
        characters, key=lambda x: x.created_at, reverse=True)
    for character in characters_sorted:
        if character.custom_image == False and character.image_url != None:
            character.portrait_src = url_for(
                'static', filename='images/portraits/' + character.image_url)
        else:
            character.portrait_src = character.image_url
    if username != current_user.username:
        return redirect(url_for('main.index'))
    return render_template('main/characters.html', username=current_user.username, characters=characters_sorted)


def create_unique_url_name(name):
    # Ensure the base name is properly slugified
    url_name = slugify(name)

    # Check if the base name already ends with a number pattern like "-1"
    match = re.search(r'-(\d+)$', url_name)
    if match:
        base_url_name = url_name.rsplit('-', 1)[0]
        counter = int(match.group(1)) + 1
    else:
        base_url_name = url_name
        counter = 1

    # Ensure uniqueness of the url_name
    while Character.query.filter_by(owner=current_user.id, url_name=url_name).first():
        url_name = f"{base_url_name}-{counter}"
        counter += 1

    return url_name


def import_system_stats(character, form):
    """An imported character's stats and conditions that the game system keeps without a column (kettlewright).
    An error message for a file of another game system (the instance plays one) or values that aren't numbers."""
    rules = _system()
    if form.game_system.data and form.game_system.data != rules.key:
        return _('This character plays another game system (%(system)s) than this site (%(here)s).',
                 system=form.game_system.data, here=rules.name)
    invalid = _('Invalid character stats or inventory in JSON file.')
    try:
        extra = json.loads(form.system_stats.data or '{}')
    except ValueError:
        return invalid
    if not isinstance(extra, dict):
        return invalid
    for stat in rules.stats:
        for field in (stat.key, stat.key + '_max'):
            if field in extra and not character.has_column(field):
                if type(extra[field]) is not int or not 0 <= extra[field] <= 9999:
                    return invalid
                character.set_stat(field, extra[field])
    for key in rules.condition_keys:
        if key in extra and not character.has_column(key):
            character.set_stat(key, extra[key] is True)
    return None


@main.route('/new_from_json/', methods=['GET', 'POST'])
@login_required
def new_from_json():
    from app.lib.companions import render_import_page
    form = CharacterJSONForm()
    user = current_user.username
    if current_user.is_authenticated:
        if form.validate_on_submit():
            from app.lib.character_json import normalize_inventory
            from app.lib.companions import import_pet
            try:
                items, containers = normalize_inventory(form.items.data, form.containers.data)
                pets_data = json.loads(form.pets.data or '[]')
                if not isinstance(pets_data, list) or len(pets_data) > 100:
                    raise ValueError('Invalid pets')
                pets = [import_pet(pet) for pet in pets_data]
                for field in ('strength', 'strength_max', 'dexterity', 'dexterity_max',
                              'willpower', 'willpower_max', 'hp', 'hp_max', 'gold'):
                    getattr(form, field).data = int(getattr(form, field).data or 0)
            except (ValueError, TypeError, KeyError):
                flash(_('Invalid character stats or inventory in JSON file.'))
                return render_import_page(form=form), 400

            # create url_name
            if form.name.data == 'Custom':
                url_name = create_unique_url_name(form.custom_name.data)
            else:
                url_name = create_unique_url_name(form.name.data)

            # add character to db
            character = Character(
                name=sanitize_data(form.name.data),
                background=sanitize_data(form.background.data),
                url_name=url_name,
                owner_username=current_user.username,
                owner=current_user.id,
                strength=sanitize_data(form.strength.data or 0),
                strength_max=sanitize_data(form.strength_max.data or 0),
                dexterity=sanitize_data(form.dexterity.data or 0),
                dexterity_max=sanitize_data(form.dexterity_max.data or 0),
                willpower=sanitize_data(form.willpower.data or 0),
                willpower_max=sanitize_data(form.willpower_max.data or 0),
                hp=sanitize_data(form.hp.data or 0),
                hp_max=sanitize_data(form.hp_max.data or 0),
                gold=sanitize_data(form.gold.data or 0),
                description=sanitize_data(form.description.data or ''),
                notes=sanitize_data(form.notes.data or ''),
                bonds=sanitize_data(form.bonds.data or ''),
                omens=sanitize_data(form.omens.data or ''),
                scars=sanitize_data(form.scars.data or ''),
                image_url=sanitize_data(form.image_url.data or ''),
                custom_image=string_to_bool(
                    sanitize_data(form.custom_image.data or False)),
                items=sanitize_json_content(json.dumps(items)),
                containers=sanitize_json_content(json.dumps(containers)),
                custom_name=sanitize_data(form.custom_name.data),
                custom_background=sanitize_data(form.custom_background.data),
                deprived=string_to_bool(
                    sanitize_data(form.deprived.data or False)),
                panicked=string_to_bool(form.panicked.data or False),
                dead=string_to_bool(form.dead.data or False),
                traits=sanitize_data(form.traits.data or ''),  # New field
                armor=sanitize_data(form.armor.data or ''),  # New field
                edition=form.edition.data if form.edition.data in EDITIONS else EDITION_SECOND
            )

            from app.models.character import BACKGROUND_FIELDS
            for field in BACKGROUND_FIELDS:
                setattr(character, field, sanitize_data(getattr(form, field).data))
            error = import_system_stats(character, form)
            if error:
                flash(error)
                return render_import_page(form=form), 400
            character.pets.extend(pets)
            character.armor = str(character.armorValue())
            db.session.add(character)
            # Its mounts carry for it again (#537): a link in the file names the other site's pet, so it is made anew.
            from app.lib.mounts import link_mounts
            character.containers = json.dumps([{key: value for key, value in container.items() if key != 'mount'}
                                               for container in json.loads(character.containers)])
            link_mounts(character)
            db.session.commit()

            print('submitted', file=sys.stderr)
            print(form.items.data, file=sys.stderr)

            return redirect(url_for('main.character', username=current_user.username, url_name=url_name))

        else:
            print('not submitted', file=sys.stderr)
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            print(" ".join(error_messages), file=sys.stderr)
    else:
        return redirect(url_for('main.index'))
    return render_import_page(form=form)


# Read a Markdown character sheet into the JSON export shape. The import page
# then submits it through new_from_json like any JSON file, with the same checks.
@main.post('/new_from_json/markdown')
@login_required
def parse_markdown_character():
    from app.lib.character_markdown import parse_character, MAX_MARKDOWN
    request.max_content_length = MAX_MARKDOWN * 4 + 64 * 1024
    if not FlaskForm().validate_on_submit():
        return jsonify(error='Invalid CSRF token.'), 400
    try:
        return jsonify(parse_character(request.form.get('markdown', '')))
    except ValueError as error:
        return jsonify(error=str(error)), 400


def string_to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 't', 'yes', 'y', '1')
    return bool(value)


@main.route('/new_character/', methods=['GET', 'POST'])
def new_character():
    if not current_user.is_authenticated:
        return make_response("Unauthorized")
    # Creation is the game system's (kettlewright): Cairn's 2e pages, in system/cairn/web.
    from kettlewright.web import plugin
    return plugin().creation_page('2e')


@main.route('/new_character/barebones/', methods=['GET'])
@login_required
def new_barebones_character():
    from kettlewright.web import plugin
    return plugin().creation_page('barebones')


@main.route('/users/<username>/characters/<url_name>/')
def character(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()

    party = Party.query.filter_by(id=character.party_id).first()

    is_owner = False
    if current_user.is_authenticated:
        is_owner = current_user.id == user.id

    if party:
        party_name = party.name
        owner_username = User.query.filter_by(id=party.owner).first().username
        party_url = 'users/' + owner_username + \
            '/parties/' + party.party_url + '/'
        party_description = party.description
        print('party:', party_name, party_url,
              party_description, file=sys.stderr)
    else:
        party_name = None
        party_url = None
        party_description = None
        
    scarlist = load_scars()
    portrait_src = character_portrait_link(character)
    items_json = json.dumps(character.items)
    inventory = Inventory(character)
    inventory.select(0)
    inventory.decorate()
    return render_template('main/character_view.html', character=character, items_json=items_json, containers_json=json.dumps(character.containers), username=username, url_name=url_name, party=party, party_url=party_url, party_name=party_name, party_description=party_description, base_url=base_url, is_owner=is_owner, can_edit_sheet=can_edit_character(character), scarlist=scarlist, portrait_src=portrait_src, inventory=inventory, stat_form=FlaskForm())


@main.route('/users/<username>/characters/<url_name>/print/')
def print_character(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    party = Party.query.filter_by(id=character.party_id).first()
    inventory = Inventory(character)
    return render_template('main/character_print.html', character=character, items_json=json.dumps(character.items), 
                           containers_json=json.dumps(character.containers), party=party, inventory=inventory)


@main.get('/users/<username>/characters/<url_name>/print/landscape.pdf')
def print_character_landscape(username, url_name):
    return _print_character_pdf(username, url_name, 'landscape')


@main.get('/users/<username>/characters/<url_name>/print/portrait.pdf')
def print_character_portrait(username, url_name):
    return _print_character_pdf(username, url_name, 'portrait')


def _print_character_pdf(username, url_name, orientation):
    from kettlewright.web import plugin
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(owner=user.id, url_name=url_name).first_or_404()
    party = db.session.get(Party, character.party_id) if character.party_id else None
    export_attributes = request.args.get('export_attributes', '1') != '0'
    # Barebones characters always get the Barebones sheet, whichever orientation link was used.
    paper = 'barebones-a4' if character.is_barebones else f'{orientation}-a4'
    # The game system draws the sheet (kettlewright): Cairn's PDF sheets.
    sheet = plugin().character_sheet(character, party, orientation, export_attributes=export_attributes)
    response = send_file(sheet.draw(), mimetype='application/pdf',
                         download_name=f'{character.url_name}-{paper}.pdf', as_attachment=False)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@main.route('/delete-character/<int:character_id>/', methods=['POST', 'GET'])
@login_required
def delete(character_id):
    character = db.get_or_404(Character, character_id)

    if character.owner != current_user.id:
        flash('You do not have permission to delete this character.', 'error')
        return redirect(url_for('main.characters', username=current_user.username))

    # remove character from party if in one
    if character.party_id:
        party = Party.query.filter_by(id=character.party_id).first()
        party_members = [] if party.members is None else json.loads(
            party.members)
        if character.id in party_members:
            party_members.remove(character.id)
            party.members = json.dumps(party_members)

    db.session.delete(character)
    db.session.commit()

    # flash('Character deleted successfully.', 'success')
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = url_for('main.characters', username=current_user.username)
    return response


@main.route('/users/<username>/parties/', methods=['GET', 'POST'])
@login_required
def parties(username):
    """The old Parties page: the Campaigns page's Parties view, every party at once."""
    return redirect(url_for('campaigns.index', view='parties'))


@main.route('/users/<ownername>/parties/<party_url>/tools/', methods=['POST', 'GET'])
@ login_required
def party_tools(ownername, party_url):
    party_id = Party.query.filter_by(
        owner_username=ownername, party_url=party_url).first().id
    return render_template('main/party_tools.html', username=current_user.username, user_id=current_user.id, party_id=party_id)


@main.route('/delete-party/<int:party_id>/', methods=['POST'])
@login_required
def delete_party(party_id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    from app.lib.campaign_parties import delete_party as remove_party
    party = db.get_or_404(Party, party_id)
    if party.owner != current_user.id:
        return redirect(url_for('campaigns.index'))
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(400)
    campaign_id = party.campaign_id
    remove_party(party)
    db.session.commit()
    return redirect(url_for('campaigns.lobby', campaign_id=campaign_id) if campaign_id else url_for('campaigns.index'))


def translate_events_data(node, path=()):
    if path[-2:] in _EVENTS_UNTRANSLATED_PATHS:
        return node
    if isinstance(node, dict):
        translated = {key: node[key] if key in _EVENTS_UNTRANSLATED_KEYS
                      else translate_events_data(node[key], path + (key,))
                      for key in node}
        if path == ('Realm', 'Topography') and translated != node:
            # Forest generation and terrain synonyms must use source identities.
            translated['TerrainKeys'] = {
                shown: source
                for difficulty, table in node['Terrain'].items()
                for source, shown in zip(table['Terrain'], translated['Terrain'][difficulty]['Terrain'])
            }
        return translated
    if isinstance(node, list):
        return [translate_events_data(item, path) for item in node]
    if isinstance(node, str) and node:
        for suffix, context in _EVENTS_TRANSLATION_CONTEXTS.items():
            if path[-len(suffix):] == suffix:
                return translate_term(node, context)
        return _(node)
    return node


@ main.route('/tools/', methods=['GET'])
def tools():
    events_data = translate_events_data(_system().content.load('events'))
    backgrounds = load_backgrounds()
    from kettlewright.web import plugin
    gear_packages = plugin().gear_packages  # The system's (kettlewright): Cairn's Barebones packages.
    warden_parties = Party.query.filter_by(owner=current_user.id).order_by(Party.name, Party.id).all() if current_user.is_authenticated else []
    from app.lib.monsters import localized_monster_catalog
    from app.models import Campaign
    generator_campaigns = Campaign.query.filter_by(owner_id=current_user.id).order_by(Campaign.name, Campaign.id).all() if current_user.is_authenticated else []
    return render_template('main/tools.html', events_data=json.dumps(events_data),pcgen_value="", backgrounds=backgrounds, barebones_packages=gear_packages(), warden_parties=warden_parties, monster_templates=localized_monster_catalog(), generator_campaigns=generator_campaigns, roll_form=FlaskForm())

@main.route('/tools/map/', methods=['GET'])
def tools_map():
    """A Tools result (realm, dungeon or forest) shown as a complete map, before saving anything. Open to
    everyone; signed-in Wardens save it to a module from here. The result comes from the Tools page in the
    browser (localStorage), so there is nothing to look up here."""
    return render_template('main/tools_map.html')


@main.route('/tools/map/tables', methods=['GET'])
def tools_map_tables():
    """The tables a Tools map is drawn from (public, like the Tools page itself)."""
    from app.lib.generator_tables import generator_tables
    return jsonify(generator_tables(maps_only=True))


@main.route('/reload-page')
def reload_page():
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = request.args.get("link")
    return response

# I18N support

@main.route('/select-language')
def select_language():
    response = make_response("Setting language")
    lang = request.args.get('lang')
    if lang != None and lang != "":
        expire_date = datetime.datetime.now()
        expire_date = expire_date + datetime.timedelta(days=180)
        response.set_cookie("kw_lang", lang, expires=expire_date)        
    response.headers["HX-Redirect"] = request.headers['Referer']
    return response

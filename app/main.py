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
from app.lib import load_scars, character_portrait_link, Inventory, sanitize_data, sanitize_json_content, load_version, load_backgrounds, load_traits, load_bonds, load_omens, DummyCharacter
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

marketplace_file_path = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'static', 'json', 'marketplace.json')

omens_file_path = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'static', 'json', 'omens.json')
with open(omens_file_path, 'r') as file:
    omens_data = json.load(file)

scars_file_path = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'static', 'json', 'scars.json')
with open(scars_file_path, 'r') as file:
    scars_data = json.load(file)




@main.route('/')
def index():
    # Discord opens an Activity at "/" with its launch parameters (#423).
    if request.args.get('frame_id') and request.args.get('instance_id'):
        return redirect(url_for('activity.launch', **request.args.to_dict()))
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
                    getattr(form, field).data = int(getattr(form, field).data)
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
            character.pets.extend(pets)
            character.armor = str(character.armorValue())
            db.session.add(character)
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
    form = CharacterForm()
    if not current_user.is_authenticated:
        return make_response("Unauthorized")
    # form = CharacterForm()
    # if current_user.is_authenticated:
    #     if form.validate_on_submit():
    #         # sanitize custom fields
    #         form.custom_background.data = bleach.clean(
    #             form.custom_background.data)
    #         form.custom_name.data = bleach.clean(form.custom_name.data)

    #         # create url_name
    #         if form.name.data == 'Custom':
    #             url_name = create_unique_url_name(form.custom_name.data)
    #             form.name.data = form.custom_name.data
    #         else:
    #             url_name = create_unique_url_name(form.name.data)

    #         if form.background.data == 'Custom':
    #             form.background.data = form.custom_background.data

    #         # add character to db

    #         custom_image = form.custom_image.data.lower() == 'true'
    #         new_character = Character(
    #             name=form.name.data, owner_username=current_user.username, background=form.background.data, owner=current_user.id, url_name=url_name, custom_background=form.custom_background.data, custom_name=form.custom_name.data, items=form.items.data, containers=form.containers.data,
    #             strength_max=form.strength_max.data, dexterity_max=form.dexterity_max.data, willpower_max=form.willpower_max.data, hp_max=form.hp_max.data, strength=form.strength_max.data, dexterity=form.dexterity_max.data, armor=form.armor.data, scars="",
    #             willpower=form.willpower_max.data, hp=form.hp_max.data, deprived=False, description=form.description.data, traits=form.traits.data, notes=form.notes.data, gold=form.gold.data, bonds=form.bonds.data, omens=form.omens.data, custom_image=custom_image, image_url=form.image_url.data)
    #         db.session.add(new_character)
    #         db.session.commit()

    #        # return redirect(url_for('main.index'))
    #         return redirect(url_for('main.character', username=current_user.username, url_name=url_name))
    #     else:
    #         print('not submitted', file=sys.stderr)
    #         error_messages = []
    #         for field, errors in form.errors.items():
    #             for error in errors:
    #                 error_messages.append(f"{field}: {error}")
    #         flash(" ".join(error_messages))

    #     # json_file_path = os.path.join(os.path.dirname(os.path.abspath(
    #     #     __file__)), 'static', 'json', 'background_data.json')
    #     backgrounds_file_path = os.path.join(os.path.dirname(os.path.abspath(
    #         __file__)), 'static', 'json', 'backgrounds', 'background_data.json')
    #     with open(backgrounds_file_path, 'r') as file:
    #         background_data = json.load(file)

    #     traits_file_path = os.path.join(os.path.dirname(os.path.abspath(
    #         __file__)), 'static', 'json', 'traits.json')
    #     with open(traits_file_path, 'r') as file:
    #         traits_data = json.load(file)

    #     bonds_file_path = os.path.join(os.path.dirname(os.path.abspath(
    #         __file__)), 'static', 'json', 'bonds.json')
    #     with open(bonds_file_path, 'r') as file:
    #         bonds_data = json.load(file)

    #     with open(marketplace_file_path, 'r') as file:
    #         marketplace_data = json.load(file)

    #     image_folder = os.path.join(os.path.dirname(os.path.abspath(
    #         __file__)), 'static', 'images', 'portraits')
    #     image_files = [f for f in os.listdir(
    #         image_folder) if f.endswith('.webp')]
        
    # portrait_src = urllib.parse.quote_plus("/static/images/portraits/default-portrait.webp")
    portrait_src = "default-portrait.webp"
    ps = request.args.get("src")
    if ps != None and ps != "":
        portrait_src = ps
    custom_image = request.args.get("custom_image")
    # Created for a party: its campaign's backgrounds, and the character joins it on save.
    from app.lib.campaign_backgrounds import party_for_code, use_party_backgrounds
    code = (request.args.get('party') or '').strip()
    party = party_for_code(code)
    if party is not None:
        use_party_backgrounds(party)
        form = CharacterForm()
        form.party_code.data = party.join_code
    custom_fields = {}
    custom_fields['background'] = None
    custom_fields['traits'] = load_traits()
    custom_fields['bonds'] = load_bonds()
    custom_fields['omens'] = load_omens()
    custom_fields['gold'] = 0
    custom_fields['bonus_gold_t1'] = 0
    custom_fields['bonus_gold_t2'] = 0
    custom_fields['bonus_gold_bond'] = 0
    custom_fields['armor'] = 0
    character = DummyCharacter()
    custom_fields['inventory'] = Inventory(character)
    custom_fields['inventory'].decorate()
    custom_fields['items'] = '[]'
    custom_fields['bond_items'] = '[]'
    custom_fields['armor'] = '0'
    custom_fields['portrait_src'] = portrait_src
    custom_fields['custom_image'] = 'false'
    
    return render_template('main/character_create.html', portrait_src = portrait_src, custom_image=custom_image, 
                           form=form, custom_fields=custom_fields, party=party, party_code_error=bool(code) and party is None)


@main.route('/new_character/barebones/', methods=['GET'])
@login_required
def new_barebones_character():
    from app.blueprints.charcreo_barebones import creation_page
    return creation_page()


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
    from app.lib.character_pdf import character_sheet
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(owner=user.id, url_name=url_name).first_or_404()
    party = db.session.get(Party, character.party_id) if character.party_id else None
    export_attributes = request.args.get('export_attributes', '1') != '0'
    # Barebones characters always get the Barebones sheet, whichever orientation link was used.
    paper = 'barebones-a4' if character.is_barebones else f'{orientation}-a4'
    response = send_file(character_sheet(character, party, orientation, export_attributes=export_attributes).draw(), mimetype='application/pdf',
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
    """Parties live inside campaigns now: the old Parties page opens Campaigns."""
    return redirect(url_for('campaigns.index'))


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
    events_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'static', 'json', 'generators', 'event_data.json')
    with open(events_path, 'r') as file:
        events_data = json.load(file)
    events_data = translate_events_data(events_data)
    backgrounds = load_backgrounds()
    from app.lib.barebones import gear_packages
    warden_parties = Party.query.filter_by(owner=current_user.id).order_by(Party.name, Party.id).all() if current_user.is_authenticated else []
    from app.lib.monsters import monster_catalog
    from app.models import Campaign
    generator_campaigns = Campaign.query.filter_by(owner_id=current_user.id).order_by(Campaign.name, Campaign.id).all() if current_user.is_authenticated else []
    return render_template('main/tools.html', events_data=json.dumps(events_data),pcgen_value="", backgrounds=backgrounds, barebones_packages=gear_packages(), warden_parties=warden_parties, monster_templates=monster_catalog(), generator_campaigns=generator_campaigns, roll_form=FlaskForm())

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

from flask import Blueprint, render_template, redirect, url_for, jsonify, flash, request, make_response
from flask_login import login_required, current_user
from .models import User, Character, Party
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


@main.route('/users/<username>/characters/')
@login_required
def characters(username):
    user = User.query.filter_by(username=username).first_or_404()
    characters = Character.query.filter_by(owner=user.id).all()
    characters_sorted = sorted(
        characters, key=lambda x: x.created_at, reverse=True)
    for character in characters_sorted:
        if character.custom_image == False:
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
def new_from_json():
    form = CharacterJSONForm()
    user = current_user.username
    if current_user.is_authenticated:
        if form.validate_on_submit():
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
                items=sanitize_json_content(form.items.data or ''),
                containers=sanitize_json_content(form.containers.data or ''),
                custom_name=sanitize_data(form.custom_name.data),
                custom_background=sanitize_data(form.custom_background.data),
                deprived=string_to_bool(
                    sanitize_data(form.deprived.data or False)),
                traits=sanitize_data(form.traits.data or ''),  # New field
                armor=sanitize_data(form.armor.data or '')  # New field
            )

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
    return render_template('main/new_from_json.html', form=form)


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
        
    portrait_src = urllib.parse.quote_plus("/static/images/portraits/default-portrait.webp")
    ps = request.args.get("src")
    if ps != None and ps != "":
        portrait_src = ps
    custom_image = request.args.get("custom_image")
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
    
    return render_template('main/character_create.html', portrait_src = portrait_src, custom_image=custom_image, 
                           form=form, custom_fields=custom_fields)


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
    return render_template('main/character_view.html', character=character, items_json=items_json, containers_json=json.dumps(character.containers), username=username, url_name=url_name, party=party, party_url=party_url, party_name=party_name, party_description=party_description, base_url=base_url, is_owner=is_owner, scarlist=scarlist, portrait_src=portrait_src, inventory=inventory)


@main.route('/users/<username>/characters/<url_name>/print/')
def print_character(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    party = Party.query.filter_by(id=character.party_id).first()
    inventory = Inventory(character)
    return render_template('main/character_print.html', character=character, items_json=json.dumps(character.items), 
                           containers_json=json.dumps(character.containers), party=party, inventory=inventory)


@main.route('/delete-character/<int:character_id>/', methods=['POST', 'GET'])
@login_required
def delete(character_id):
    character = Character.query.get_or_404(character_id)

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


def generate_unique_join_code():
    while True:
        join_code = os.urandom(8).hex()
        existing_party = Party.query.filter_by(join_code=join_code).first()
        if existing_party is None:
            break

    return join_code


def generate_unique_party_url(name):
    # check that owner doesn't already have a party with the same name
    party_url = slugify(name)
    # filter for both party_url and owner
    existing_party = Party.query.filter_by(
        party_url=party_url, owner=current_user.id).first()
    if existing_party is not None:
        counter = 1
        while True:
            party_url = slugify(name) + str(counter)
            existing_party = Party.query.filter_by(
                party_url=party_url, owner=current_user.id).first()
            if existing_party is None:
                break
            counter += 1

    return party_url


@main.route('/users/<username>/parties/',  methods=['GET', 'POST'])
@login_required
def parties(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = PartyForm()

    if username != current_user.username:
        return redirect(url_for('main.index'))
    if current_user.is_authenticated:
        # get all parties owned by the user
        parties = Party.query.filter_by(owner=user.id).all()
        parties_sorted = sorted(
            parties, key=lambda x: x.created_at, reverse=True)

        # go through each character the user owns, and if they are in a party, add the party to the list of parties
        characters = Character.query.filter_by(owner=user.id).all()
        for character in characters:
            if character.party_id:
                party = Party.query.filter_by(id=character.party_id).first()
                if party not in parties_sorted:
                    parties_sorted.append(party)

        # for each party in parties_sorted, get the member names, and add them to the party object
        for party in parties_sorted:
            party.member_names = ""
            party.member_portraits = []
            if party.members and party.members.strip():
                members_list = json.loads(party.members)
                for member in members_list:
                    character = Character.query.filter_by(id=member).first()
                    if character:
                        party.member_names += character.name + ", "
                        if not character.custom_image:
                            character.portrait_src = url_for(
                                'static', filename='images/portraits/' + character.image_url)
                        else:
                            character.portrait_src = character.image_url
                        party.member_portraits.append(character.portrait_src)
            if party.member_names == "":
                party.member_names = "No members yet."
            else:
                party.member_names = party.member_names[:-2]

        if form.validate_on_submit():
            party_url = generate_unique_party_url(
                sanitize_data(form.name.data))
            join_code = generate_unique_join_code()
            new_party = Party(name=sanitize_data(form.name.data),
                              owner=current_user.id, owner_username=current_user.username, description=sanitize_data(form.description.data), join_code=join_code, party_url=party_url, items='[]', containers='[{"name":"Main","slots":10,"id":0}]')
            db.session.add(new_party)
            db.session.commit()
            # redirect to the new party page
            return redirect(url_for('party.party_view', ownername=username, party_url=party_url))

    return render_template('main/parties.html', form=form, parties=parties_sorted, base_url=base_url)


@main.route('/users/<ownername>/parties/<party_url>/tools/', methods=['POST', 'GET'])
@ login_required
def party_tools(ownername, party_url):
    party_id = Party.query.filter_by(
        owner_username=ownername, party_url=party_url).first().id
    return render_template('main/party_tools.html', username=current_user.username, user_id=current_user.id, party_id=party_id)


@ main.route('/delete-party/<int:party_id>/', methods=['POST', 'GET'])
@ login_required
def delete_party(party_id):
    party = Party.query.get_or_404(party_id)

    if party.owner != current_user.id:
        return redirect(url_for('main.parties', username=current_user.username))

    # remove party from all characters in the party
    characters = Character.query.filter_by(party_id=party.id).all()
    for character in characters:
        character.party_id = None
        character.party_code = None

    db.session.delete(party)
    db.session.commit()

    # flash('Party deleted successfully.', 'success')
    return redirect(url_for('main.parties', username=current_user.username))


@ main.route('/tools/', methods=['GET'])
def tools():
    events_path = os.path.join(os.path.dirname(os.path.abspath(
        __file__)), 'static', 'json', 'party_events', 'event_data.json')
    with open(events_path, 'r') as file:
        events_data = json.load(file)
    backgrounds = load_backgrounds()
    return render_template('main/tools.html', events_data=json.dumps(events_data),pcgen_value="", backgrounds=backgrounds)

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


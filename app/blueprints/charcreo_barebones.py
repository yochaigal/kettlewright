# Cairn Barebones Edition character creation (#292)
#
# The whole form is re-rendered on every change. Rolled item groups are kept in
# hidden JSON fields so rerolling one table (say, the weapon) keeps the random
# results of the others, such as a background's spellbook.

import json
import urllib.parse

import bleach
from flask import Blueprint, render_template, request, make_response, url_for, abort
from flask_login import current_user, login_required

from app.lib.barebones import (GEAR_BACKGROUND, armor_items, background_items, background_name, barebones_data,
                               build_inventory, gear_items, gear_packages, package_items, roll_index, roll_name,
                               slots_used, starting_items, weapon_items)
from app.lib.char_utils import DummyCharacter, TraitValue, traits_text
from app.lib.data import load_images, load_traits
from app.lib.inventory import Inventory
from app.lib.roll import roll_list, roll_multi_dice
from app.models import Character, db
from app.models.character import EDITION_BAREBONES
from app.lib.dice_feedback import queue_dice

charcreo_barebones = Blueprint('charcreo_barebones', __name__)

TRAIT_NAMES = ("Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice")
ATTRIBUTES = {'str': ('strength', 6, 3), 'dex': ('dexterity', 6, 3), 'wil': ('willpower', 6, 3), 'hp': ('hp', 6, 1)}
# Hidden JSON item groups, in inventory order.
GROUPS = ('start_items', 'bkg_items', 'armor_items', 'weapon_items', 'gear_items', 'package_items')
TABLES = {'background': ('backgrounds', 'bkg_items', background_items),
          'armor': ('armor', 'armor_items', armor_items),
          'weapon': ('weapons', 'weapon_items', weapon_items),
          'gear': ('gear', 'gear_items', gear_items)}
DEFAULT_PORTRAIT = 'default-portrait.webp'


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _items(value):
    try:
        items = json.loads(value or '[]')
    except ValueError:
        return []
    return items if isinstance(items, list) else []


def read_state(data):
    state = {key: (data.get(key) or '').strip() for key in ('name', 'gear_source', 'portrait_src', 'custom_image')}
    for key in ('age', 'strength', 'dexterity', 'willpower', 'hp', 'gold', 'background', 'armor', 'weapon', 'gear'):
        state[key] = _int(data.get(key))
    for name in TRAIT_NAMES:
        value = data.get(name) or ''
        state[name] = value if value in load_traits()[name] else ''
    for group in GROUPS:
        state[group] = _items(data.get(group))
    if state['gear_source'] not in gear_packages():
        state['gear_source'] = GEAR_BACKGROUND
    state['portrait_src'] = state['portrait_src'] or DEFAULT_PORTRAIT
    state['custom_image'] = 'true' if state['custom_image'] == 'true' else 'false'
    return state


def set_table(state, field, index):
    table, group, resolve = TABLES[field]
    state[field] = index
    state[group] = resolve(index) if index else []


def set_package(state, source):
    state['gear_source'] = source
    state['package_items'] = package_items(source) if source != GEAR_BACKGROUND else []


def roll_field(state, field, animate=False):
    """Roll one field; with animate, the dice also roll in 3D (single rolls only, not Roll All)."""
    def dice(faces, count):
        values, total = roll_multi_dice(faces, count)
        if animate:
            queue_dice(values, faces)
        return total
    if field in TABLES:
        set_table(state, field, roll_index(TABLES[field][0]))
    elif field in ATTRIBUTES:
        key, faces, count = ATTRIBUTES[field]
        state[key] = dice(faces, count)
    elif field == 'name':
        state['name'] = roll_name()
    elif field == 'age':
        state['age'] = dice(20, 2) + 10
    elif field == 'gold':
        state['gold'] = dice(6, 3)
    elif field == 'traits':
        for name in TRAIT_NAMES:
            state[name] = roll_list(load_traits()[name])
    elif field == 'portrait':
        state['portrait_src'] = roll_list(load_images())
        state['custom_image'] = 'false'
    else:
        abort(404)


def roll_missing(state, everything=False):
    if everything or not state['start_items']:
        state['start_items'] = starting_items()
    for field in ('name', 'age', 'str', 'dex', 'wil', 'hp', 'gold'):
        key = ATTRIBUTES[field][0] if field in ATTRIBUTES else field
        if everything or not state[key]:
            roll_field(state, field)
    if everything or not all(state[name] for name in TRAIT_NAMES):
        for name in TRAIT_NAMES:
            if everything or not state[name]:
                state[name] = roll_list(load_traits()[name])
    for field in TABLES:
        if everything or not state[field]:
            roll_field(state, field)
    if everything or state['portrait_src'] == DEFAULT_PORTRAIT:
        roll_field(state, 'portrait')


def selected_groups(state):
    if state['gear_source'] != GEAR_BACKGROUND:
        return [state['package_items']]
    return [state[group] for group in GROUPS if group != 'package_items']


def background_label(state):
    if state['gear_source'] != GEAR_BACKGROUND:
        return state['gear_source']
    return background_name(state['background']) if state['background'] else ''


def traits_sentence(state):
    if not all(state[name] for name in TRAIT_NAMES):
        return ''
    return traits_text(state['age'] or '', [TraitValue(name, state[name]) for name in TRAIT_NAMES])


def render_form(state):
    items, containers = build_inventory(selected_groups(state))
    character = DummyCharacter()
    character.items = json.dumps(items)
    character.containers = json.dumps(containers)
    inventory = Inventory(character)
    inventory.select(0)
    inventory.decorate()
    armor = min(3, sum(value for item in items for value in (1, 2, 3) if f'{value} Armor' in item['tags']))
    custom_fields = {'inventory': inventory, 'portrait_src': state['portrait_src'],
                     'custom_image': state['custom_image']}
    return render_template('partial/barebones/form.html', state=state, data=barebones_data(),
                           traits=load_traits(), trait_names=TRAIT_NAMES, packages=gear_packages(),
                           groups=GROUPS, armor=armor, slots=slots_used(items), traits_text=traits_sentence(state),
                           custom_fields=custom_fields)


def new_state():
    state = read_state({})
    state['start_items'] = starting_items()
    return state


def creation_page():
    return render_template('main/character_create_barebones.html', form_html=render_form(new_state()))


@charcreo_barebones.post('/charcreo/barebones/change/<field>')
def change(field):
    state = read_state(request.form)
    if field in TABLES:
        set_table(state, field, state[field])
    elif field == 'gear_source':
        set_package(state, state['gear_source'])
    return render_form(state)


@charcreo_barebones.post('/charcreo/barebones/roll/<field>')
def roll(field):
    state = read_state(request.form)
    if field in ('all', 'remaining'):
        roll_missing(state, everything=field == 'all')
    else:
        roll_field(state, field, animate=True)
    return render_form(state)


@charcreo_barebones.post('/charcreo/barebones/swap')
def swap():
    state = read_state(request.form)
    first, second = (ATTRIBUTES.get(request.form.get(f'swap_attribute_{n}', '')) for n in (1, 2))
    if first and second and first is not ATTRIBUTES['hp'] and second is not ATTRIBUTES['hp']:
        state[first[0]], state[second[0]] = state[second[0]], state[first[0]]
    return render_form(state)


def validation_errors(state):
    """Same checks and messages as the Second Edition creator."""
    errors = []
    if not background_label(state):
        errors.append('Required background selection')
    if not state['name']:
        errors.append('Required character name')
    for key, label in (('strength', 'STR'), ('dexterity', 'DEX'), ('willpower', 'WIL'), ('hp', 'HP')):
        if not state[key] or state[key] < 1:
            errors.append(f'Required {label} attribute')
    return errors


@charcreo_barebones.post('/charcreo/barebones/save')
@login_required
def save():
    from app.main import create_unique_url_name
    state = read_state(request.form)
    state['name'] = bleach.clean(state['name'])[:64]
    errors = validation_errors(state)
    if errors:
        # The Second Edition error popup, shown in #dialog-anchor.
        return render_template('partial/modal/save_char_error.html',
                               error='<ul>' + ''.join(f'<li>{error}</li>' for error in errors) + '</ul>')
    items, containers = build_inventory(selected_groups(state))
    image_url = state['portrait_src']
    if state['custom_image'] == 'false' and image_url not in load_images(include_categories=True):
        image_url = DEFAULT_PORTRAIT
    url_name = create_unique_url_name(state['name'])
    character = Character(
        name=state['name'], background=background_label(state), custom_name='', custom_background='',
        owner=current_user.id, owner_username=current_user.username, url_name=url_name,
        edition=EDITION_BAREBONES, items=json.dumps(items), containers=json.dumps(containers),
        strength=state['strength'], strength_max=state['strength'],
        dexterity=state['dexterity'], dexterity_max=state['dexterity'],
        willpower=state['willpower'], willpower_max=state['willpower'],
        hp=state['hp'], hp_max=state['hp'], gold=state['gold'] or 0, deprived=False,
        description='', traits=traits_sentence(state), notes='', bonds='', omens='', scars='',
        background_table1_question='', background_table1_answer='',
        background_table2_question='', background_table2_answer='',
        custom_image=state['custom_image'] == 'true', image_url=image_url)
    character.armor = str(character.armorValue())
    db.session.add(character)
    db.session.commit()
    response = make_response('Redirecting')
    response.headers['HX-Redirect'] = url_for('main.character', username=current_user.username, url_name=url_name)
    return response

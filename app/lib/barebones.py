"""Cairn Barebones Edition character rules (#292).

Barebones creation is fully random: a d100 name and surname, 3d6 attributes,
d6 HP, d10 traits, a d100 background with three items, d6 armor and weapon
rolls, one d100 additional gear roll, 3d6 gold, rations and a torch. A gear
package (Fighter, Thief, Magic-User, Cleric) can replace all of the rolled gear.
"""
import json
import os
import random
import uuid
from functools import lru_cache

from .paths import app_static_path

GEAR_BACKGROUND = 'background'


@lru_cache(maxsize=1)
def _data():
    with open(os.path.join(app_static_path(), 'json', 'barebones.json'), 'r') as file:
        return json.load(file)


@lru_cache(maxsize=1)
def _spellbooks():
    with open(os.path.join(app_static_path(), 'json', 'generators', 'spellbooks.json'), 'r') as file:
        return {spell['name']: spell for spell in json.load(file)['Spellbooks']}


def barebones_data():
    return _data()


def gear_packages():
    return list(_data()['gear_packages'])


def roll_index(table):
    """Roll on a 1-based table; return the 1-based result."""
    return random.randint(1, len(_data()[table]))


def entry(table, index):
    rows = _data()[table]
    index = int(index)
    if not 1 <= index <= len(rows):
        raise ValueError(f'{table} roll out of range: {index}')
    return rows[index - 1]


def roll_name():
    names = _data()['names']
    return f"{random.choice(names)['name']} {random.choice(names)['surname']}"


def background_name(index):
    return entry('backgrounds', index)['name']


def spell_item(spell_name, kind='spellbook', petty=False):
    spell = _spellbooks().get(spell_name, {'name': spell_name, 'description': ''})
    description = spell.get('description', '')
    if spell.get('personality'):
        description = f"{description} *{spell['personality']}*".strip()
    label = 'Scroll' if kind == 'scroll' else 'Spellbook'
    return {'name': f'{label} ({spell["name"]})', 'tags': ['petty'] if petty else [],
            'description': description}


def resolve(item):
    """Turn a table item into concrete inventory items, rolling any 'random' parts."""
    if 'spell' in item:
        return [spell_item(item['spell'], item.get('kind', 'spellbook'), item.get('petty', False))]
    match item.get('random'):
        case 'spellbook' | 'scroll':
            spell = random.choice(list(_spellbooks()))
            return [spell_item(spell, item['random'], item.get('petty', item['random'] == 'scroll'))]
        case 'gear':
            return gear_items(roll_index('gear'))
    resolved = {key: value for key, value in item.items() if key != 'containers'}
    resolved['tags'] = list(item.get('tags', []))
    return [resolved]


def background_items(index):
    return [it for raw in entry('backgrounds', index)['items'] for it in resolve(raw)]


def armor_items(index):
    """Armor items; rolling 'None' grants an extra additional gear roll."""
    row = entry('armor', index)
    items = [it for raw in row['items'] for it in resolve(raw)]
    if row.get('extra_gear'):
        items.extend(gear_items(roll_index('gear')))
    return items


def weapon_items(index):
    row = entry('weapons', index)
    item = dict(row['item'])
    item['tags'] = list(item.get('tags', []))
    item['name'] = random.choice(row['options'])
    return [item]


def gear_items(index):
    return resolve(entry('gear', index))


def package_items(name):
    package = _data()['gear_packages'].get(name)
    if package is None:
        raise ValueError(f'Unknown gear package: {name}')
    return [it for raw in package['items'] for it in resolve(raw)]


def starting_items():
    return [dict(item, tags=list(item['tags'])) for item in _data()['starting_gear']]


def _containers_for(name):
    """Carts and wagons carry extra slots; look up their capacity by item name."""
    for row in _data()['gear']:
        for container in row.get('containers', []):
            if container['name'] == name:
                return container
    return None


def build_inventory(item_groups):
    """Flatten item groups into stored item and container JSON for a new character.

    Items are written directly rather than through Inventory.create_item: a
    Barebones PC can start over ten slots, and Cairn handles that at the table
    (an overloaded PC is at 0 HP), so nothing is silently dropped.
    """
    containers = [{'name': 'Main', 'slots': 10, 'id': 0}]
    items = []
    for group in item_groups:
        for raw in group:
            item = {'id': uuid.uuid4().hex, 'name': raw['name'], 'tags': list(raw.get('tags', [])),
                    'location': 0, 'description': raw.get('description', '')}
            if 'uses' in item['tags']:
                item['uses'] = item['max_uses'] = int(raw.get('uses', 1))
            if not any(tag in item['tags'] for tag in ('1 Armor', '2 Armor', '3 Armor')):
                item['armor_active'] = False
            items.append(item)
            container = _containers_for(raw['name'])
            if container:
                containers.append({'name': container['name'], 'slots': container['slots'],
                                   'id': len(containers)})
    return items, containers


def slots_used(items):
    used = 0
    for item in items:
        tags = item.get('tags', [])
        if 'petty' in tags:
            continue
        used += 2 if 'bulky' in tags else 1
    return used


def generate_character(package=None):
    """Roll a complete Barebones PC for the Tools generator.

    Returns the same pair as the 2e generator: an object for the plain-text
    template and the JSON snapshot used by the preview, print, export and save
    actions. Bonds, omens and background tables stay empty, as Barebones has none.
    """
    from app.lib.char_utils import AttrsValue, GeneratedCharacter, TraitValue, item_text, traits_text
    from app.lib.data import load_traits

    if package is not None and package not in _data()['gear_packages']:
        raise ValueError(f'Unknown gear package: {package}')
    if package:
        background = package
        groups = [package_items(package)]
    else:
        index = roll_index('backgrounds')
        background = background_name(index)
        groups = [starting_items(), background_items(index), armor_items(roll_index('armor')),
                  weapon_items(roll_index('weapons')), gear_items(roll_index('gear'))]
    items, containers = build_inventory(groups)
    for item in items:
        item['title'] = item_text(item)

    genchar = GeneratedCharacter()
    genchar.name = roll_name()
    genchar.background_name = background
    genchar.items = items
    genchar.containers = containers
    genchar.attributes = AttrsValue()
    genchar.attributes.str, genchar.attributes.dex, genchar.attributes.wil = (
        sum(random.randint(1, 6) for _ in range(3)) for _ in range(3))
    genchar.attributes.hp = random.randint(1, 6)
    genchar.attributes.armor = genchar.armor()
    genchar.traits = [TraitValue(name, random.choice(values)) for name, values in load_traits().items()]
    genchar.age = random.randint(1, 20) + random.randint(1, 20) + 10
    genchar.gold = sum(random.randint(1, 6) for _ in range(3))
    genchar.slots = slots_used(items)
    genchar.pets = []

    attrs = genchar.attributes
    snapshot = {
        'edition': 'barebones', 'name': genchar.name, 'background': background,
        'armor': attrs.armor, 'gold': genchar.gold, 'deprived': False,
        'strength': attrs.str, 'strength_max': attrs.str, 'dexterity': attrs.dex, 'dexterity_max': attrs.dex,
        'willpower': attrs.wil, 'willpower_max': attrs.wil, 'hp': attrs.hp, 'hp_max': attrs.hp,
        'traits': traits_text(genchar.age, genchar.traits),
        'description': '', 'bonds': '', 'omens': '', 'scars': '', 'notes': '',
        'background_table1_question': '', 'background_table1_answer': '',
        'background_table2_question': '', 'background_table2_answer': '',
        'items': [{key: value for key, value in item.items() if key != 'title'} for item in items],
        'containers': containers, 'image_url': 'default-portrait.webp', 'pets': [],
    }
    return genchar, json.dumps(snapshot)

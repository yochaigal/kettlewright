"""A compact character sheet beside the whiteboard in a Discord Activity (#423).

It shows what a player checks during play (HP, abilities, conditions, armor and the inventory
with its slots, uses and Fatigue) and makes the few changes they make at the table. The
changes are the Discord /kw actions (app/lib/discord_character.py), so the same rules apply.
"""
import json

from app.lib.discord_character import act
from app.lib.inventory import FATIGUE_NAME, Inventory

ACTIONS = ('stat', 'condition', 'fatigue', 'use', 'remove')
FIELDS = ('stat', 'value', 'condition', 'active', 'amount', 'item', 'resource')


def _item(item):
    tags = item.get('tags') or []
    entry = {'id': item['id'], 'name': item['name'], 'fatigue': item['name'] == FATIGUE_NAME,
             'bulky': 'bulky' in tags, 'petty': 'petty' in tags}
    for resource in ('uses', 'charges'):
        if resource in tags and resource in item:
            entry[resource] = item[resource]
            entry['max_' + resource] = item.get('max_' + resource, item[resource])
    return entry


def sheet(character):
    """What the compact sheet shows. Only for the character's owner: it includes the inventory."""
    inventory = Inventory(character)
    containers = [{'id': c['id'], 'name': c['name'], 'slots': int(c.get('slots') or 0),
                   'used': inventory.container_slots(c),
                   'items': [_item(i) for i in c['items'] if 'carrying' not in i]}
                  for c in inventory.containers if not c.get('on_the_ground')]
    stat = lambda field: {'value': getattr(character, field) or 0, 'max': getattr(character, field + '_max') or 0}
    return {'id': character.id, 'name': character.name,
            # Effective HP is 0 while panicked or with a full main inventory; `stored` is what −/+ change.
            'hp': {'value': character.hpValue()[0], 'stored': character.hp or 0, 'max': character.hp_max or 0},
            'strength': stat('strength'), 'dexterity': stat('dexterity'), 'willpower': stat('willpower'),
            'armor': character.armorValue(), 'deprived': bool(character.deprived),
            'panicked': bool(character.panicked), 'dead': bool(getattr(character, 'dead', False)),
            'containers': containers}


def apply(character, characters, data):
    """Make one change; raises ValueError (nothing changed) when it is not allowed."""
    action = data.get('action')
    if action not in ACTIONS:
        raise ValueError('Unknown action.')
    values = {key: data[key] for key in FIELDS if key in data}
    if action == 'remove':
        # The sheet only clears Fatigue; other items are removed on the full sheet.
        item = next((i for i in json.loads(character.items or '[]') if str(i['id']) == str(values.get('item'))), None)
        if item is None or item['name'] != FATIGUE_NAME:
            raise ValueError('Only Fatigue can be cleared here.')
    if action == 'use':
        values['remove-empty'] = False
    act(action, values, character, characters, lambda text: text)

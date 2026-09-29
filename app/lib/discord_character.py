"""Player sheet actions. The caller checks ownership and commits the interaction."""
import json

from werkzeug.exceptions import HTTPException

from app.lib.data import load_market, sanitize_data
from app.lib.inventory import FATIGUE_NAME, Inventory
from app.lib.inventory_slots import item_size
from app.lib.ground_items import drop_item, drop_container, ground_items, pickup_item
from app.models import Party, db


STATS = {'hp': 'hp', 'str': 'strength', 'dex': 'dexterity', 'wil': 'willpower'}
ITEM_ACTIONS = ('use', 'remove', 'drop', 'transfer', 'move')


def option(name, description, **kwargs):
    return dict(type=3, name=name, description=description, **kwargs)


def integer(name, description, minimum=0, maximum=9999, **kwargs):
    return dict(type=4, name=name, description=description, min_value=minimum,
                max_value=maximum, **kwargs)


def player_commands():
    item = option('item', 'Item in your inventory', required=True, autocomplete=True)
    container = option('container', 'Your destination container (default: main)', autocomplete=True)
    return [
        ('stat', 'Change a current stat on your selected character', [
            option('stat', 'Stat to change', required=True,
                   choices=[dict(name=s.upper(), value=s) for s in STATS]),
            integer('value', 'Amount to add/subtract, or the new value with mode:set', -9999, required=True),
            option('mode', 'Default: change by the amount', choices=[
                dict(name='Change by amount', value='change'), dict(name='Set value', value='set')])]),
        ('condition', 'Set or clear a condition on your character', [
            option('condition', 'Condition', required=True, choices=[
                dict(name=s.title(), value=s) for s in ('deprived', 'panicked')]),
            dict(type=5, name='active', description='True to apply, false to clear', required=True)]),
        ('fatigue', 'Add Fatigue to your main inventory', [integer('amount', 'How much Fatigue (default: 1)', 1, 10)]),
        ('inventory', 'Privately list your items and containers', [integer('page', 'Inventory page', 1)]),
        ('add', 'Add a catalog item or a custom item to your inventory', [
            option('name', 'Choose from the catalog or enter a custom name', required=True,
                   autocomplete=True, max_length=100), container,
            option('tags', 'Custom tags separated by commas, e.g. bulky,d8,uses', max_length=200),
            integer('uses', 'Remaining uses'), integer('charges', 'Remaining and maximum charges'),
            option('description', 'Item description', max_length=1000)]),
        ('use', 'Spend uses or charges; optionally remove the exhausted item', [item,
            integer('amount', 'How many to spend (default: 1)', 1),
            option('resource', 'Counter to spend (default: uses)', choices=[
                dict(name=s, value=s) for s in ('uses', 'charges')]),
            dict(type=5, name='remove-empty', description='Remove the item when this counter reaches zero')]),
        ('remove', 'Permanently remove an item (including Fatigue)', [item]),
        ('drop', 'Drop an item into the party’s on the ground container', [item,
            option('place', 'Where are you leaving this item?', required=True, max_length=200)]),
        ('drop-container', 'Drop a container with its contents on the ground', [
            option('container', 'Your container (not the main inventory)', required=True, autocomplete=True),
            option('place', 'Where are you leaving this container?', required=True, max_length=200)]),
        ('ground', 'List items on the ground and where they were dropped', [integer('page', 'Items page', 1)]),
        ('pickup', 'Pick up an item from the ground into your main inventory', [
            option('item', 'Item on the ground in this party', required=True, autocomplete=True)]),
        ('move', 'Move an item between your personal containers', [item,
            option('container', 'Your destination container', required=True, autocomplete=True)]),
        ('transfer', 'Give one of your items to another character in this party', [item,
            option('character', 'Recipient character (main inventory)', required=True, autocomplete=True)]),
        ('note', 'Append text to your character notes without replacing them', [
            option('text', 'Text to append; not posted to the channel', required=True, max_length=2000)]),
    ]


def number(value, minimum=0, maximum=9999):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'Enter a whole number between {minimum} and {maximum}.')
    return value


def clean_text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'Enter text between 1 and {limit} characters.')
    return sanitize_data(value.strip())


def choose_entry(entries, value):
    matches = [entry for entry in entries if str(entry['id']) == str(value)]
    if not matches:
        matches = [entry for entry in entries if entry['name'].casefold() == str(value).casefold()]
    if len(matches) != 1:
        raise ValueError('Choose a matching entry from autocomplete (names may not be unique).')
    return matches[0]


def player_choices(name, focused, values, character, characters):
    """Only called after checking live selection and party membership."""
    query = str(values.get(focused, '')).casefold()
    if name == 'add' and focused == 'name':
        candidates = [(i['name'], i['name']) for i in load_market()]
    elif name == 'pickup' and focused == 'item':
        party = db.session.get(Party, character.party_id)
        candidates = [(f'{i["name"][:30]} — {i.get("ground_place", "")[:28]} (#{i["id"]})', str(i['id']))
                      for i in ground_items(party)]
    elif name in ITEM_ACTIONS and focused == 'item':
        containers = {c['id']: c['name'] for c in json.loads(character.containers or '[]')}
        candidates = [(f'{i["name"][:40]} — {str(containers.get(i["location"], i["location"]))[:15]} (#{i["id"]})', str(i['id']))
                      for i in json.loads(character.items or '[]') if 'carrying' not in i]
    elif name in ('add', 'move', 'drop-container') and focused == 'container':
        candidates = [(f'{c["name"]} (#{c["id"]})', str(c['id']))
                      for c in json.loads(character.containers or '[]') if name != 'drop-container' or c['id'] != 0]
    elif name == 'transfer' and focused == 'character':
        candidates = [(f'{c.name} (#{c.id})', str(c.id)) for c in characters if c.id != character.id]
    else:
        candidates = []
    return [dict(name=label[:100], value=value) for label, value in candidates
            if query in label.casefold() or query == value.casefold()][:25]


def act(name, values, character, characters, safe_name):
    """Return private confirmation text, or None for non-player commands."""
    who = f'**{safe_name(character.name)}**'
    if name == 'drop-container':
        container = choose_entry(json.loads(character.containers or '[]'), values.get('container'))
        try:
            drop_container(character.id, character.owner, character.party_id, container['id'], values.get('place'))
        except HTTPException as error:
            raise ValueError(error.description) from error
        return f'{who}: dropped {safe_name(container["name"])} with its contents — {safe_name(values["place"].strip())}.'
    if name == 'ground':
        items = ground_items(db.session.get(Party, character.party_id))
        pages = max(1, (len(items) + 2) // 3)
        page = number(values.get('page', 1), 1, pages)
        lines = [f'• {safe_name(i["name"][:80])} — {safe_name(i.get("ground_place", "")[:200])}'
                 for i in items[(page - 1) * 3:page * 3]]
        return f'**on the ground** ({page}/{pages})\n' + ('\n'.join(lines) or 'No items.') + '\nUse /kw pickup to pick an item up.'
    if name == 'pickup':
        items = ground_items(db.session.get(Party, character.party_id))
        item = choose_entry(items, values.get('item'))
        try:
            pickup_item(character.id, character.owner, character.party_id, item['id'])
        except HTTPException as error:
            raise ValueError(error.description) from error
        return f'{who}: picked up {safe_name(item["name"])}.'
    if name == 'stat':
        field = STATS.get(values.get('stat'))
        if not field or values.get('mode', 'change') not in ('change', 'set'):
            raise ValueError('Choose HP, STR, DEX or WIL and a valid mode.')
        amount = number(values.get('value'), -9999)
        old = getattr(character, field) or 0
        value = amount if values.get('mode') == 'set' else old + amount
        maximum = getattr(character, field + '_max') or 0
        if not 0 <= value <= maximum:
            raise ValueError(f'The resulting {values["stat"].upper()} must be between 0 and {maximum}. '
                             'No changes saved; use mode:set to record the intended value.')
        setattr(character, field, value)
        text = f'{who}: {values["stat"].upper()} {old} → {value}/{maximum}.'
        if field == 'hp' and character.hpValue()[0] != value:
            text += f' Effective HP is {character.hpValue()[0]} because of panic or inventory load.'
        return text
    if name == 'condition':
        field, active = values.get('condition'), values.get('active')
        if field not in ('deprived', 'panicked') or type(active) is not bool:
            raise ValueError('Choose deprived or panicked and set active to true or false.')
        setattr(character, field, active)
        return f'{who}: {field.title()} {"applied" if active else "cleared"}. Effective HP: {character.hpValue()[0]}.'
    if name == 'note':
        text = clean_text(values.get('text'), 2000)
        notes = (character.notes or '') + ('\n' if character.notes else '') + text
        if len(notes) > 2000:
            raise ValueError('Character notes would exceed 2000 characters. Edit them in KW first; nothing was appended.')
        character.notes = notes
        return f'Note appended to {who} in KW.'
    if name not in (*ITEM_ACTIONS, 'add', 'fatigue', 'inventory'):
        return None
    inventory = Inventory(character)
    if name == 'inventory':
        items = json.loads(character.items or '[]')
        pages = max(1, (len(items) + 4) // 5)
        page = number(values.get('page', 1), 1, pages)
        containers = {c['id']: c['name'] for c in inventory.containers}
        lines = []
        for item in items[(page - 1) * 5:page * 5]:
            counters = ''.join(f' · {key}: {item[key]}' for key in ('uses', 'charges') if key in item)
            location = safe_name(containers.get(item['location'], str(item['location']))[:80])
            lines.append(f'• {safe_name(item["name"][:100])} — {location}{counters}')
        return (f'{who} — inventory ({page}/{pages})\n' + ('\n'.join(lines) or 'No items.') +
                '\nUse /kw use, remove, drop, move or transfer; autocomplete identifies each item.')
    if name in ('add', 'fatigue'):
        container = choose_entry(inventory.containers, values.get('container', '0'))
        amount = number(values.get('amount', 1), 1, 10) if name == 'fatigue' else 1
        if name == 'fatigue':
            item_name, tags, uses, charges, description = FATIGUE_NAME, [], 0, 0, ''
        else:
            item_name = clean_text(values.get('name'), 100)
            catalog = next((i for i in load_market() if i['name'].casefold() == values['name'].strip().casefold()), {})
            tags = catalog.get('tags', [])
            if 'tags' in values:
                tags = [t.strip() for t in clean_text(values['tags'], 200).split(',') if t.strip()]
            if 'petty' in tags and 'bulky' in tags:
                raise ValueError('An item cannot be both petty and bulky.')
            tags = list(tags)
            uses = number(values.get('uses', catalog.get('uses', 0)))
            charges = number(values.get('charges', catalog.get('charges', 0)))
            for resource in ('uses', 'charges'):
                if resource in values and resource not in tags:
                    tags.append(resource)
            description = clean_text(values['description'], 1000) if 'description' in values else catalog.get('description', '')
        for _ in range(amount):
            item = inventory.create_item(item_name, ','.join(tags), uses, charges, charges,
                                         container['id'], description, commit=False)
            if item is None:
                raise ValueError('Not enough free slots in that container. Nothing was added.')
        return f'{who}: added {amount} × {safe_name(item_name)} to {safe_name(container["name"])}.'
    item = choose_entry(json.loads(character.items or '[]'), values.get('item'))
    if 'carrying' in item:
        raise ValueError('Manage carrying markers through their container in KW.')
    if name == 'use':
        resource = values.get('resource', 'uses')
        if resource not in ('uses', 'charges') or resource not in item or resource not in item.get('tags', []):
            raise ValueError('This item has no such counter. Choose uses or charges for an appropriate item.')
        amount = number(values.get('amount', 1), 1)
        if item[resource] < amount:
            raise ValueError(f'Only {item[resource]} {resource} remain. Nothing was changed.')
        remove_empty = values.get('remove-empty', False)
        if type(remove_empty) is not bool:
            raise ValueError('Set remove-empty to true or false.')
        remaining = item[resource] - amount
        if remaining == 0 and remove_empty:
            inventory.delete_item(item['location'], item['id'], commit=False)
            return f'{who}: used {safe_name(item["name"])} and removed the exhausted item.'
        items = json.loads(character.items)
        for entry in items:
            if str(entry['id']) == str(item['id']):
                if resource == 'uses':
                    entry['max_uses'] = max(entry.get('max_uses', entry['uses']), entry['uses'])
                entry[resource] = remaining
        character.items = json.dumps(items)
        return f'{who}: {safe_name(item["name"])} — {remaining} {resource} remaining.'
    if name == 'remove':
        inventory.delete_item(item['location'], item['id'], commit=False)
        return f'{who}: removed {safe_name(item["name"])}.'
    if item['name'] == FATIGUE_NAME:
        raise ValueError('Fatigue cannot be dropped, moved or transferred. Use /kw remove when it is cleared.')
    if name == 'transfer':
        recipients = [c for c in characters if c.id != character.id]
        choices = [dict(id=c.id, name=c.name) for c in recipients]
        recipient_id = choose_entry(choices, values.get('character'))['id']
        recipient = next(c for c in recipients if c.id == recipient_id)
        try:
            inventory.transfer_item(item['id'], recipient, commit=False)
        except HTTPException as error:
            raise ValueError(error.description) from error
        return f'{who}: gave {safe_name(item["name"])} to **{safe_name(recipient.name)}**.'
    if name == 'drop':
        try:
            drop_item(character.id, character.owner, character.party_id, item['id'], values.get('place'))
        except HTTPException as error:
            raise ValueError(error.description) from error
        return f'{who}: dropped {safe_name(item["name"])} on the ground — {safe_name(values["place"].strip())}.'
    target = choose_entry(inventory.containers, values.get('container'))
    if item['location'] == target['id']:
        raise ValueError('This item is already in that container.')
    if inventory.container_slots(target) + item_size(item) > int(target['slots']):
        raise ValueError('Destination container has insufficient free slots.')
    inventory.pin_slots(item['location'])
    inventory.pin_slots(target['id'])
    items = json.loads(character.items)
    for entry in items:
        if str(entry['id']) == str(item['id']):
            entry['location'] = target['id']
            entry.pop('slot', None)
    character.items = json.dumps(items)
    return f'{who}: moved {safe_name(item["name"])} to {safe_name(target["name"])}.'

"""Shared party ground storage for web and Discord; callers own the transaction."""
import json
import uuid

from flask import abort
from sqlalchemy import update

from app.lib.inventory import FATIGUE_NAME, Inventory
from app.lib.inventory_slots import item_size
from app.models import Character, Party, db

GROUND_NAME = 'on the ground'


def ground_container(party):
    return next((c for c in json.loads(party.containers or '[]') if c.get('on_the_ground')), None)


def ground_items(party):
    container = ground_container(party)
    return [i for i in json.loads(party.items or '[]') if container and i['location'] == container['id']]


def owned_members(party, user_id):
    return Character.query.filter(Character.id.in_(json.loads(party.members or '[]')),
                                  Character.party_id == party.id, Character.owner == user_id).order_by(Character.id).all()


def validate_place(place):
    if not isinstance(place, str) or not 1 <= len(place.strip()) <= 200:
        abort(400, description='Describe where it was dropped (1–200 characters).')
    return place.strip()


def ground_revision(containers):
    return next((c.get('ground_revision', 0) for c in json.loads(containers or '[]') if c['id'] == 0), 0)


def mark_ground_change(character):
    containers = json.loads(character.containers or '[]')
    for container in containers:
        if container['id'] == 0:
            container['ground_revision'] = container.get('ground_revision', 0) + 1
    character.containers = json.dumps(containers)


def preserve_ground(party, items, containers):
    """An old full-party editor must not undo other players' ground actions."""
    current = ground_container(party)
    ground_ids = {c['id'] for c in containers if c.get('on_the_ground')}
    if current:
        ground_ids.add(current['id'])
    return ([i for i in items if i['location'] not in ground_ids] + ground_items(party),
            [c for c in containers if c['id'] not in ground_ids] + ([current] if current else []))


def ensure_ground(party, size):
    containers = json.loads(party.containers or '[]')
    target = next((c for c in containers if c.get('on_the_ground')), None)
    if target is None:
        target = dict(id=max((c['id'] for c in containers), default=0) + 1,
                      name=GROUND_NAME, slots=0, on_the_ground=True)
        containers.append(target)
    target['slots'] = sum(item_size(i) for i in ground_items(party)) + size
    party.containers = json.dumps(containers)
    party.items = party.items or '[]'
    return target['id']


def locked_context(character_id, user_id, party_id):
    # Both entry points lock in party -> character order. A second pickup must
    # reload the party inventory after the first transaction has completed.
    if db.session.get_bind().dialect.name == 'sqlite':
        # SQLite ignores FOR UPDATE. Acquire its write lock before re-reading
        # the source, so simultaneous web pickups cannot both use an old copy.
        db.session.execute(update(Party).where(Party.id == party_id).values(items=Party.items)
                           .execution_options(synchronize_session=False))
    party = Party.query.filter_by(id=party_id).with_for_update().populate_existing().first()
    character = Character.query.filter_by(id=character_id).with_for_update().populate_existing().first()
    if not character or character.owner != user_id:
        abort(403, description='You can only manage your own character.')
    if not party or character.party_id != party.id or character.id not in json.loads(party.members or '[]'):
        abort(400, description='Your character must belong to this party.')
    return character, party


def drop_item(character_id, user_id, party_id, item_id, place):
    place = validate_place(place)
    character, party = locked_context(character_id, user_id, party_id)
    inventory = Inventory(character)
    item = inventory.get_item(item_id)
    if item is None:
        abort(404, description='This item is no longer in your inventory.')
    if 'carrying' in item or item['name'] == FATIGUE_NAME:
        abort(400, description='Fatigue and carrying markers cannot be dropped.')
    target_id = ensure_ground(party, item_size(item))
    inventory.pin_slots(item['location'])
    moved = inventory.transfer_item(item_id, party, target_id, commit=False, ground_action=True)
    entries = json.loads(party.items)
    for entry in entries:
        if str(entry['id']) == str(item_id):
            entry.pop('slot', None)
            entry['ground_place'] = place
            entry['dropped_by'] = character.name
    party.items = json.dumps(entries)
    mark_ground_change(character)
    return moved, party


def drop_container(character_id, user_id, party_id, container_id, place):
    place = validate_place(place)
    character, party = locked_context(character_id, user_id, party_id)
    containers = json.loads(character.containers or '[]')
    root = next((c for c in containers if str(c['id']) == str(container_id)), None)
    if root is None:
        abort(404, description='This container is no longer in your inventory.')
    if root['id'] == 0:
        abort(400, description='The main inventory cannot be dropped.')
    included = {root['id']}
    while True:
        children = {c['id'] for c in containers if str(c.get('carried_by')) in {str(i) for i in included}}
        if children <= included:
            break
        included.update(children)
    if 0 in included:
        abort(400, description='The main inventory cannot be dropped.')
    items = json.loads(character.items or '[]')
    contents = [i for i in items if i['location'] in included]
    if any(i['name'] == FATIGUE_NAME for i in contents):
        abort(400, description='Clear Fatigue before dropping this container.')
    # Carrying markers in containers left on the character are detached with
    # the bundle. Picking it up places those markers in the new owner's main bag.
    markers = [i for i in items if i['location'] not in included and str(i.get('carrying')) in {str(c) for c in included}]
    bundle = dict(containers=[c for c in containers if c['id'] in included], items=contents, markers=markers)
    entry = dict(id=uuid.uuid4().hex, name=root['name'], location=ensure_ground(party, 1), tags=[],
                 ground_place=place, dropped_by=character.name, ground_bundle=bundle)
    removed = {str(i['id']) for i in contents + markers}
    character.items = json.dumps([i for i in items if str(i['id']) not in removed])
    character.containers = json.dumps([c for c in containers if c['id'] not in included])
    party.items = json.dumps(json.loads(party.items) + [entry])
    mark_ground_change(character)
    return entry, party


def pickup_container(character, party, item):
    bundle = item['ground_bundle']
    containers = json.loads(character.containers or '[]')
    items = json.loads(character.items or '[]')
    source_items = bundle['items'] + bundle['markers']
    existing_ids = {str(i['id']) for i in items}
    if any(str(i['id']) in existing_ids for i in source_items):
        abort(409, description='An item from this container already exists in your inventory.')
    inventory = Inventory(character)
    main = inventory.get_container(0)
    load = sum(item_size(i) for i in bundle['markers'])
    if load and (main is None or inventory.container_slots(main) + load > int(main['slots'])):
        abort(400, description='Not enough free slots to carry this container.')
    next_id = max((c['id'] for c in containers), default=0) + 1
    mapping = {c['id']: next_id + offset for offset, c in enumerate(bundle['containers'])}
    for container in bundle['containers']:
        container['id'] = mapping[container['id']]
        container.pop('items', None)
        if 'carried_by' in container:
            container['carried_by'] = mapping.get(int(container['carried_by']), 0)
    for entry in bundle['items']:
        entry['location'] = mapping[entry['location']]
        if 'carrying' in entry:
            entry['carrying'] = mapping[int(entry['carrying'])]
    inventory.pin_slots(0)
    items = json.loads(character.items)
    for entry in bundle['markers']:
        entry['location'] = 0
        entry['carrying'] = mapping[int(entry['carrying'])]
        entry.pop('slot', None)
    character.containers = json.dumps(containers + bundle['containers'])
    character.items = json.dumps(items + source_items)
    party.items = json.dumps([i for i in json.loads(party.items) if str(i['id']) != str(item['id'])])


def pickup_item(character_id, user_id, party_id, item_id):
    character, party = locked_context(character_id, user_id, party_id)
    item = next((i for i in ground_items(party) if str(i['id']) == str(item_id)), None)
    if item is None:
        abort(404, description='This item is no longer on the ground.')
    if item.get('ground_bundle'):
        pickup_container(character, party, item)
        mark_ground_change(character)
        return item, party
    Inventory(character).pin_slots(0)
    moved = Inventory(party).transfer_item(item_id, character, commit=False, ground_action=True)
    entries = json.loads(character.items)
    for entry in entries:
        if str(entry['id']) == str(item_id):
            for key in ('ground_place', 'dropped_by', 'slot'):
                entry.pop(key, None)
    character.items = json.dumps(entries)
    mark_ground_change(character)
    return moved, party

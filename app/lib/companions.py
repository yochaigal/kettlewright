import json
import uuid
from pathlib import Path
from random import randint, choice
from flask_babel import _
from flask_login import current_user
from app.models import db, Character, Companion, Party
from app.lib.character_json import normalize_inventory
from app.lib.data import sanitize_json_content

STATS = ('hp', 'strength', 'dexterity', 'willpower')
DATA = Path(__file__).resolve().parents[1] / 'static' / 'json'


def catalog(kind):
    return json.loads((DATA / ('hirelings.json' if kind == 'hireling' else 'pets.json')).read_text())


def party_member(party):
    if not current_user.is_authenticated:
        return False
    return party.owner == current_user.id or db.session.query(Character.id).filter(
        Character.party_id == party.id, Character.owner == current_user.id,
        Character.id.in_(json.loads(party.members or '[]'))).first() is not None


def can_manage(companion):
    if not current_user.is_authenticated:
        return False
    if companion.kind == 'hireling':
        return companion.party.owner == current_user.id or (companion.shared and party_member(companion.party))
    if companion.character:
        return companion.character.owner == current_user.id
    return can_manage(companion.hireling)


def pet_data(template, parent):
    result = dict(name=template['name'], role=template['name'], notes=_(template.get('notes', '')),
                  armor=template.get('armor', 0), attack=template.get('attack', ''), gold=0,
                  items=[], containers=[dict(id=0, name='Main', slots=template.get('slots', 0))])
    for stat in STATS:
        result[stat] = getattr(parent, stat, None) if template.get('mirror') else template.get(stat)
        result[stat + '_max'] = getattr(parent, stat + '_max', None) if template.get('mirror') else template.get(stat)
    return result


def starting_pets(parent, options):
    """Resolve explicit background rewards before descriptions are translated."""
    templates = catalog('pet')
    keys = dict.fromkeys(key for option in options if option for key in option.get('pets', []))
    return [import_pet(pet_data(templates[key], parent)) for key in keys]


def import_pet(data):
    if not isinstance(data, dict):
        raise ValueError('Invalid pet')
    result = {}
    for field, limit in (('name',100), ('role',100), ('attack',200), ('notes',10000)):
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError('Invalid pet text')
        result[field] = value
    if not result['name'].strip():
        raise ValueError('Missing pet name')
    for field in (*STATS, *(s + '_max' for s in STATS), 'armor', 'gold'):
        value = data.get(field, 0 if field in ('armor','gold') else None)
        if value is not None and (type(value) is not int or not 0 <= value <= (3 if field == 'armor' else 100000)):
            raise ValueError('Invalid pet stat')
        result[field] = value
    for stat in STATS:
        if (result[stat] is None) != (result[stat+'_max'] is None) or (result[stat] is not None and result[stat] > result[stat+'_max']):
            raise ValueError('Invalid pet maximum')
    items, containers = normalize_inventory(json.dumps(data.get('items', [])), json.dumps(data.get('containers', [])))
    result.update(items=sanitize_json_content(json.dumps(items)), containers=sanitize_json_content(json.dumps(containers)))
    return Companion(kind='pet', **result)


def new_hireling(party, role):
    from app.lib.data import load_traits
    from app.lib.char_utils import random_name
    template = next((r for r in catalog('hireling') if r['name'] == role), None)
    if role != 'Custom' and template is None:
        raise ValueError('Unknown hireling role')
    items = []
    for item in template['items'] if template else []:
        items.append(dict(item, id=uuid.uuid4().hex, location=0))
    traits = '\n'.join(_(name) + ': ' + _(choice(values)) for name, values in load_traits().items())
    companion = Companion(kind='hireling', party=party, name=random_name(None), role=role,
                          daily_cost=template['daily_cost'] if template else 0, items=json.dumps(items), notes=traits)
    for stat in STATS:
        value = sum(randint(1,6) for _ in range(1 if stat == 'hp' else 3))
        setattr(companion, stat, value)
        setattr(companion, stat+'_max', value)
    return companion


def source_party(source):
    if isinstance(source, Party):
        return source
    party = db.session.get(Party, source.party_id) if source.party_id else None
    if party and source.id in json.loads(party.members or '[]'):
        return party
    return None


def can_transfer_from(source):
    if not current_user.is_authenticated:
        return False
    if isinstance(source, Party):
        return party_member(source)
    party = source_party(source)
    return source.owner == current_user.id or (party is not None and party.owner == current_user.id)


def companion_destinations(source):
    """Receiving equipment doesn't grant permission to edit a companion's sheet."""
    if not can_transfer_from(source):
        return []
    recipients = list(source.pets) if isinstance(source, Character) else []
    party = source_party(source)
    if party and party_member(party):
        members = Character.query.filter(Character.party_id == party.id,
                                         Character.id.in_(json.loads(party.members or '[]'))).all()
        recipients = [pet for member in members
                      if member.owner == current_user.id or party.owner == current_user.id
                      for pet in member.pets]
        for hireling in party.hirelings:
            recipients.append(hireling)
    destinations = []
    for recipient in recipients:
        for container in json.loads(recipient.containers or '[]'):
            if int(container['slots']) <= 0:
                continue
            destinations.append(dict(value=f'companion:{recipient.id}:{container["id"]}',
                                     companion=recipient, container=container))
    return destinations


def transfer_record_key(source):
    return ('party' if isinstance(source, Party) else 'companion' if isinstance(source, Companion) else 'character') + ':' + str(source.id)


def save_item_to_companion(inventory, item_id, destination):
    """Use the existing item editor; save edits and the move in one transaction."""
    from flask import abort, request
    from flask_wtf import FlaskForm
    if not can_transfer_from(inventory.character):
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    target = next((d for d in companion_destinations(inventory.character) if d['value'] == destination), None)
    if target is None:
        abort(403)
    item = inventory.get_item(item_id)
    if item is None:
        abort(404)
    original_location = item['location']
    data = request.form
    inventory.update_item(item_id, data['edit_item_name'], data['edit_item_tags'],
                          data['edit_item_uses'], data['edit_item_charges'], data['edit_item_max_charges'],
                          original_location, data['edit_item_description'],
                          armor_active=data.get('edit_item_armor_active') == 'on', commit=False)
    inventory.transfer_item(item_id, target['companion'], target['container']['id'])
    record_transfer(inventory.character, target['companion'], item_id)
    inventory.select(original_location)


def record_transfer(source, target, item_id):
    from flask import session
    records = session.get('companion_item_transfers', {})
    records.setdefault(transfer_record_key(source), []).append([transfer_record_key(target), str(item_id)])
    session['companion_item_transfers'] = records



def finish_companion_transfers(source, restored_items=None):
    """Cancel an edit without duplicating items already handed to companions."""
    from flask import session
    records = session.get('companion_item_transfers', {})
    transfers = records.pop(transfer_record_key(source), [])
    session['companion_item_transfers'] = records
    if restored_items is None:
        return
    restored_ids = {str(it['id']) for it in restored_items}
    current_ids = {str(it['id']) for it in json.loads(source.items or '[]')}
    for companion_id, item_id in transfers:
        if item_id not in restored_ids:
            continue
        if isinstance(companion_id, int):  # Earlier sessions recorded only companion IDs.
            companion = db.session.get(Companion, companion_id)
        else:
            kind, target_id = companion_id.split(':', 1)
            companion = db.session.get({'companion':Companion, 'character':Character, 'party':Party}[kind], int(target_id))
        target_items = json.loads(companion.items) if companion else []
        if any(str(it['id']) == item_id for it in target_items):
            companion.items = json.dumps([it for it in target_items if str(it['id']) != item_id])
        elif item_id not in current_ids:
            # It has since moved elsewhere or the companion was deleted.
            # Don't manufacture a second copy from the old edit snapshot.
            restored_items[:] = [it for it in restored_items if str(it['id']) != item_id]

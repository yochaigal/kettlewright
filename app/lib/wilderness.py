"""Cairn 2e Supply and Make Camp inventory changes (no implicit commits)."""
import json
import secrets
import uuid

DICE = (4, 6, 8, 10, 12)


def supply(party, participants, bonus=0):
    if not participants or not 0 <= bonus <= 4:
        raise ValueError('Select at least one participant.')
    sides = DICE[min(len(participants) - 1 + bonus, len(DICE) - 1)]
    amount = secrets.randbelow(sides) + 1
    items = json.loads(party.items or '[]')
    if not any(c['id'] == 0 for c in json.loads(party.containers or '[]')):
        raise ValueError('Party storage needs a Main container.')
    for _ in range(amount):
        items.append(dict(id=uuid.uuid4().hex, name='Rations', tags=['uses'], uses=3, location=0))
    party.items = json.dumps(items)
    return sides, amount


def consume_ration(items):
    for item in items:
        # Names remain canonical in the normal inventory. Accept translated legacy imports too.
        from flask_babel import _
        if item.get('name') not in ('Rations', _('Rations')):
            continue
        uses = item.get('uses', 0)
        try:
            uses = int(uses)
        except (ValueError, TypeError):
            continue
        if uses > 0:
            item['uses'] = uses - 1
            if item['uses'] == 0:
                items.remove(item)
            return True
    return False


def make_camp(party, participants, mounts=(), resolve_deprivation=False):
    if not participants:
        raise ValueError('Select at least one participant.')
    storage = json.loads(party.items or '[]')
    inventories = []
    for member in [*participants, *mounts]:
        items = json.loads(member.items or '[]')
        if not consume_ration(items) and not consume_ration(storage):
            raise ValueError('Not enough Rations. Add provisions before making camp.')
        inventories.append((member, items))
    # Apply only after everyone can eat. Existing deprivation can have other causes.
    for member, items in inventories:
        if resolve_deprivation and hasattr(member, 'deprived'):
            member.deprived = False
        if not getattr(member, 'deprived', False):
            items = [item for item in items if item.get('name') != 'Fatigue']
        member.items = json.dumps(items)
    party.items = json.dumps(storage)

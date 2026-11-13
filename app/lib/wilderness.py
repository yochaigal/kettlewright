"""Cairn 2e Supply and Make Camp inventory changes (no implicit commits)."""
import json
import secrets
import uuid
from app.lib.translations import N_

DICE = (4, 6, 8, 10, 12)


def supply(party, participants, bonus=0):
    if not participants or not 0 <= bonus <= 4:
        raise ValueError(N_('Select at least one participant.'))
    sides = DICE[min(len(participants) - 1 + bonus, len(DICE) - 1)]
    amount = secrets.randbelow(sides) + 1
    items = json.loads(party.items or '[]')
    if not any(c['id'] == 0 for c in json.loads(party.containers or '[]')):
        raise ValueError(N_('Party storage needs a Main container.'))
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
    """Feed everyone, then rest. Returns who ate from where, and who shed or kept Fatigue."""
    if not participants:
        raise ValueError(N_('Select at least one participant.'))
    storage = json.loads(party.items or '[]')
    inventories = []
    report = dict(rested=[c.name for c in participants], mounts=[m.name for m in mounts],
                  from_packs=0, from_storage=0, fatigue_removed=[], still_deprived=[])
    for member in [*participants, *mounts]:
        items = json.loads(member.items or '[]')
        if consume_ration(items):
            report['from_packs'] += 1
        elif consume_ration(storage):
            report['from_storage'] += 1
        else:
            raise ValueError(N_('Not enough Rations. Add provisions before making camp.'))
        inventories.append((member, items))
    # Apply only after everyone can eat. Existing deprivation can have other causes.
    for member, items in inventories:
        if resolve_deprivation and hasattr(member, 'deprived'):
            member.deprived = False
        if getattr(member, 'deprived', False):
            report['still_deprived'].append(member.name)
        else:
            rested = [item for item in items if item.get('name') != 'Fatigue']
            if len(rested) != len(items) and member in participants:
                report['fatigue_removed'].append(member.name)
            items = rested
        member.items = json.dumps(items)
    party.items = json.dumps(storage)
    return report


# Chance in six of getting lost, by path difficulty (Cairn 2e, Travel).
LOST_ON = {'road': 0, 'trail': 2, 'wilderness': 3}


def travel(path):
    """Roll to stay on course. Roads cannot be lost, so nothing is rolled."""
    if path not in LOST_ON:
        raise ValueError(N_('Choose a path.'))
    if not LOST_ON[path]:
        return None, False
    roll = secrets.randbelow(6) + 1
    return roll, roll <= LOST_ON[path]


def wilderness_event():
    """Roll d6 on the Wilderness Events table, in the viewer's language."""
    from pathlib import Path
    from app.main import translate_events_data
    table = json.loads((Path(__file__).resolve().parents[1] / 'static/json/generators/wilderness-events.json').read_text())
    roll = secrets.randbelow(len(table['Wilderness Events']))
    event = translate_events_data({'Wilderness Events': [table['Wilderness Events'][roll]]})['Wilderness Events'][0]
    return roll + 1, event['description']

"""Server-side Warden dice, private unless explicitly shared with a party."""
import secrets

from flask_babel import _

from kettlewright import system

from app.lib.character_rolls import parse_dice
from app.models import PartyRoll, db


def roll_warden(user, party, kind, expression=None, *, public=False):
    if party is not None and party.owner != user.id:
        raise PermissionError('Only the Warden can roll for this party.')
    if public and party is None:
        raise ValueError('Choose a party for a public roll.')
    # Besides dice, the Warden's rolls are the game system's (kettlewright): Reaction Roll and Die of Fate in Cairn.
    rules = party.rules if party is not None else system()
    warden_roll = None if kind == 'dice' else rules.warden_roll(kind)
    if kind == 'dice':
        sides = parse_dice(expression)
        label = _('Roll Dice')
    elif warden_roll is not None:
        sides, label = list(warden_roll.dice), _(warden_roll.label)
    else:
        raise ValueError('Unknown roll type.')
    values = [secrets.randbelow(side) + 1 for side in sides]
    total = sum(values)
    # A system's roll is written the way its rules name it (2d6).
    notation = (warden_roll and warden_roll.notation) or '+'.join(f'd{side}' for side in sides)
    result = f'{label}: {", ".join(map(str, values))} ({notation})'
    outcome = warden_roll.outcome(total) if warden_roll else None
    if outcome:
        result += f' = {total} — {_(outcome)}'
    if party is not None:
        db.session.add(PartyRoll(party_id=party.id, character_name='Warden',
                                 result=result, private_user_id=None if public else user.id))
    return {'result': result, 'values': values, 'sides': sides}

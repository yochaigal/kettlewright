"""Server-side Warden dice, private unless explicitly shared with a party."""
import secrets

from flask_babel import _

from app.lib.character_rolls import parse_dice
from app.models import PartyRoll, db


def roll_warden(user, party, kind, expression=None, *, public=False):
    if party is not None and party.owner != user.id:
        raise PermissionError('Only the Warden can roll for this party.')
    if public and party is None:
        raise ValueError('Choose a party for a public roll.')
    if kind == 'dice':
        sides = parse_dice(expression)
        label = _('Roll Dice')
    elif kind == 'reaction':
        sides, label = [6, 6], _('Reaction Roll')
    elif kind == 'fate':
        sides, label = [6], _('Die of Fate')
    else:
        raise ValueError('Unknown roll type.')
    values = [secrets.randbelow(side) + 1 for side in sides]
    total = sum(values)
    result = f'{label}: {", ".join(map(str, values))} ({"+".join(f"d{side}" for side in sides)})'
    if kind == 'reaction':
        reaction = 'Hostile' if total == 2 else 'Wary' if total <= 5 else 'Curious' if total <= 8 else 'Kind' if total <= 11 else 'Helpful'
        result += f' = {total} — {_(reaction)}'
    if party is not None:
        db.session.add(PartyRoll(party_id=party.id, character_name='Warden',
                                 result=result, private_user_id=None if public else user.id))
    return {'result': result, 'values': values}

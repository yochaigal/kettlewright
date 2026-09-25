"""Server-side dice and ownership rules shared by the sheet and Discord."""
import json
import re
import secrets

from app.models import Party, PartyRoll, db

def parse_dice(expression):
    if not isinstance(expression, str) or len(expression) > 30:
        raise ValueError('Use dice such as d20, 2d6 or d6+d8 (at most two dice).')
    dice = []
    for term in expression.lower().replace(' ', '').split('+'):
        match = re.fullmatch(r'([12]?)d(4|6|8|10|12|20|100)', term)
        if not match:
            raise ValueError('Use dice such as d20, 2d6 or d6+d8 (at most two dice).')
        dice.extend([int(match[2])] * int(match[1] or 1))
    if not 1 <= len(dice) <= 2:
        raise ValueError('Roll at most two dice at a time.')
    return dice


def character_party(character):
    party = db.session.get(Party, character.party_id) if character.party_id else None
    if party and character.id in json.loads(party.members or '[]'):
        return party
    return None


def roll_character(user_id, character, expression, expected_party=None):
    if character is None or character.owner != user_id:
        raise PermissionError('You can only roll for your own characters.')
    party = character_party(character)
    if expected_party is not None and (not party or party.id != expected_party):
        raise PermissionError('This character is no longer in the channel’s party. Use /kw select again.')
    dice = parse_dice(expression)
    values = [secrets.randbelow(sides) + 1 for sides in dice]
    result = f'{", ".join(map(str, values))} ({"+".join(f"d{sides}" for sides in dice)})'
    if party:
        db.session.add(PartyRoll(party_id=party.id, character_name=character.name, result=result))
    return {'result': result, 'values': values}, party


def publish_roll(party, name, result):
    if party is None:
        return
    from flask import current_app
    from app import socketio
    from app.socket_events import party_recipient_ids, notify_roll_history_changed
    try:
        for user_id in party_recipient_ids(party):
            socketio.emit('dice_rolled', f'{name} rolled a {result}', room=f'user_{user_id}')
        notify_roll_history_changed(party)
    except Exception:
        current_app.logger.exception('Unable to publish committed roll')

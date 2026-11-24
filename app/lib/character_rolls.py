"""Server-side dice and ownership rules shared by the sheet and Discord."""
from kettlewright import system
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


# The attributes that can be rolled as a save, and their labels: {'strength': 'STR', ...} (kettlewright).
SAVES = {stat.key: stat.abbr for stat in system().attributes if stat.save}


def save_outcome(roll, score, rules=None):
    """Saves: roll a d20; Cairn's saves fail when the die is higher than the attribute's current value."""
    return (rules or system()).save_succeeds(roll, score)


def describe_save(result, save, score, roll, rules=None):
    """'7 (d20)' becomes '7 (d20) · STR 12 · Success'. rules: the roller's game system (default: the default one)."""
    from flask_babel import gettext
    rules = rules or system()
    outcome = gettext('Success') if save_outcome(roll, score, rules) else gettext('Failure')
    return f'{result} · {rules.abbr(save)} {score} · {outcome}'


def roll_label(value):
    """What was rolled for, e.g. an item's name, kept short and on one line for the roll history."""
    if not isinstance(value, str):
        return None
    return ' '.join(value.split())[:60] or None


def roll_character(user_id, character, expression, expected_party=None, save=None, label=None):
    if character is None or character.owner != user_id:
        raise PermissionError('You can only roll for your own characters.')
    party = character_party(character)
    if expected_party is not None and (not party or party.id != expected_party):
        raise PermissionError('This character is no longer in the channel’s party. Use /kw select again.')
    rules = character.rules
    if save is not None:
        # A save is a single die (a d20 in Cairn) against the attribute's current value (#398).
        if save not in rules.save_keys or character.get_stat(save) is None:
            raise ValueError('Choose STR, DEX or WIL to roll a save.')
        expression = f'd{rules.save_die}'
    return roll_for_party(character.name, expression, party,
                          save=(save, character.get_stat(save)) if save else None, label=label, rules=rules), party


def roll_companion(companion, expression, expected_party=None):
    from app.lib.companions import can_roll, companion_party
    if companion is not None and companion.kind == 'monster':
        raise PermissionError('Use the monster sheet roller to choose roll visibility.')
    if not can_roll(companion):
        raise PermissionError('You cannot roll for this companion.')
    party = companion_party(companion)
    if expected_party is not None and (not party or party.id != expected_party):
        raise PermissionError('This companion is no longer in this party. Reload the sheet.')
    return roll_for_party(companion.name, expression, party), party


def roll_for_party(name, expression, party, save=None, label=None, rules=None):
    dice = parse_dice(expression)
    values = [secrets.randbelow(sides) + 1 for sides in dice]
    result = f'{", ".join(map(str, values))} ({"+".join(f"d{sides}" for sides in dice)})'
    outcome = None
    label = roll_label(label)
    if label and save is None:
        result = f'{result} · {label}'  # e.g. '7 (d8) · Sword': the history says what was rolled for.
    if save is not None:
        rules = rules or system()
        result = describe_save(result, save[0], save[1], values[0], rules)
        # For the sheet's notification: which save, against what, and whether it passed.
        outcome = {'stat': save[0], 'label': rules.abbr(save[0]), 'score': save[1],
                   'success': save_outcome(values[0], save[1], rules)}
    if party:
        db.session.add(PartyRoll(party_id=party.id, character_name=name, result=result))
    rolled = {'result': result, 'values': values, 'sides': dice}
    if outcome:
        rolled['save'] = outcome
    return rolled


def publish_roll(party, name, result, private_user_id=None):
    if party is None:
        return
    from flask import current_app
    from app import socketio
    from app.socket_events import party_recipient_ids, notify_roll_history_changed
    try:
        if private_user_id is not None:
            # A private roll must not even announce a history change to players.
            socketio.emit('roll_history_changed', {'party_id': party.id}, room=f'user_{private_user_id}')
            return
        for user_id in party_recipient_ids(party):
            socketio.emit('dice_rolled', f'{name} rolled a {result}', room=f'user_{user_id}')
        notify_roll_history_changed(party)
    except Exception:
        current_app.logger.exception('Unable to publish committed roll')

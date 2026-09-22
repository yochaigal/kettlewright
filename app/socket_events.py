import json

from flask_login import current_user
from flask_socketio import emit, join_room

from app.models import Character, Party, db


def party_recipient_ids(party):
    """Resolve current membership for every broadcast, including already-open tabs."""
    members = json.loads(party.members or '[]')
    owners = db.session.query(Character.owner).filter(
        Character.id.in_(members), Character.party_id == party.id
    ).all()
    return {party.owner, *(owner for (owner,) in owners)}


def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        if not current_user.is_authenticated:
            return False
        join_room(f'user_{current_user.id}')

    @socketio.on('register')
    def handle_register():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')

    @socketio.on('roll_dice')
    def handle_roll_dice(data):
        if not current_user.is_authenticated or not isinstance(data, dict):
            return
        try:
            character_id = int(data.get('character_id'))
            party_id = int(data.get('party_id'))
        except (TypeError, ValueError):
            return
        roll_result = data.get('roll')
        if not isinstance(roll_result, (str, int, float)) or isinstance(roll_result, bool):
            return
        if not str(roll_result) or len(str(roll_result)) > 500:
            return

        character = db.session.get(Character, character_id)
        party = db.session.get(Party, party_id)
        if not character or not party or character.owner != current_user.id:
            return
        if character.party_id != party.id or character.id not in json.loads(party.members or '[]'):
            return

        message = f'{character.name} rolled a {roll_result}'
        # User rooms work across Redis workers, but party membership is never cached
        # in a socket room: leaving a party takes effect on the next roll.
        for user_id in party_recipient_ids(party):
            emit('dice_rolled', message, room=f'user_{user_id}')

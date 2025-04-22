from flask import request
import sys
import json
from app.models import Party, User, Character
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room


def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected', file=sys.stderr)
        print(current_user.id, file=sys.stderr)
        join_user_parties()

    @socketio.on('disconnect')
    def handle_disconnect(reason=""): # according logs, it should have at least one parameter
        if current_user and current_user.id:
            print(f' User {current_user.id} disconnected. Reason: {reason}')
        else:
            print(f' User disconnected but probably was not logged. Reason: {reason}')

    @socketio.on('register')
    def handle_register():
        join_user_parties()
        print(f'User {current_user.id} registered and joined their party rooms')

    def join_user_parties():
        # Find all parties the user is a member of
        user_parties = Party.query.filter(
            (Party.owner == current_user.id) |
            (Party.subowners.contains(str(current_user.id)))
        ).all()

        for party in user_parties:
            party_room = f'party_{party.id}'
            join_room(party_room)
            print(f'User {current_user.id} joined party room {party_room}')

    @socketio.on('roll_dice')
    def handle_roll_dice(data):
        try:
            print('Rolling dice', data)
            print(current_user.id, file=sys.stderr)
            character_id = data.get('character_id')
            roll_result = data.get('roll')
            party_id = data.get('party_id')

            if not all([character_id, roll_result, party_id]):
                print("Missing required data")
                return

            character = Character.query.get(int(character_id))
            if not character:
                print(f"Character {character_id} not found")
                return

            if str(character.owner) != str(current_user.id):
                print(
                    f"User {current_user.id} is not the owner of character {character_id}")
                return

            party = Party.query.get(int(party_id))
            if not party:
                print(f"Party {party_id} not found")
                return

            try:
                party_members = json.loads(
                    party.members) if party.members else []
            except json.JSONDecodeError:
                print(f"Invalid JSON in party {party_id} members list")
                return

            if int(character_id) not in party_members:
                print(
                    f"Character {character_id} not in party {party_id} members list. Members: {party_members}")
                return

            message = f'{character.name} rolled a {roll_result}'

            party_room = f'party_{party_id}'
            emit('dice_rolled', message, room=party_room)
            print(f"Emitted dice roll to party room {party_room}")

        except Exception as e:
            print(f"Error in handle_roll_dice: {str(e)}", file=sys.stderr)

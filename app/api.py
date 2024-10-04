from flask import Blueprint, jsonify
from flask_login import current_user
from app.models import User, Character, Party
import os
import sys

api = Blueprint('api', __name__)

base_url = os.environ.get('BASE_URL')
print('base_url:', base_url, file=sys.stderr)


def character_to_dict(character):
    return {
        'name': character.name,
        'url_name': character.url_name,
        'background': character.background,
        'description': character.description,
        'traits': character.traits,
        'bonds': character.bonds,
        'scars': character.scars,
        'omens': character.omens,
        'portrait': character.image_url if character.custom_image else f'{base_url}/static/images/portraits/{character.image_url}',
        'strength': character.strength,
        'strength_max': character.strength_max,
        'dexterity': character.dexterity,
        'dexterity_max': character.dexterity_max,
        'willpower': character.willpower,
        'willpower_max': character.willpower_max,
        'hp': character.hp,
        'hp_max': character.hp_max,
        'deprived': character.deprived,
        'gold': character.gold,
        'notes': character.notes,
        'items': character.items,
        'containers': character.containers,
    }


@api.route('/api/users/<username>/characters/<url_name>/')
def get_character(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()

    party = Party.query.filter_by(id=character.party_id).first()

    character_data = character_to_dict(character)

    if party:
        owner = User.query.filter_by(id=party.owner).first()
        character_data['party'] = {
            'name': party.name,
            'url': f'users/{owner.username}/parties/{party.party_url}/',
            'description': party.description
        }

    return jsonify(character_data)

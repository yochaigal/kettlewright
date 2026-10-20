"""Character sheet edits belong to its owner and its current party's Warden."""
from flask_login import current_user

from app.lib.character_rolls import character_party


def can_edit_character(character):
    if not current_user.is_authenticated:
        return False
    if character.owner == current_user.id:
        return True
    party = character_party(character)
    return party is not None and party.owner == current_user.id

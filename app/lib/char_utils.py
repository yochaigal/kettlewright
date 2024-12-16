from app.models import db, User, Character, Party

# Retrieve character data
def get_character(character_id):
    character = Character.query.filter_by(id=character_id).first()
    return character

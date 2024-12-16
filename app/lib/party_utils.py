from app.models import db, User, Character, Party
import json

# Party utils
def load_party_members(party):
    return json.loads(party.members) if party.members else []
def save_party_members(party, party_members):
    party.members = json.dumps(party_members)
def load_party_subowners(party):
    return json.loads(party.subowners) if party.subowners else []
def save_party_subowners(party, party_subowners):
    party.subowners = json.dumps(party_subowners)
def get_user_characters_in_party(party_members, user_id):
    return [member for member in party_members if Character.query.get(member).owner == user_id]

# Add character to party (assuming party_id in charater is already set)
def add_character_to_party(character):
    if character == None or character.party_id == None:
        return
    party = Party.query.filter_by(id=character.party_id).first()
    if party == None:
        print("party with the id ", character.party_id, "not found")
        return 
    party_members = load_party_members(party)
    if character.id not in party_members:
        party_members.append(character.id)
        save_party_members(party, party_members)
    # Add user to subowners
    party_subowners = load_party_subowners(party)
    if character.owner not in party_subowners:
        party_subowners.append(character.owner)
        save_party_subowners(party, party_subowners)
    
# Remove character from current party        
def remove_character_from_party(character):
    if character.party_id == None:
        return
    party = Party.query.filter_by(id=character.party_id).first()
    if party == None:
        print("party with the id ", character.party_id, "not found")
        return
    party_members = load_party_members(party)
    party_subowners = load_party_subowners(party)
    if character.id in party_members:
        party_members.remove(character.id)
        save_party_members(party, party_members)
    # Check if the user has other characters in the party before removing from subowners
    user_characters = get_user_characters_in_party(party_members, character.owner)
    if not user_characters and character.owner in party_subowners:
        party_subowners.remove(character.owner)
        save_party_subowners(party, party_subowners)
    character.party_id = None
    character.party_code = ""

def get_party_by_owner(ownername, party_url):
    owner = User.query.filter_by(username=ownername).first()
    party = Party.query.filter_by(
        owner=owner.id, party_url=party_url).first()
    return party

def get_party_by_id(party_id):
    party = Party.query.filter_by(id=party_id).first()
    return party
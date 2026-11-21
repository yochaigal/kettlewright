"""Parties live in campaigns: one, or several at once for a West Marches game.

Parties are only ever created inside a campaign: its first one with the campaign, more
with New party. The Warden can delete a party or move it to another of their campaigns
(it keeps what it was shown). These helpers create campaigns and parties, list parties,
and find the parties a player's characters are in (those are someone else's campaigns).
"""
import json
import os

from flask import url_for
from slugify import slugify

from app.models import db, Character, Party, PartyRoll, PartyMap

DEFAULT_CONTAINERS = '[{"name":"Main","slots":10,"id":0}]'


def generate_unique_join_code():
    while True:
        join_code = os.urandom(8).hex()
        if Party.query.filter_by(join_code=join_code).first() is None:
            return join_code


def generate_unique_party_url(name, owner_id):
    """A slug of the name, unique among the owner's parties."""
    base = slugify(name) or 'party'
    party_url, counter = base, 1
    while Party.query.filter_by(party_url=party_url, owner=owner_id).first() is not None:
        party_url = f'{base}{counter}'
        counter += 1
    return party_url


def create_campaign(owner_id, name):
    """A new campaign with its (empty) party, named after it. The caller commits."""
    from app.models import Campaign
    campaign = Campaign(owner_id=owner_id, name=name)
    db.session.add(campaign)
    create_party(campaign, name[:64])
    return campaign


def create_party(campaign, name, description=''):
    """A party of the campaign, run by the campaign's owner. The caller commits."""
    from app.models import User
    db.session.flush()  # A campaign created in this request needs its id.
    owner = db.session.get(User, campaign.owner_id)
    party = Party(name=name, description=description, owner=owner.id, owner_username=owner.username,
                  campaign=campaign, join_code=generate_unique_join_code(),
                  party_url=generate_unique_party_url(name, owner.id), items='[]', containers=DEFAULT_CONTAINERS)
    db.session.add(party)
    return party


def delete_party(party):
    """Delete a party: its characters are kept and leave it. The caller commits."""
    from app.lib.campaigns import delete_party_notes
    for character in Character.query.filter_by(party_id=party.id).all():
        character.party_id = None
        character.party_code = None
    PartyRoll.query.filter_by(party_id=party.id).delete(synchronize_session=False)
    PartyMap.query.filter_by(party_id=party.id).delete(synchronize_session=False)
    delete_party_notes(party.id)
    db.session.delete(party)


def party_page(party):
    return url_for('party.party_view', ownername=party.owner_username, party_url=party.party_url)


def member_portraits(party):
    """Portrait URLs of the party's members, in member order."""
    try:
        member_ids = json.loads(party.members) if party.members and party.members.strip() else []
    except ValueError:
        member_ids = []
    characters = {c.id: c for c in Character.query.filter(Character.id.in_(member_ids)).all()} if member_ids else {}
    portraits = []
    for member_id in member_ids:
        character = characters.get(member_id)
        if character is None:
            continue
        portraits.append({'name': character.name, 'src': character.image_url if character.custom_image else
                          url_for('static', filename='images/portraits/' + (character.image_url or 'default-portrait.webp'))})
    return portraits


def party_cards(parties):
    """What a party card shows: name, link, members' portraits."""
    return [{'party': party, 'url': party_page(party), 'members': member_portraits(party)} for party in parties]


def played_parties(user_id):
    """Parties of other Wardens that one of the user's characters is in, newest first."""
    party_ids = {party_id for (party_id,) in db.session.query(Character.party_id).filter(
        Character.owner == user_id, Character.party_id.isnot(None))}
    if not party_ids:
        return []
    parties = Party.query.filter(Party.id.in_(party_ids), Party.owner != user_id).all()
    return sorted(parties, key=lambda party: party.id, reverse=True)


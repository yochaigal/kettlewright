"""Parties live in campaigns: one, or several at once for a West Marches game.

Parties are only ever created inside a campaign: its first one with the campaign, more
with New party. The Warden can delete a party or move it to another of their campaigns
(it keeps what it was shown). These helpers create campaigns and parties, list parties,
and find the parties a player's characters are in (those are someone else's campaigns).
"""
from kettlewright import system
import json
import os

from flask import url_for
from slugify import slugify

from app.models import db, Character, Party, PartyRoll, PartyMap

DEFAULT_CONTAINERS = json.dumps(system().inventory.default_containers(), separators=(',', ':'))


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


def create_campaign(owner_id, name, with_party=True, game_system=None):
    """A new campaign, with an (empty) party named after it unless with_party is False (#501). The caller commits.

    game_system (#487) is the system it plays, fixed from now on; the default one unless given. Not offered in
    the app: every campaign plays the default system today."""
    from app.models import Campaign
    campaign = Campaign(owner_id=owner_id, name=name, game_system=game_system or system().key)
    db.session.add(campaign)
    if with_party:
        create_party(campaign, name[:64])
    return campaign


def create_party(campaign, name, description='', owner_id=None):
    """A party of the campaign, run by the campaign's owner; with no campaign, one of owner_id's own (Parties view).
    The caller commits."""
    from app.models import User
    db.session.flush()  # A campaign created in this request needs its id.
    owner = db.session.get(User, campaign.owner_id if campaign is not None else owner_id)
    # It plays its campaign's game system (#487), or the default one; fixed from now on.
    party = Party(name=name, description=description, owner=owner.id, owner_username=owner.username,
                  campaign=campaign, game_system=campaign.game_system if campaign is not None else system().key,
                  join_code=generate_unique_join_code(),
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


def party_roster(party):
    """The Parties view (Discord feedback): each character at a glance, in member order."""
    try:
        member_ids = json.loads(party.members) if party.members and party.members.strip() else []
    except ValueError:
        member_ids = []
    characters = {c.id: c for c in Character.query.filter(Character.id.in_(member_ids), Character.party_id == party.id)} \
        if member_ids else {}
    roster = []
    for member_id in member_ids:
        character = characters.get(member_id)
        if character is None:
            continue
        hp, hp_max = character.hpValue()
        roster.append({
            'name': character.name, 'url': url_for('main.character', username=character.owner_username, url_name=character.url_name)
                   if character.owner_username and character.url_name else None,
            'src': character.image_url if character.custom_image else
                   url_for('static', filename='images/portraits/' + (character.image_url or 'default-portrait.webp')),
            'hp': hp, 'hp_max': hp_max,
            'stats': [(stat, character.get_stat(stat), character.get_stat(stat + '_max')) for stat in character.rules.attribute_keys],
            'rules': character.rules, 'armor': character.armorValue(), 'free': character.freeMainSlots(),
            'deprived': bool(character.deprived), 'panicked': bool(character.panicked), 'dead': bool(character.dead)})
    return roster


def parties_view(user_id):
    """Every party at once (Discord feedback): the ones you run, in any campaign or none, then the ones you play in."""
    from app.models import Campaign
    running = Party.query.filter_by(owner=user_id).order_by(Party.name).all()
    campaigns = {campaign.id: campaign for campaign in Campaign.query.filter(
        Campaign.id.in_({party.campaign_id for party in running if party.campaign_id}))}
    card = lambda party: {'party': party, 'url': party_page(party), 'roster': party_roster(party),
                          'campaign': campaigns.get(party.campaign_id)}
    return {'running': [card(party) for party in running], 'playing': [card(party) for party in played_parties(user_id)]}


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


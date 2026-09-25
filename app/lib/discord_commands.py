"""Small guild-only command surface. Mutations commit with the interaction receipt."""
import math
import re

from flask import current_app, url_for

from app.lib.character_rolls import roll_character
from app.models import Character, DiscordAccount, DiscordChannel, DiscordSelection, Party, User, db
from app.blueprints.party import party_characters


def option(name, description, **kwargs):
    return dict(type=3, name=name, description=description, **kwargs)


def command_definition():
    commands = [
        ('login', 'Connect your Kettlewright account', []),
        ('bind', 'Bind this channel to a party you own; shares cards here', [
            option('party', 'Your party', required=True, autocomplete=True)]),
        ('unbind', 'Remove this channel’s party binding', []),
        ('select', 'Choose your active character in this channel', [
            option('character', 'Your character in this party', required=True, autocomplete=True)]),
        ('character', 'Show your selected character', []),
        ('party', 'Show this channel’s party', [
            dict(type=4, name='page', description='Roster page', min_value=1)]),
        ('roll', 'Roll dice for your selected character', [
            option('dice', 'For example d20, 2d6 or d6+d8; at most two dice', required=True, max_length=30)]),
    ]
    return dict(name='kw', description='Kettlewright characters, parties and dice', type=1,
                contexts=[0], integration_types=[0], options=[
                    dict(type=1, name=name, description=description, options=options)
                    for name, description, options in commands])


def reply(content, private=True):
    return {'type': 4, 'data': {'content': content[:2000], 'allowed_mentions': {'parse': []},
                              **({'flags': 64} if private else {})}}


def safe_name(text):
    return re.sub(r'([\\`*_{}\[\]()<>~|])', r'\\\1', str(text or '').replace('\n', ' '))


def site_url(path):
    return current_app.config['DISCORD_BASE_URL'].rstrip('/') + path


def linked_party(guild_id, channel_id):
    binding = db.session.get(DiscordChannel, (guild_id, channel_id))
    party = db.session.get(Party, binding.party_id) if binding else None
    # A transferred party or disconnected Warden must be explicitly bound again.
    if (not party or party.owner != binding.linked_by
            or not db.session.get(DiscordAccount, binding.linked_by)
            or not db.session.get(User, binding.linked_by)):
        raise ValueError('This channel needs a party binding. Its Warden can use /kw bind.')
    return binding, party


def resolve_choice(objects, value):
    matches = [obj for obj in objects if str(obj.id) == str(value)]
    if not matches:
        matches = [obj for obj in objects if obj.name.casefold() == str(value).casefold()]
    if len(matches) != 1:
        raise ValueError('Choose a matching entry from autocomplete (names may not be unique).')
    return matches[0]


def command_parts(payload):
    data = payload.get('data', {})
    if data.get('name') != 'kw' or len(data.get('options', [])) != 1:
        raise ValueError('Unknown command.')
    subcommand = data['options'][0]
    return subcommand['name'], {o['name']: o.get('value') for o in subcommand.get('options', [])}


def autocomplete(payload, account):
    choices = []
    try:
        name, values = command_parts(payload)
        if not account or not db.session.get(User, account.user_id):
            return {'type': 8, 'data': {'choices': []}}
        if name == 'bind':
            candidates = Party.query.filter_by(owner=account.user_id).all()
            query = str(values.get('party', '')).casefold()
        elif name == 'select':
            _, party = linked_party(payload['guild_id'], payload['channel_id'])
            candidates = [c for c in party_characters(party) if c.owner == account.user_id]
            query = str(values.get('character', '')).casefold()
        else:
            candidates, query = [], ''
        choices = [dict(name=f'{c.name} (#{c.id})'[:100], value=str(c.id))
                   for c in candidates if query in c.name.casefold() or query == str(c.id)][:25]
    except (ValueError, KeyError):
        pass
    return {'type': 8, 'data': {'choices': choices}}


def execute(payload, account):
    """Return (Discord response, optional post-commit roll notification)."""
    name, values = command_parts(payload)
    if name == 'login':
        return reply('Connect your Discord account in Kettlewright: ' + site_url(url_for('discord.settings'))), None
    if not account or not db.session.get(User, account.user_id):
        raise ValueError('Connect your Kettlewright account first with /kw login.')
    user_id = account.user_id
    guild_id, channel_id = payload['guild_id'], payload['channel_id']
    scope = dict(guild_id=guild_id, channel_id=channel_id)
    if name in ('bind', 'unbind'):
        permissions = int(payload.get('member', {}).get('permissions', 0))
        if not permissions & (8 | 16):  # ADMINISTRATOR or MANAGE_CHANNELS
            raise PermissionError('You need Manage Channels permission to change the binding.')
        binding = db.session.get(DiscordChannel, (guild_id, channel_id))
        old_party = db.session.get(Party, binding.party_id) if binding else None
        if old_party and old_party.owner != user_id:
            raise PermissionError('Only the current party’s Warden can change this binding.')
        if name == 'unbind':
            if binding:
                db.session.delete(binding)
            DiscordSelection.query.filter_by(**scope).delete()
            return reply('Party unbound. Character selections in this channel were cleared.'), None
        party = resolve_choice(Party.query.filter_by(owner=user_id).all(), values.get('party'))
        if not binding:
            binding = DiscordChannel(**scope)
            db.session.add(binding)
        binding.party_id, binding.linked_by = party.id, user_id
        DiscordSelection.query.filter_by(**scope).delete()
        return reply(f'Bound to **{safe_name(party.name)}**. Party cards and rolls requested here will be visible '
                     'to everyone who can read this channel. Each player should use /kw select.'), None
    _, party = linked_party(guild_id, channel_id)
    characters = party_characters(party)
    if user_id != party.owner and not any(c.owner == user_id for c in characters):
        raise PermissionError('You are not a member of this party.')
    if name == 'party':
        page = values.get('page', 1)
        pages = max(1, math.ceil(len(characters) / 10))
        if type(page) is not int or not 1 <= page <= pages:
            raise ValueError(f'Choose a page between 1 and {pages}.')
        roster = '\n'.join(f'{safe_name(c.name)} — STR {c.strength or 0}, DEX {c.dexterity or 0}, '
                           f'WIL {c.willpower or 0}, HP {c.hpValue()[0]}/{c.hp_max or 0}'
                           for c in characters[(page - 1) * 10:page * 10]) or 'No characters yet.'
        owner = db.session.get(User, party.owner)
        link = site_url(url_for('party.party_view', ownername=owner.username, party_url=party.party_url or ''))
        return reply(f'**{safe_name(party.name)}** ({page}/{pages})\n{roster}\n<{link}>', private=False), None
    key = (user_id, guild_id, channel_id)
    selection = db.session.get(DiscordSelection, key)
    if name == 'select':
        character = resolve_choice([c for c in characters if c.owner == user_id], values.get('character'))
        if not selection:
            selection = DiscordSelection(user_id=user_id, **scope)
            db.session.add(selection)
        selection.character_id = character.id
        return reply(f'Selected **{safe_name(character.name)}** in this channel. '
                     'Use /kw character or /kw roll dice:d20.'), None
    character = next((c for c in characters if selection and c.id == selection.character_id
                      and c.owner == user_id), None)
    if character is None:
        raise ValueError('Select one of your characters in this party first: /kw select.')
    if name == 'character':
        owner = db.session.get(User, user_id)
        link = site_url(url_for('main.character', username=owner.username, url_name=character.url_name or ''))
        conditions = ', '.join(label for field, label in [('deprived', 'Deprived'), ('panicked', 'Panicked'),
                              ('dead', 'Dead')] if getattr(character, field)) or 'None'
        text = (f'**{safe_name(character.name)}**\n'
                f'STR {character.strength or 0}/{character.strength_max or 0} · '
                f'DEX {character.dexterity or 0}/{character.dexterity_max or 0} · '
                f'WIL {character.willpower or 0}/{character.willpower_max or 0}\n'
                f'HP {character.hpValue()[0]}/{character.hp_max or 0} · Armor {character.armorValue()}\n'
                f'Conditions: {conditions}\n<{link}>')
        return reply(text, private=False), None
    if name == 'roll':
        result, party = roll_character(user_id, character, values.get('dice'), expected_party=party.id)
        return reply(f'**{safe_name(character.name)}** rolled **{result["result"]}**', private=False), (
            party, character.name, result['result'])
    raise ValueError('Unknown command.')

"""Discord identities and per-channel game context; no OAuth tokens are stored."""
from .globals import db


class DiscordAccount(db.Model):
    __tablename__ = 'discord_accounts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    discord_id = db.Column(db.String(20), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)


class DiscordChannel(db.Model):
    __tablename__ = 'discord_channels'
    guild_id = db.Column(db.String(20), primary_key=True)
    channel_id = db.Column(db.String(20), primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    linked_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)


class DiscordSelection(db.Model):
    __tablename__ = 'discord_selections'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    guild_id = db.Column(db.String(20), primary_key=True)
    channel_id = db.Column(db.String(20), primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False)


class DiscordInteraction(db.Model):
    __tablename__ = 'discord_interactions'
    id = db.Column(db.String(20), primary_key=True)
    discord_id = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.Integer, nullable=False, index=True)
    response = db.Column(db.Text, nullable=False)

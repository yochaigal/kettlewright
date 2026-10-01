"""Warden originals and independently published party knowledge.

Map roots, locations and paths share the same publication boundary. Geometry
contains no player-facing prose.
"""
from sqlalchemy.orm import declared_attr
from datetime import datetime, timezone
from .globals import db


class Versioned:
    version = db.Column(db.Integer, nullable=False, default=1)

    @declared_attr
    def __mapper_args__(cls):
        return {'version_id_col': cls.version}


class Campaign(Versioned, db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    owner = db.relationship('User', backref=db.backref('campaigns', cascade='all, delete-orphan'))
    parties = db.relationship('CampaignParty', cascade='all, delete-orphan', backref='campaign')
    entries = db.relationship('ContentEntry', backref='campaign')


class CampaignParty(db.Model):
    __tablename__ = 'campaign_parties'
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='CASCADE'), primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True)
    party = db.relationship('Party', backref=db.backref('campaign_links', cascade='all, delete-orphan'))


class ContentEntry(Versioned, db.Model):
    __tablename__ = 'content_entries'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='SET NULL'), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='SET NULL'), index=True)
    parent = db.relationship('ContentEntry', remote_side='ContentEntry.id', backref='children')
    category = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='')
    body = db.Column(db.Text, nullable=False, default='')
    path_type = db.Column(db.String(20), nullable=False, default='standard')
    owner = db.relationship('User', backref=db.backref('content_entries', cascade='all, delete-orphan'))
    presentations = db.relationship('PartyPresentation', cascade='all, delete-orphan', backref='entry')
    links = db.relationship('ContentLink', foreign_keys='ContentLink.source_id', cascade='all, delete-orphan')
    incoming_links = db.relationship('ContentLink', foreign_keys='ContentLink.target_id', cascade='all, delete-orphan')


class ContentLink(db.Model):
    __tablename__ = 'content_links'
    source_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), primary_key=True)


class CampaignImport(db.Model):
    __tablename__ = 'campaign_imports'
    id = db.Column(db.String(32), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    consumed = db.Column(db.Boolean, nullable=False, default=False)
    payload = db.Column(db.JSON, nullable=False)


class PartyPresentation(Versioned, db.Model):
    __tablename__ = 'party_presentations'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False, default='')
    path_type = db.Column(db.String(20), nullable=False, default='standard')
    published = db.Column(db.Boolean, nullable=False, default=True)
    drawing = db.Column(db.JSON, nullable=True)
    party = db.relationship('Party', backref=db.backref('content_presentations', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('entry_id', 'party_id', name='uq_presentation_entry_party'),)


class PointcrawlMap(Versioned, db.Model):
    __tablename__ = 'pointcrawl_maps'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False, unique=True)
    kind = db.Column(db.String(20), nullable=False, default='dungeon')
    drawing = db.Column(db.JSON, nullable=True)
    entry = db.relationship('ContentEntry', backref=db.backref('pointcrawl', uselist=False, cascade='all, delete-orphan'))
    nodes = db.relationship('MapNode', foreign_keys='MapNode.map_id', cascade='all, delete-orphan', backref='map')
    edges = db.relationship('MapEdge', cascade='all, delete-orphan', backref='map')
    entrances = db.relationship('MapNode', foreign_keys='MapNode.nested_map_id', backref='nested_map')


class MapNode(db.Model):
    __tablename__ = 'map_nodes'
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    nested_map_id = db.Column(db.Integer, db.ForeignKey('pointcrawl_maps.id', ondelete='SET NULL'))
    entry = db.relationship('ContentEntry', backref=db.backref('map_nodes', cascade='all, delete-orphan'))
    outgoing = db.relationship('MapEdge', foreign_keys='MapEdge.source_id', cascade='all, delete-orphan')
    incoming = db.relationship('MapEdge', foreign_keys='MapEdge.target_id', cascade='all, delete-orphan')
    __table_args__ = (db.UniqueConstraint('map_id', 'entry_id', name='uq_map_location'),)


class MapEdge(db.Model):
    __tablename__ = 'map_edges'
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False, unique=True)
    source_id = db.Column(db.Integer, db.ForeignKey('map_nodes.id', ondelete='CASCADE'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('map_nodes.id', ondelete='CASCADE'), nullable=False)
    entry = db.relationship('ContentEntry', backref=db.backref('map_edges', cascade='all, delete-orphan'))

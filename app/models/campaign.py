"""Warden originals and independently published party knowledge.

Map roots, locations and paths share the same publication boundary. Geometry
contains no player-facing prose.
"""
from sqlalchemy import event
from sqlalchemy.orm import declared_attr, Session
from datetime import datetime, timezone
from uuid import uuid4
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
    # Its picture (#476): the campaign's cover. Empty: the first picture in its articles.
    image = db.Column(db.String(2000), nullable=False, default='', server_default='')
    owner = db.relationship('User', backref=db.backref('campaigns', cascade='all, delete-orphan'))
    # Its parties (several at once for a West Marches game), created in it; the first comes with the
    # campaign. A party can be deleted, or moved to another of the Warden's campaigns.
    parties = db.relationship('Party', backref='campaign', order_by='Party.id')
    entries = db.relationship('ContentEntry', backref='campaign')
    modules = db.relationship('Module', backref='campaign', cascade='all, delete-orphan', order_by='Module.id')


class Module(Versioned, db.Model):
    """Content a campaign is built from: articles, notes, maps and backgrounds.

    Created in the campaign (blank or randomly generated), added from the Modules
    Marketplace (slug names the bundled module) or uploaded; exported as an archive."""
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(64), nullable=False, default='', server_default='')
    # Custom backgrounds, in the format of background_data.json (name -> background); NULL means none.
    backgrounds = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    entries = db.relationship('ContentEntry', backref='module')


class ContentEntry(Versioned, db.Model):
    __tablename__ = 'content_entries'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='SET NULL'), index=True)
    # The module it belongs to, in its campaign. Only party notes have none.
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id', ondelete='SET NULL'), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='SET NULL'), index=True)
    parent = db.relationship('ContentEntry', remote_side='ContentEntry.id', backref='children')
    category = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='')
    body = db.Column(db.Text, nullable=False, default='')
    # Its own picture (#476), apart from the text: a stored upload (/material-images/…) or an image URL.
    # Shown above the text and on its card; parties it was revealed to see it too.
    image = db.Column(db.String(2000), nullable=False, default='', server_default='')
    # A party note's sketch (Excalidraw, like a map's drawing), below its text.
    drawing = db.Column(db.JSON, nullable=True)
    source_path = db.Column(db.String(500), nullable=False, default='', server_default='')
    reference_key = db.Column(db.String(32), nullable=False, unique=True, default=lambda: uuid4().hex)
    references = db.Column(db.JSON, nullable=False, default=dict, server_default='{}')
    is_heart = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
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
    references = db.Column(db.JSON, nullable=False, default=dict, server_default='{}')
    path_type = db.Column(db.String(20), nullable=False, default='standard')
    published = db.Column(db.Boolean, nullable=False, default=True)
    # For a map: this party's fog over the drawing (whiteboard format), uncovered by the Warden.
    fog = db.Column(db.JSON, nullable=True)
    fog_version = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    party = db.relationship('Party', backref=db.backref('content_presentations', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('entry_id', 'party_id', name='uq_presentation_entry_party'),)


class MapPin(db.Model):
    """A pin a party placed on a revealed map: a party note (title and text) with a position."""
    __tablename__ = 'map_pins'
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False, unique=True)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    entry = db.relationship('ContentEntry', backref=db.backref('pin', uselist=False, cascade='all, delete-orphan'))
    party = db.relationship('Party', backref=db.backref('map_pins', cascade='all, delete-orphan'))
    __table_args__ = (db.Index('ix_map_pins_map_party', 'map_id', 'party_id'),)


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
    pins = db.relationship('MapPin', cascade='all, delete-orphan', backref='map')


class MapNode(db.Model):
    __tablename__ = 'map_nodes'
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False, index=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    geometry = db.Column(db.JSON, nullable=True)
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


@event.listens_for(Session, 'before_flush')
def file_new_articles(session, context, instances):
    """Every article belongs to a module of its campaign (party notes excepted).

    Code that creates articles names their module; anything else lands in its parent's
    module, else the campaign's first module (created when the campaign has none)."""
    pending = [obj for obj in session.new if isinstance(obj, ContentEntry)
               and obj.module is None and obj.module_id is None and obj.category != 'party_note']
    while pending:
        waiting = []
        for entry in pending:
            parent = entry.parent
            if parent is not None and parent.module is None and parent.module_id is None and parent in pending:
                waiting.append(entry)  # File its parent first.
                continue
            module = parent.module if parent is not None else None
            campaign = entry.campaign or (session.get(Campaign, entry.campaign_id) if entry.campaign_id else None)
            if module is None and campaign is not None:
                module = campaign.modules[0] if campaign.modules else Module(campaign=campaign, title=campaign.name)
                session.add(module)
            entry.module = module
        if len(waiting) == len(pending):
            break
        pending = waiting


MIRRORED = ('title', 'body', 'path_type', 'references')


@event.listens_for(Session, 'before_flush')
def mirror_revealed_articles(session, context, instances):
    """A party sees the original: changing an article changes what every party it was revealed to reads.

    There are no party versions; a party's copy (PartyPresentation) always mirrors the original."""
    from sqlalchemy import inspect as inspect_state
    for entry in [obj for obj in session.dirty if isinstance(obj, ContentEntry)]:
        state = inspect_state(entry)
        if not any(state.attrs[name].history.has_changes() for name in MIRRORED):
            continue
        for row in entry.presentations:
            row.title, row.body, row.path_type = entry.title, entry.body, entry.path_type
            row.references = dict(entry.references or {})

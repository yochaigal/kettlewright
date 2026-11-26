from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import sys
import json
from .globals import db


class Party(db.Model):
    __tablename__ = 'parties'

    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    # The Warden's campaign this party plays in (several parties can share one, as in West Marches).
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id', ondelete='SET NULL'), index=True)
    # Character creation: the official Cairn backgrounds besides the campaign modules' ones.
    official_backgrounds = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    # Cairn Barebones creation: the official d100 background table besides the campaign modules' backgrounds.
    official_barebones = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    # The art of new bestiary monsters: 'kettlewright' or 'oozejar' (app/lib/monsters.py MONSTER_ARTS).
    monster_art = db.Column(db.String(20), nullable=False, default='kettlewright', server_default='kettlewright')
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(2000))
    # Its picture (#476), set by the Warden: on the party page and as its wiki's cover.
    image = db.Column(db.String(2000), nullable=False, default='', server_default='')
    notes = db.Column(db.String(2000))
    members = db.Column(db.String(2000))
    subowners = db.Column(db.String(2000))
    join_code = db.Column(db.String(64))
    party_url = db.Column(db.String(200))
    owner_username = db.Column(db.String(100))
    items = db.Column(db.String)
    containers = db.Column(db.String)
    events = db.Column(db.String)
    version = db.Column(db.Integer, nullable=False, default=0)

    @property
    def hirelings(self):
        return [c for c in self.party_companions if c.kind == 'hireling']

    @property
    def monsters(self):
        return [c for c in self.party_companions if c.kind == 'monster']

    def to_dict(self):
        return {
            'id': self.id,
            'owner': self.owner,
            'created_at': self.created_at,
            'name': self.name,
            'description': self.description,
            'notes': self.notes,
            'members': self.members,
            # excluding join_code so that it's not exposed to users
            'party_url': self.party_url,
            'owner_username': self.owner_username,
            'items': self.items,
            'containers': self.containers,
            'events': self.events
        }



class Star(db.Model):
    """Something someone starred (#476): a bookmark, listed first on their Campaigns page.

    kind is party, module, article, map or background; target_id the party, module or article (a map is
    its article); a background is its module and its name."""
    __tablename__ = 'stars'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), nullable=False, default='', server_default='')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.relationship('User', backref=db.backref('stars', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('user_id', 'kind', 'target_id', 'name', name='uq_star'),)

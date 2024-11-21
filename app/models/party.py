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
    owner = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(2000))
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

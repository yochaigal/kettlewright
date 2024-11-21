from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import sys
import json
from .globals import db

class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    url_name = db.Column(db.String(100))
    owner = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner_username = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    name = db.Column(db.String(64), nullable=False)
    background = db.Column(db.String(64), nullable=False)
    custom_name = db.Column(db.String(64))
    custom_background = db.Column(db.String(64))
    strength = db.Column(db.Integer)
    strength_max = db.Column(db.Integer)
    dexterity = db.Column(db.Integer)
    dexterity_max = db.Column(db.Integer)
    willpower = db.Column(db.Integer)
    willpower_max = db.Column(db.Integer)
    hp = db.Column(db.Integer)
    hp_max = db.Column(db.Integer)
    deprived = db.Column(db.Boolean)
    items = db.Column(db.String)
    containers = db.Column(db.String)
    gold = db.Column(db.Integer)
    description = db.Column(db.String(2000))
    traits = db.Column(db.String(2000))
    notes = db.Column(db.String(2000))
    bonds = db.Column(db.String(2000))
    scars = db.Column(db.String(2000))
    omens = db.Column(db.String(2000))
    custom_image = db.Column(db.Boolean)
    image_url = db.Column(db.String(512))
    armor = db.Column(db.String(16))
    party_code = db.Column(db.String(64))
    party_id = db.Column(db.Integer)

    def to_dict(self):  # convert to python dictionary
        return {
            'id': self.id,
            'url_name': self.url_name,
            'owner': self.owner,
            'owner_username': self.owner_username,
            'created_at': self.created_at,
            'name': self.name,
            'background': self.background,
            'strength': self.strength,
            'strength_max': self.strength_max
        }

    def __repr__(self):
        return f'<Character {self.name}>'
    
    # Compute HP value, returns current and max
    def hpValue(self):
        hp = self.hp
        if self.occupiedSlots() >= 10:
            hp = 0
        return [hp,self.hp_max]
    
    # Returns True if character is overburdened
    def overburdened(self):
        return self.occupiedSlots() >= 10
    
    # Compute armor value based on possessed items
    def armorValue(self):
        armor = 0
        if self.items == None:
            return 0
        items = json.loads(self.items)
        if  len(self.items) == 0:
            return 0
        for it in items:
            if it["location"] != 0:
                continue
            if it["tags"] == None or len(it["tags"]) == 0:
                continue
            if "1 Armor" in it["tags"]:
                armor += 1
            if "2 Armor" in it["tags"]:
                armor += 2
            if "3 Armor" in it["tags"]:
                armor += 3
        if armor > 3:
            armor = 3
        return armor
    
    # Compute occupied slots based on possessed items
    def occupiedSlots(self):
        if self.items == None:
            return 0
        items = json.loads(self.items)
        if  len(self.items) == 0:
            return 0
        slots = 0
        for it in items:
            if "petty" in it["tags"]:
                continue
            if "bulky" in it["tags"]:
                slots += 2
            else:
                slots += 1
        return slots
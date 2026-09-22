from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import sys
import json
from .globals import db

def item_armor_value(item):
    # Old Sloth-Tarps also require explicit activation; ordinary armor stays active.
    active = item.get('armor_active', item.get('name') != 'Sloth-Tarp')
    if not active or item.get('location') != 0:
        return 0
    tags = item.get('tags') or []
    return sum(value for value in (1, 2, 3) if f'{value} Armor' in tags)


class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    url_name = db.Column(db.String(100))
    owner = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
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
    panicked = db.Column(db.Boolean)
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
        if self.occupiedMainSlots() >= 10 or self.panicked:
            hp = 0
        return [hp,self.hp_max]
    
    # Returns True if character is overburdened
    def overburdened(self):
        max = 10
        containers = json.loads(self.containers)
        for c in containers:
            if c['id'] == 0:
                max = c['slots']
        return self.occupiedMainSlots() >= max
    
    # Compute armor value based on possessed items
    def armorValue(self):
        return min(3, sum(item_armor_value(item) for item in json.loads(self.items or '[]')))

    # Compute occupied slots based on possessed items
    # but only for a main container
    def occupiedMainSlots(self):
        if self.items == None:
            return 0
        items = json.loads(self.items)
        if  len(self.items) == 0:
            return 0
        slots = 0
        for it in items:
            if "petty" in it["tags"] or it["location"] != 0:
                continue
            if "bulky" in it["tags"]:
                slots += 2
                continue
            slots += 1
        return slots
    
    # Free slots in the main inventory; extra containers have their own capacity.
    def freeMainSlots(self):
        capacity = 10
        for container in json.loads(self.containers or '[]'):
            if container['id'] == 0:
                capacity = int(container['slots'])
                break
        return max(0, capacity - self.occupiedMainSlots())

    # Serialize object to JSON
    def toJSON(self):
        excluded = {'id', 'party_id', 'party_code', 'created_at', 'url_name', 'owner_username', 'owner'}
        data = {column.name: getattr(self, column.name) for column in self.__table__.columns
                if column.name not in excluded}
        data['items'] = json.loads(self.items or '[]')
        data['containers'] = json.loads(self.containers or '[]')
        data['armor'] = self.armorValue()
        return json.dumps(data, indent=4, sort_keys=True)

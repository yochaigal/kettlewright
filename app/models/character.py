from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import sys
import json
from .globals import db
from .game_stats import SystemStats
from .game_system import GAME_SYSTEM_DEFAULT
from kettlewright import system

BACKGROUND_FIELDS = ('background_table1_question', 'background_table1_answer', 'background_table2_question', 'background_table2_answer')

# Rules edition a character was made with. Barebones characters have no bonds,
# omens or background tables, so their sheets leave those sections out.
EDITION_SECOND = '2e'
EDITION_BAREBONES = 'barebones'
EDITIONS = (EDITION_SECOND, EDITION_BAREBONES)


class Character(SystemStats, db.Model):
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
    dead = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    items = db.Column(db.String)
    containers = db.Column(db.String)
    gold = db.Column(db.Integer)
    description = db.Column(db.String(2000))
    traits = db.Column(db.String(2000))
    notes = db.Column(db.String(2000))
    background_table1_question = db.Column(db.String(2000))
    background_table1_answer = db.Column(db.String(2000))
    background_table2_question = db.Column(db.String(2000))
    background_table2_answer = db.Column(db.String(2000))

    bonds = db.Column(db.String(2000))
    scars = db.Column(db.String(2000))
    omens = db.Column(db.String(2000))
    custom_image = db.Column(db.Boolean)
    image_url = db.Column(db.String(512))
    armor = db.Column(db.String(16))
    # Stats of the game system that have no column of their own (#487; see game_stats.py).
    system_stats = db.Column(db.Text, nullable=False, default='{}', server_default='{}')
    # The game system it plays (#487): its party's when it was created (or the default one), and fixed after
    # (app/models/game_system.py). It only joins a party of the same system.
    game_system = db.Column(db.String(32), nullable=False, default=GAME_SYSTEM_DEFAULT, server_default='cairn')
    party_code = db.Column(db.String(64))
    party_id = db.Column(db.Integer)
    edition = db.Column(db.String(16), nullable=False, default=EDITION_SECOND, server_default=EDITION_SECOND)

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

    @property
    def is_barebones(self):
        return self.edition == EDITION_BAREBONES

    def __repr__(self):
        return f'<Character {self.name}>'
    
    # The rules below are the game system's (kettlewright, #487): its party's campaign's, or the default one.

    @property
    def rules(self):
        """Its game system (kettlewright, #487); the default one if its key is no longer known."""
        from kettlewright import system_or_default
        return system_or_default(self.game_system)

    def active_conditions(self):
        return tuple(key for key in self.rules.condition_keys if getattr(self, key, False))

    # HP that counts right now, and its maximum (Cairn: 0 with a full inventory or Panicked).
    def hpValue(self):
        return [self.rules.effective_hp(self.hp, self.occupiedMainSlots(), self.active_conditions()), self.hp_max]

    # Returns True if the main inventory is full.
    def overburdened(self):
        return self.occupiedMainSlots() >= self.rules.inventory.main_capacity(json.loads(self.containers))

    # Armor from the items carried, up to the system's maximum.
    def armorValue(self):
        return self.rules.armor_value(json.loads(self.items or '[]'))

    # Slots used in the main inventory, coins included (#507).
    def occupiedMainSlots(self):
        return self.rules.inventory.occupied_main_slots(json.loads(self.items or '[]'), self.gold)

    # Free slots in the main inventory; extra containers have their own capacity.
    def freeMainSlots(self):
        capacity = self.rules.inventory.main_capacity(json.loads(self.containers or '[]'))
        return max(0, capacity - self.occupiedMainSlots())

    # The exported sheet as a dictionary; JSON and Markdown exports both use it.
    def export_data(self):
        excluded = {'id', 'party_id', 'party_code', 'created_at', 'url_name', 'owner_username', 'owner'}
        data = {column.name: getattr(self, column.name) for column in self.__table__.columns
                if column.name not in excluded}
        # A game system's stats without a column (#487) are listed like the others: {'luck': 7, 'luck_max': 9}.
        data.update(self._extra_stats())
        data['items'] = json.loads(self.items or '[]')
        data['containers'] = json.loads(self.containers or '[]')
        data['armor'] = self.armorValue()
        data['pets'] = [pet.export() for pet in self.pets]
        return data

    # Serialize object to JSON
    def toJSON(self):
        return json.dumps(self.export_data(), indent=4, sort_keys=True)

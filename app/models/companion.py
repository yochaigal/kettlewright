"""Small sheets for party hirelings and character (or hireling) pets."""
import json
from .globals import db
from .character import item_armor_value


class Companion(db.Model):
    __tablename__ = 'companions'
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id', ondelete='CASCADE'), index=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), index=True)
    hireling_id = db.Column(db.Integer, db.ForeignKey('companions.id', ondelete='CASCADE'), index=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='')
    hp = db.Column(db.Integer)
    hp_max = db.Column(db.Integer)
    strength = db.Column(db.Integer)
    strength_max = db.Column(db.Integer)
    dexterity = db.Column(db.Integer)
    dexterity_max = db.Column(db.Integer)
    willpower = db.Column(db.Integer)
    willpower_max = db.Column(db.Integer)
    armor = db.Column(db.Integer, nullable=False, default=0)
    attack = db.Column(db.String(200), nullable=False, default='')
    daily_cost = db.Column(db.Integer, nullable=False, default=0)
    gold = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=False, default='')
    items = db.Column(db.Text, nullable=False, default='[]')
    containers = db.Column(db.Text, nullable=False, default='[{"id": 0, "name": "Main", "slots": 10}]')
    shared = db.Column(db.Boolean, nullable=False, default=True)
    character = db.relationship('Character', backref=db.backref('pets', cascade='all, delete-orphan', order_by='Companion.id'))
    party = db.relationship('Party', backref=db.backref('hirelings', cascade='all, delete-orphan', order_by='Companion.id'))
    hireling = db.relationship('Companion', remote_side=[id], backref=db.backref('pets', cascade='all, delete-orphan', order_by='Companion.id'))
    __table_args__ = (db.CheckConstraint(
        "(kind = 'hireling' AND party_id IS NOT NULL AND character_id IS NULL AND hireling_id IS NULL) OR "
        "(kind = 'pet' AND party_id IS NULL AND ((character_id IS NOT NULL AND hireling_id IS NULL) OR "
        "(character_id IS NULL AND hireling_id IS NOT NULL)))", name='companion_parent'),)

    def armorValue(self):
        return min(3, (self.armor or 0) + sum(item_armor_value(it) for it in json.loads(self.items or '[]')))

    def export(self):
        fields = ('name', 'role', 'hp', 'hp_max', 'strength', 'strength_max', 'dexterity', 'dexterity_max',
                  'willpower', 'willpower_max', 'armor', 'attack', 'gold', 'notes')
        result = {field: getattr(self, field) for field in fields}
        result.update(items=json.loads(self.items or '[]'), containers=json.loads(self.containers or '[]'))
        return result

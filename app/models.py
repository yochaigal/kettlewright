from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
import sys

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), default=func.now())
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))
    username = db.Column(db.String(1000), unique=True)
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def generate_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    @staticmethod
    def confirm_email(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=3600)
            print(data.get('confirm'), file=sys.stdout)
            return data.get('confirm')
        except:
            return False

    def __repr__(self):
        return f'<User {self.username}>'


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

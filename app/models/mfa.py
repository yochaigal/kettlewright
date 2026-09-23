"""One expiring, single-use email challenge per account."""
from .globals import db


class MFAChallenge(db.Model):
    __tablename__ = 'mfa_challenges'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    nonce = db.Column(db.String(64), nullable=False, unique=True)
    code_hash = db.Column(db.String(64), nullable=False)
    binding = db.Column(db.String(64), nullable=False)
    purpose = db.Column(db.String(10), nullable=False)
    expires = db.Column(db.Integer, nullable=False)
    sent_at = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    user = db.relationship('User', backref=db.backref('mfa_challenges', cascade='all, delete-orphan'))

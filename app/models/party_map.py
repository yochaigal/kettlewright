from .globals import db


class PartyMap(db.Model):
    __tablename__ = 'party_maps'

    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True)
    drawing = db.Column(db.JSON, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)

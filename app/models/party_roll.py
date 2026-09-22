from datetime import datetime, timezone

from .globals import db


class PartyRoll(db.Model):
    __tablename__ = 'party_rolls'
    __table_args__ = (db.Index('ix_party_rolls_party_id_id', 'party_id', 'id'),)

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    # Keep the name and result even if the character is renamed or deleted.
    character_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @classmethod
    def latest(cls, party_id):
        return cls.query.filter_by(party_id=party_id).order_by(cls.id.desc()).limit(20).all()

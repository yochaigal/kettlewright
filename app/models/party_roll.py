from datetime import datetime, timezone

from .globals import db


class PartyRoll(db.Model):
    __tablename__ = 'party_rolls'
    __table_args__ = (db.Index('ix_party_rolls_party_id_id', 'party_id', 'id'),)

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    # Keep the name and result even if the character is renamed or deleted.
    character_name = db.Column(db.String(100), nullable=False)
    # NULL denotes a shared roll; private rolls belong to their original roller.
    private_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    result = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @classmethod
    def latest(cls, party_id, viewer_id):
        return cls.query.filter_by(party_id=party_id).filter(
            db.or_(cls.private_user_id.is_(None), cls.private_user_id == viewer_id)
        ).order_by(cls.id.desc()).limit(20).all()

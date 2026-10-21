from .globals import db


class PartyMap(db.Model):
    __tablename__ = 'party_maps'

    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True)
    active_scene_id = db.Column(db.Integer)
    activation_version = db.Column(db.Integer, nullable=False, default=0)
    drawing = db.Column(db.JSON, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    generation = db.Column(db.Integer, nullable=False, default=1)
    fog_version = db.Column(db.Integer, nullable=False, default=0)
    fog = db.Column(db.JSON, nullable=False, default=lambda: {
        'enabled': False, 'base': 'covered', 'strokes': [], 'applied': []})


class WhiteboardScene(db.Model):
    __tablename__ = 'whiteboard_scenes'
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, default='Whiteboard')
    drawing = db.Column(db.JSON, nullable=False, default=lambda: {'elements': [], 'files': {}})
    version = db.Column(db.Integer, nullable=False, default=0)
    generation = db.Column(db.Integer, nullable=False, default=1)
    fog = db.Column(db.JSON, nullable=False, default=lambda: {
        'enabled': False, 'base': 'covered', 'strokes': [], 'applied': []})
    fog_version = db.Column(db.Integer, nullable=False, default=0)
    tokens_version = db.Column(db.Integer, nullable=False, default=0)
    encounter = db.Column(db.JSON, nullable=False, default=lambda: {'round': 1, 'participants': []})
    encounter_version = db.Column(db.Integer, nullable=False, default=0)
    markers_version = db.Column(db.Integer, nullable=False, default=0)
    tokens = db.relationship('WhiteboardToken', cascade='all, delete-orphan', backref='scene')
    markers = db.relationship('WhiteboardMarker', cascade='all, delete-orphan', backref='scene')


class WhiteboardToken(db.Model):
    __tablename__ = 'whiteboard_tokens'
    scene_id = db.Column(db.Integer, db.ForeignKey('whiteboard_scenes.id', ondelete='CASCADE'), primary_key=True)
    id = db.Column(db.String(200), primary_key=True)
    actor_key = db.Column(db.String(80), nullable=False)
    element = db.Column(db.JSON, nullable=False)
    files = db.Column(db.JSON, nullable=False, default=dict)
    visible = db.Column(db.Boolean, nullable=False, default=True)
    numbered = db.Column(db.Boolean, nullable=False, default=False)


class WhiteboardMarker(db.Model):
    __tablename__ = 'whiteboard_markers'
    scene_id = db.Column(db.Integer, db.ForeignKey('whiteboard_scenes.id', ondelete='CASCADE'), primary_key=True)
    id = db.Column(db.String(80), primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    number = db.Column(db.String(40), nullable=False, default='')

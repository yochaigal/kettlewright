"""Saved Whiteboard scenes and private managed objects."""
from copy import deepcopy
import re
from alembic import op
import sqlalchemy as sa

revision = '375a01'
down_revision = '296a02'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('party_maps') as batch:
        batch.add_column(sa.Column('active_scene_id', sa.Integer()))
        batch.add_column(sa.Column('activation_version', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('whiteboard_scenes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('drawing', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('generation', sa.Integer(), nullable=False),
        sa.Column('fog', sa.JSON(), nullable=False),
        sa.Column('fog_version', sa.Integer(), nullable=False),
        sa.Column('tokens_version', sa.Integer(), nullable=False),
        sa.Column('encounter', sa.JSON(), nullable=False),
        sa.Column('encounter_version', sa.Integer(), nullable=False),
        sa.Column('markers_version', sa.Integer(), nullable=False))
    op.create_index('ix_whiteboard_scenes_party_id', 'whiteboard_scenes', ['party_id'])
    op.create_table('whiteboard_tokens',
        sa.Column('scene_id', sa.Integer(), sa.ForeignKey('whiteboard_scenes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('id', sa.String(200), primary_key=True),
        sa.Column('actor_key', sa.String(80), nullable=False),
        sa.Column('element', sa.JSON(), nullable=False), sa.Column('files', sa.JSON(), nullable=False),
        sa.Column('visible', sa.Boolean(), nullable=False), sa.Column('numbered', sa.Boolean(), nullable=False))
    op.create_table('whiteboard_markers',
        sa.Column('scene_id', sa.Integer(), sa.ForeignKey('whiteboard_scenes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('id', sa.String(80), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('x', sa.Float(), nullable=False), sa.Column('y', sa.Float(), nullable=False),
        sa.Column('number', sa.String(40), nullable=False))
    connection = op.get_bind()
    meta = sa.MetaData()
    tables = {name: sa.Table(name, meta, autoload_with=connection) for name in
              ('party_maps', 'whiteboard_scenes', 'whiteboard_tokens', 'characters', 'companions', 'parties')}
    for row in connection.execute(sa.select(tables['party_maps'])).mappings().all():
        party_id = row['party_id']
        import json
        party = connection.execute(sa.select(tables['parties']).where(tables['parties'].c.id == party_id)).mappings().one()
        members = set(json.loads(party['members'] or '[]'))
        characters = {c['id'] for c in connection.execute(sa.select(tables['characters']).where(
            tables['characters'].c.party_id == party_id)).mappings() if c['id'] in members}
        companions = connection.execute(sa.select(tables['companions'])).mappings().all()
        hirelings = {c['id'] for c in companions if c['party_id'] == party_id and c['kind'] == 'hireling'}
        actors = {str(key) for key in characters} | {f"companion:{c['id']}" for c in companions if
            c['party_id'] == party_id or c['character_id'] in characters or c['hireling_id'] in hirelings}
        drawing = deepcopy(row['drawing'])
        result = connection.execute(tables['whiteboard_scenes'].insert().values(
            party_id=party_id, name='Whiteboard', drawing=drawing, version=row['version'],
            generation=row['generation'], fog=row['fog'], fog_version=row['fog_version'], tokens_version=0,
            encounter={'round': 1, 'participants': []}, encounter_version=0, markers_version=0))
        scene_id = result.inserted_primary_key[0]
        retained = []
        for element in drawing['elements']:
            match = re.match(r'^actor-(companion-)?(\d+)-', element['id'])
            actor = ('companion:' if match[1] else '') + match[2] if match else None
            if actor in actors and element.get('type') == 'image':
                file_id = element.get('fileId')
                connection.execute(tables['whiteboard_tokens'].insert().values(
                    scene_id=scene_id, id=element['id'], actor_key=actor, element=element,
                    files={file_id: drawing['files'][file_id]} if file_id in drawing['files'] else {},
                    visible=True, numbered=False))
            else:
                # Orphans remain ordinary, unlinked drawing objects.
                if match:
                    element['id'] = 'orphan-' + element['id']
                retained.append(element)
        used = {e.get('fileId') for e in retained}
        drawing['elements'] = retained
        drawing['files'] = {key: value for key, value in drawing['files'].items() if key in used}
        connection.execute(tables['whiteboard_scenes'].update().where(tables['whiteboard_scenes'].c.id == scene_id).values(drawing=drawing))
        connection.execute(tables['party_maps'].update().where(tables['party_maps'].c.party_id == party_id).values(
            active_scene_id=scene_id, drawing={'elements': [], 'files': {}}))


def downgrade():
    connection = op.get_bind()
    meta = sa.MetaData()
    boards, scenes, tokens = [sa.Table(name, meta, autoload_with=connection) for name in
                              ('party_maps', 'whiteboard_scenes', 'whiteboard_tokens')]
    for board in connection.execute(sa.select(boards)).mappings().all():
        scene = connection.execute(sa.select(scenes).where(scenes.c.id == board['active_scene_id'])).mappings().first()
        if scene:
            drawing = deepcopy(scene['drawing'])
            for token in connection.execute(sa.select(tokens).where(tokens.c.scene_id == scene['id'])).mappings():
                drawing['elements'].append(token['element'])
                drawing['files'].update(token['files'])
            connection.execute(boards.update().where(boards.c.party_id == board['party_id']).values(
                drawing=drawing, version=scene['version'], generation=scene['generation'],
                fog=scene['fog'], fog_version=scene['fog_version']))
    op.drop_table('whiteboard_markers')
    op.drop_table('whiteboard_tokens')
    op.drop_table('whiteboard_scenes')
    with op.batch_alter_table('party_maps') as batch:
        batch.drop_column('activation_version')
        batch.drop_column('active_scene_id')

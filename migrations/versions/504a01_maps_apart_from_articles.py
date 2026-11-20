"""Maps apart from articles: no drawing snapshots, no empty canvases on articles.

A revealed map now always shows its current drawing, so each party's copy of the drawing
(party_presentations.drawing) is dropped. Articles no longer get a canvas automatically:
empty canvases that were attached to points and sub-articles (no points, paths, pins or
drawing) are removed. Maps that someone made (a root article, or with any content) stay.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = '504a01'
down_revision = '503a01'
branch_labels = None
depends_on = None


def drawn(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return True
    return bool((value or {}).get('elements'))


def upgrade():
    bind = op.get_bind()
    used = {row[0] for row in bind.execute(sa.text(
        'SELECT map_id FROM map_nodes UNION SELECT map_id FROM map_edges UNION SELECT map_id FROM map_pins'))}
    placed = {row[0] for row in bind.execute(sa.text('SELECT entry_id FROM map_nodes'))}
    rows = bind.execute(sa.text(
        'SELECT m.id, m.drawing, e.id, e.parent_id, e.category FROM pointcrawl_maps m '
        'JOIN content_entries e ON e.id = m.entry_id')).all()
    empty = [map_id for map_id, drawing, entry_id, parent_id, category in rows
             if map_id not in used and not drawn(drawing) and category != 'realm'
             and (parent_id is not None or entry_id in placed)]
    for map_id in empty:
        bind.execute(sa.text('UPDATE map_nodes SET nested_map_id = NULL WHERE nested_map_id = :id'), {'id': map_id})
        bind.execute(sa.text('DELETE FROM pointcrawl_maps WHERE id = :id'), {'id': map_id})
    with op.batch_alter_table('party_presentations') as batch:
        batch.drop_column('drawing')


def downgrade():
    # Parties saw the drawing as it is now: give each revealed map that snapshot back.
    with op.batch_alter_table('party_presentations') as batch:
        batch.add_column(sa.Column('drawing', sa.JSON(), nullable=True))
    op.execute('UPDATE party_presentations SET drawing = (SELECT m.drawing FROM pointcrawl_maps m '
               'WHERE m.entry_id = party_presentations.entry_id) '
               'WHERE entry_id IN (SELECT entry_id FROM pointcrawl_maps)')

"""Typed setting articles and settlement Heart flag.

Unknown legacy locations retain all content as Custom; explicit generator
prefixes and map kinds supply types without guessing from arbitrary prose.
"""
from alembic import op
import sqlalchemy as sa
import re

revision = '321a01'
down_revision = '320a01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_entries', sa.Column('is_heart', sa.Boolean(), nullable=False, server_default=sa.false()))
    connection = op.get_bind()
    points = {'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon', 'forest',
              'terrain', 'water', 'room', 'monster', 'ruins', 'shelter', 'hazard', 'trap', 'special', 'lore'}
    for row in connection.execute(sa.text("SELECT id, title FROM content_entries WHERE category = 'location'")).mappings():
        match = re.match(r'^(?:\d+\.\s*)?(?:Heart\s*[·:]\s*)?([A-Za-z]+):', row['title'] or '', re.I)
        kind = match.group(1).lower() if match else 'custom'
        kind = kind if kind in points else 'custom'
        heart = kind == 'settlement' and bool(re.match(r'^(?:\d+\.\s*)?Heart\s*[·:]', row['title'] or '', re.I))
        connection.execute(sa.text('UPDATE content_entries SET category=:kind, is_heart=:heart WHERE id=:id'),
                           {'kind': kind, 'heart': heart, 'id': row['id']})
    connection.execute(sa.text("UPDATE content_entries SET category=(SELECT kind FROM pointcrawl_maps WHERE entry_id=content_entries.id) WHERE category='map' AND id IN (SELECT entry_id FROM pointcrawl_maps WHERE kind IN ('realm','forest','dungeon'))"))


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE content_entries SET category='map' WHERE id IN (SELECT entry_id FROM pointcrawl_maps)"))
    connection.execute(sa.text("UPDATE content_entries SET category='location' WHERE id IN (SELECT entry_id FROM map_nodes)"))
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_column('is_heart')

"""Stable Markdown article references and independent publication bindings."""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
import re

revision = '336a01'
down_revision = '335a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.add_column(sa.Column('source_path', sa.String(500), nullable=False, server_default=''))
        batch.add_column(sa.Column('references', sa.JSON(), nullable=False, server_default='{}'))
        batch.add_column(sa.Column('reference_key', sa.String(32), nullable=True))
    connection = op.get_bind()
    used = set()
    for row in connection.execute(sa.text('SELECT id,owner_id,campaign_id,title FROM content_entries ORDER BY id')).mappings().all():
        key = uuid4().hex
        name = re.sub(r'[\\/:\x00-\x1f]', '-', row['title'] or '').strip().strip('.') or 'article'
        path = f'articles/{name[:180]}.md'
        scope = (row['owner_id'], row['campaign_id'])
        if (*scope, path) in used:
            path = f'articles/{name[:180]}-{key[:8]}.md'
        used.add((*scope, path))
        connection.execute(sa.text('UPDATE content_entries SET reference_key=:key, source_path=:path WHERE id=:id'),
                           {'id': row['id'], 'key': key, 'path': path})
    with op.batch_alter_table('content_entries') as batch:
        batch.alter_column('reference_key', existing_type=sa.String(32), nullable=False)
        batch.create_unique_constraint('uq_content_entry_reference_key', ['reference_key'])
    with op.batch_alter_table('party_presentations') as batch:
        batch.add_column(sa.Column('references', sa.JSON(), nullable=False, server_default='{}'))


def downgrade():
    with op.batch_alter_table('party_presentations') as batch:
        batch.drop_column('references')
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_column('references')
        batch.drop_column('source_path')
        batch.drop_constraint('uq_content_entry_reference_key', type_='unique')
        batch.drop_column('reference_key')

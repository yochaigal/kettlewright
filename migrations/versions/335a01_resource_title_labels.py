"""Label abundance and scarcity in generated resource titles.

Only titles matching the previous generated format are changed. Custom titles,
descriptions and published party copies are preserved.
"""
import re

from alembic import op
import sqlalchemy as sa

revision = '335a01'
down_revision = '323a01'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "SELECT id, title, body FROM content_entries WHERE category='resources'"
    )).mappings().all()
    for row in rows:
        fields = dict(re.findall(r'^\*\*([^*\n]+):\*\*\s*([^\n]+)', row['body'] or '', re.M))
        abundance = fields.get('Abundance', '').strip()
        scarcity = fields.get('Scarcity', '').strip()
        if not abundance or not scarcity:
            continue
        previous = f'{abundance} · Scarce: {scarcity}'[:200]
        if row['title'] != previous:
            continue
        connection.execute(sa.text(
            'UPDATE content_entries SET title=:title, version=version+1 WHERE id=:id'
        ), {'id': row['id'], 'title': f'Abundance: {abundance} · Scarcity: {scarcity}'[:200]})


def downgrade():
    # Later user edits cannot be distinguished safely from generated titles.
    pass

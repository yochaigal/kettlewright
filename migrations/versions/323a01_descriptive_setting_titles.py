"""Replace generated placeholder headings with their rolled descriptions.

Only exact placeholders with recognizable generated Markdown are changed.
Custom titles and published party copies are preserved. Renames are not undone
on downgrade, since later user edits cannot be distinguished safely.
"""
import re
from alembic import op
import sqlalchemy as sa

revision = '323a01'
down_revision = '322a01'
branch_labels = None
depends_on = None


def upgrade():
    specifications = {
        'culture': ('Culture', ['Character', 'Ambition']),
        'resources': ('Resources', ['Abundance', 'Scarcity']),
        'faction_type': ('Faction types', ['Type', 'Agent']),
        'faction_trait': ('Faction traits', ['Trait 1', 'Trait 2']),
        'advantage': ('Advantages', ['Advantages']),
        'agenda': ('Agendas', ['Agenda']),
    }
    connection = op.get_bind()
    for category, (placeholder, keys) in specifications.items():
        rows = connection.execute(sa.text(
            'SELECT id, body FROM content_entries WHERE category=:category AND title=:title'),
            {'category': category, 'title': placeholder}).mappings().all()
        for row in rows:
            fields = dict(re.findall(r'^\*\*([^*\n]+):\*\*\s*([^\n]+)', row['body'] or '', re.M))
            if not all(fields.get(key, '').strip() for key in keys):
                continue
            values = [fields[key].strip() for key in keys]
            if category == 'resources':
                values[1] = 'Scarce: ' + values[1]
            connection.execute(sa.text(
                'UPDATE content_entries SET title=:title, version=version+1 WHERE id=:id'),
                {'id': row['id'], 'title': ' · '.join(values)[:200]})


def downgrade():
    pass

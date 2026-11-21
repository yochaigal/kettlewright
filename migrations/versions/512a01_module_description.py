"""A module's front page is its description, not an article named after it.

Adding a module (CAS-1 and the other bundled ones) made an Overview article with the module's own title,
so the module's header and its first article repeated. Its text moves to modules.description and the
article goes, unless something visible depends on it: sub-articles, a map, a [[link]] in another article's
text or a picture of its own; those stay as they are. Being revealed to a party (Reveal module reveals the
front page too) or chosen as a related article does not keep it: those reveals and links go with it.

Not reversible: the downgrade drops the column (moved text included)."""
from alembic import op
import sqlalchemy as sa

revision = '512a01'
down_revision = '511a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('modules') as batch:
        batch.add_column(sa.Column('description', sa.Text(), nullable=False, server_default=''))
    connection = op.get_bind()
    fronts = connection.execute(sa.text("""
        SELECT e.id, e.module_id, e.body, e.reference_key FROM content_entries e JOIN modules m ON m.id = e.module_id
        WHERE e.category = 'overview' AND e.title = m.title AND e.parent_id IS NULL AND e.image = ''
          AND NOT EXISTS (SELECT 1 FROM content_entries c WHERE c.parent_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM pointcrawl_maps p WHERE p.entry_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM map_nodes n WHERE n.entry_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM map_edges n WHERE n.entry_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM map_pins n WHERE n.entry_id = e.id)
        ORDER BY e.id""")).fetchall()
    moved = set()
    for entry_id, module_id, body, key in fronts:
        if module_id in moved:
            continue
        linked = connection.execute(sa.text(
            'SELECT 1 FROM content_entries WHERE id != :id AND CAST("references" AS TEXT) LIKE :key'),
            {'id': entry_id, 'key': f'%{key}%'}).first()
        if linked:
            continue
        connection.execute(sa.text('UPDATE modules SET description = :body WHERE id = :id'),
                           {'body': body or '', 'id': module_id})
        # SQLite may not enforce ON DELETE CASCADE here: remove what points at the article first.
        connection.execute(sa.text("DELETE FROM stars WHERE kind = 'article' AND target_id = :id"), {'id': entry_id})
        connection.execute(sa.text('DELETE FROM party_presentations WHERE entry_id = :id'), {'id': entry_id})
        connection.execute(sa.text('DELETE FROM content_links WHERE source_id = :id OR target_id = :id'), {'id': entry_id})
        connection.execute(sa.text('DELETE FROM content_entries WHERE id = :id'), {'id': entry_id})
        moved.add(module_id)


def downgrade():
    with op.batch_alter_table('modules') as batch:
        batch.drop_column('description')

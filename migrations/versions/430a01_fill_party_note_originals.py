"""Fill blank private originals of articles created from a party page.

"Create and show" used to keep a party note's text only in the party's version,
leaving a blank "Untitled private original" in the Warden's library. New notes
save the text in both. Copy it into old originals that are still blank and have
exactly one party version. Data only: no schema change.
"""
from alembic import op
import sqlalchemy as sa

revision = '430a01'
down_revision = '292a01'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "SELECT e.id, MIN(p.title) AS title, MIN(p.body) AS body "
        "FROM content_entries e JOIN party_presentations p ON p.entry_id = e.id "
        "WHERE e.title = '' AND e.body = '' "
        "GROUP BY e.id HAVING COUNT(p.id) = 1")).mappings().all()
    for row in rows:
        connection.execute(sa.text('UPDATE content_entries SET title = :title, body = :body WHERE id = :id'), dict(row))


def downgrade():
    # The copied text is the Warden's own note either way; nothing to undo.
    pass

"""No party versions: a party reads the original article.

A revealed article's party copy (party_presentations) now mirrors the original. Copies
whose title or text differ (party versions, or originals edited after they were revealed)
are not overwritten, since that could show the party text the Warden kept from it. Each
becomes a party note for that party, with exactly the text it had, and the article is
hidden from that party until the Warden reveals it again. Copies that match get the
original's path type and references.
"""
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = '502a01'
down_revision = '501a01'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "SELECT p.id, p.party_id, p.title, p.body, e.owner_id, e.title, e.body "
        "FROM party_presentations p JOIN content_entries e ON e.id = p.entry_id "
        "WHERE e.category != 'party_note' ORDER BY p.id")).all()
    for row_id, party_id, title, body, owner_id, original_title, original_body in rows:
        if (title, body) == (original_title, original_body):
            continue
        connection.execute(sa.text(
            "INSERT INTO content_entries (owner_id, category, title, body, path_type, version, source_path, "
            "reference_key, \"references\", is_heart) VALUES (:owner, 'party_note', :title, :body, 'standard', 1, '', "
            ":key, '{}', :heart)"), {'owner': owner_id, 'title': (title or original_title or 'Note')[:200],
                                     'body': body or '', 'key': uuid4().hex, 'heart': False})
        note_id = connection.execute(sa.text('SELECT MAX(id) FROM content_entries WHERE owner_id = :owner'),
                                     {'owner': owner_id}).scalar()
        connection.execute(sa.text(
            "INSERT INTO party_presentations (entry_id, party_id, title, body, \"references\", path_type, published, version) "
            "VALUES (:entry, :party, :title, :body, '{}', 'standard', :published, 1)"),
            {'entry': note_id, 'party': party_id, 'title': (title or original_title or 'Note')[:200], 'body': body or '',
             'published': True})
        connection.execute(sa.text('DELETE FROM party_presentations WHERE id = :id'), {'id': row_id})
    connection.execute(sa.text(
        "UPDATE party_presentations SET path_type = (SELECT e.path_type FROM content_entries e WHERE e.id = party_presentations.entry_id), "
        "\"references\" = (SELECT e.\"references\" FROM content_entries e WHERE e.id = party_presentations.entry_id) "
        "WHERE entry_id IN (SELECT id FROM content_entries WHERE category != 'party_note')"))


def downgrade():
    # The notes keep what each party knew; nothing to undo.
    pass

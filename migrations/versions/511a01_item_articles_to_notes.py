"""Item, relic and spellbook articles become Notes (#476): items are a module's items now.

Their text is kept as it is. Not reversible: a Note does not say which type it was."""
from alembic import op

revision = '511a01'
down_revision = '510a01'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE content_entries SET category = 'note' WHERE category IN ('item', 'relic', 'spellbook')")


def downgrade():
    pass

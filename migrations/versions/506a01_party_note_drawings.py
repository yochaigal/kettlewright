"""Party notes can hold a drawing: a sketch below their text (Excalidraw, like a map's drawing)."""
from alembic import op
import sqlalchemy as sa

revision = '506a01'
down_revision = '505a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.add_column(sa.Column('drawing', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_column('drawing')

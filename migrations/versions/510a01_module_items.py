"""Module items (#476): gear, relics and spellbooks a module holds, to send to a party."""
from alembic import op
import sqlalchemy as sa

revision = '510a01'
down_revision = '509a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('modules') as batch:
        batch.add_column(sa.Column('items', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('modules') as batch:
        batch.drop_column('items')

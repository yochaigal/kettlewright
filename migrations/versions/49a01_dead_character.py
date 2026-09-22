"""Track deceased characters without deleting their sheets (#49)."""
from alembic import op
import sqlalchemy as sa

revision = '49a01'
down_revision = '066ddbbebeb8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('characters') as batch_op:
        batch_op.add_column(sa.Column('dead', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('characters') as batch_op:
        batch_op.drop_column('dead')

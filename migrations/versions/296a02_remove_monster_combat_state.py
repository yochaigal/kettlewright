"""Every party monster is available as a Whiteboard token."""
from alembic import op
import sqlalchemy as sa

revision = '296a02'
down_revision = '296a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('companions') as batch:
        batch.drop_column('in_combat')


def downgrade():
    with op.batch_alter_table('companions') as batch:
        batch.add_column(sa.Column('in_combat', sa.Boolean(), nullable=False, server_default='0'))

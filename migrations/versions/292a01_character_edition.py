"""Record which Cairn edition a character uses (#292)."""
from alembic import op
import sqlalchemy as sa

revision = '292a01'
down_revision = '296a02'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('characters') as batch_op:
        batch_op.add_column(sa.Column('edition', sa.String(length=16), nullable=False, server_default='2e'))


def downgrade():
    with op.batch_alter_table('characters') as batch_op:
        batch_op.drop_column('edition')

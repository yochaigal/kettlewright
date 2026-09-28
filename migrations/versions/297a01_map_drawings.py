"""Private map drawings and independently published snapshots."""
from alembic import op
import sqlalchemy as sa

revision = '297a01'
down_revision = '133a01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pointcrawl_maps', sa.Column('drawing', sa.JSON(), nullable=True))
    op.add_column('party_presentations', sa.Column('drawing', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('party_presentations') as batch:
        batch.drop_column('drawing')
    with op.batch_alter_table('pointcrawl_maps') as batch:
        batch.drop_column('drawing')

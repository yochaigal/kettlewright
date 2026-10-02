"""Persist manually shaped terrain and water on article drawings."""
from alembic import op
import sqlalchemy as sa

revision = '322a01'
down_revision = '321a01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('map_nodes', sa.Column('geometry', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('map_nodes') as batch:
        batch.drop_column('geometry')

"""Portraits for hirelings and pets."""
from alembic import op
import sqlalchemy as sa

revision = '295a01'
down_revision = '319a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('companions') as batch:
        batch.add_column(sa.Column('image_url', sa.String(512), nullable=True))
        batch.add_column(sa.Column('custom_image', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('companions') as batch:
        batch.drop_column('custom_image')
        batch.drop_column('image_url')

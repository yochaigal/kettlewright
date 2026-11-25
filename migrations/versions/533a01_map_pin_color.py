"""A party pin's colour (#533): one of a few, chosen when it is added. Existing pins keep the red they had."""
from alembic import op
import sqlalchemy as sa

revision = '533a01'
down_revision = '536a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('map_pins') as batch:
        batch.add_column(sa.Column('color', sa.String(16), nullable=True))


def downgrade():
    with op.batch_alter_table('map_pins') as batch:
        batch.drop_column('color')

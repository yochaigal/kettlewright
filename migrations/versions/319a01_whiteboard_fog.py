"""Independent fog and replacement generations for Whiteboard."""
from alembic import op
import sqlalchemy as sa

revision = '319a01'
down_revision = '298a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('party_maps') as batch:
        batch.add_column(sa.Column('generation', sa.Integer(), nullable=False, server_default='1'))
        batch.add_column(sa.Column('fog_version', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('fog', sa.JSON(), nullable=False,
            server_default='{"enabled": false, "base": "covered", "strokes": [], "applied": []}'))


def downgrade():
    with op.batch_alter_table('party_maps') as batch:
        batch.drop_column('fog')
        batch.drop_column('fog_version')
        batch.drop_column('generation')

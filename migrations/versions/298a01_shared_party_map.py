"""Live shared Excalidraw canvas per party."""
from alembic import op
import sqlalchemy as sa

revision = '298a01'
down_revision = '297a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('party_maps',
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('drawing', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table('party_maps')

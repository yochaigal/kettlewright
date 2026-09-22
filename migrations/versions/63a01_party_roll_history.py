"""Persist shared party roll history (#63)."""
from alembic import op
import sqlalchemy as sa

revision = '63a01'
down_revision = '49a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'party_rolls',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('character_name', sa.String(100), nullable=False),
        sa.Column('result', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_party_rolls_party_id_id', 'party_rolls', ['party_id', 'id'])


def downgrade():
    op.drop_table('party_rolls')

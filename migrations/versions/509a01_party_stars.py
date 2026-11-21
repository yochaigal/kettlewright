"""Starred parties (#476): a person's bookmarks, listed first on their Campaigns page."""
from alembic import op
import sqlalchemy as sa

revision = '509a01'
down_revision = '508a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'party_stars',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_party_stars_party_id', 'party_stars', ['party_id'])


def downgrade():
    op.drop_index('ix_party_stars_party_id', table_name='party_stars')
    op.drop_table('party_stars')

"""Stars (#476): a person's bookmarks (parties, modules, articles, maps, backgrounds), listed first
on their Campaigns page."""
from alembic import op
import sqlalchemy as sa

revision = '509a01'
down_revision = '508a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stars',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'kind', 'target_id', 'name', name='uq_star'),
    )
    op.create_index('ix_stars_user_id', 'stars', ['user_id'])


def downgrade():
    op.drop_index('ix_stars_user_id', table_name='stars')
    op.drop_table('stars')

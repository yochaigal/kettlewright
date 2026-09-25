"""Discord account links, channel bindings, selections and interaction receipts."""
from alembic import op
import sqlalchemy as sa

revision = '124a01'
down_revision = '115a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('discord_accounts',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('discord_id', sa.String(20), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100), nullable=False))
    op.create_table('discord_channels',
        sa.Column('guild_id', sa.String(20), primary_key=True),
        sa.Column('channel_id', sa.String(20), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('linked_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False))
    op.create_table('discord_selections',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('guild_id', sa.String(20), primary_key=True),
        sa.Column('channel_id', sa.String(20), primary_key=True),
        sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False))
    op.create_table('discord_interactions',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('discord_id', sa.String(20), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False))
    op.create_index('ix_discord_interactions_created_at', 'discord_interactions', ['created_at'])


def downgrade():
    for table in ('discord_interactions', 'discord_selections', 'discord_channels', 'discord_accounts'):
        op.drop_table(table)

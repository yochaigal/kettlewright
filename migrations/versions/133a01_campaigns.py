"""Campaign originals, party knowledge and pointcrawl maps (#133)."""
from alembic import op
import sqlalchemy as sa

revision = '133a01'
down_revision = '124a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
    )
    op.create_index('ix_campaigns_owner_id', 'campaigns', ['owner_id'])
    op.create_table('campaign_parties',
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('content_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('path_type', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
    )
    op.create_index('ix_content_entries_owner_id', 'content_entries', ['owner_id'])
    op.create_index('ix_content_entries_campaign_id', 'content_entries', ['campaign_id'])
    op.create_table('content_links',
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('party_presentations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('path_type', sa.String(20), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.UniqueConstraint('entry_id', 'party_id', name='uq_presentation_entry_party'),
    )
    op.create_index('ix_party_presentations_party_id', 'party_presentations', ['party_id'])
    op.create_table('pointcrawl_maps',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.UniqueConstraint('entry_id'),
    )
    op.create_table('map_nodes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('map_id', sa.Integer(), sa.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('nested_map_id', sa.Integer(), sa.ForeignKey('pointcrawl_maps.id', ondelete='SET NULL'), nullable=True),
        sa.UniqueConstraint('map_id', 'entry_id', name='uq_map_location'),
    )
    op.create_index('ix_map_nodes_map_id', 'map_nodes', ['map_id'])
    op.create_table('map_edges',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('map_id', sa.Integer(), sa.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('map_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('map_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('entry_id'),
    )
    op.create_index('ix_map_edges_map_id', 'map_edges', ['map_id'])


def downgrade():
    op.drop_table('map_edges')
    op.drop_table('map_nodes')
    op.drop_table('pointcrawl_maps')
    op.drop_table('party_presentations')
    op.drop_table('content_links')
    op.drop_table('content_entries')
    op.drop_table('campaign_parties')
    op.drop_table('campaigns')

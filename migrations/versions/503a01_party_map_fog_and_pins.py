"""Party maps: fog per party on a revealed map, and pins the party places on it.

A party's copy of a map (its party_presentations row for the map's article) keeps that
party's fog, like the whiteboard's. Pins are party notes with a position on a map.
"""
from alembic import op
import sqlalchemy as sa

revision = '503a01'
down_revision = '502a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('party_presentations') as batch:
        batch.add_column(sa.Column('fog', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('fog_version', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('map_pins',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('map_id', sa.Integer(), sa.ForeignKey('pointcrawl_maps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('content_entries.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_map_pins_map_party', 'map_pins', ['map_id', 'party_id'])


def downgrade():
    op.drop_index('ix_map_pins_map_party', 'map_pins')
    op.drop_table('map_pins')
    with op.batch_alter_table('party_presentations') as batch:
        batch.drop_column('fog_version')
        batch.drop_column('fog')

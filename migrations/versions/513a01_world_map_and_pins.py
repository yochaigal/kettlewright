"""Maps (#482, #488): a campaign's World Map, the size of pin labels, and pins revealed with their map.

pointcrawl_maps.world_map marks the campaign's World Map (one per campaign; none until the Warden picks one
or generates a setting). pointcrawl_maps.pin_size is how big pin labels are drawn. map_nodes.reveal: parties
shown the map are shown that pin too (off for existing pins, so nothing new is revealed)."""
from alembic import op
import sqlalchemy as sa

revision = '513a01'
down_revision = '512a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pointcrawl_maps') as batch:
        batch.add_column(sa.Column('world_map', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('pin_size', sa.String(10), nullable=False, server_default='medium'))
    with op.batch_alter_table('map_nodes') as batch:
        batch.add_column(sa.Column('reveal', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('map_nodes') as batch:
        batch.drop_column('reveal')
    with op.batch_alter_table('pointcrawl_maps') as batch:
        batch.drop_column('pin_size')
        batch.drop_column('world_map')

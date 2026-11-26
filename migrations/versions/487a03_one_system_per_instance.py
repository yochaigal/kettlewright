"""One game system per Kettlewright instance (#487): campaigns, parties and characters no longer keep one each.

The instance plays the system GAME_SYSTEM names (in .env; Cairn by default), so the game_system columns that
487a02 added are dropped. Every row so far played Cairn, the only system there was. Going back, they all play
Cairn again.
"""
from alembic import op
import sqlalchemy as sa

revision = '487a03'
down_revision = '537a01'
branch_labels = None
depends_on = None

TABLES = ('campaigns', 'parties', 'characters')


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_column('game_system')


def downgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('game_system', sa.String(32), nullable=False, server_default='cairn'))

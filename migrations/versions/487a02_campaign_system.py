"""The game system each campaign, party and character plays (#487): a game_system column, a kettlewright system's key.

It is set when the row is created and never changes after: a party starts with its campaign's system, a
character with its party's (or the default one). Every existing row plays Cairn ('cairn'), the only system
there is today. Companions play their party's or their owner's.
"""
from alembic import op
import sqlalchemy as sa

revision = '487a02'
down_revision = '487a01'
branch_labels = None
depends_on = None

TABLES = ('campaigns', 'parties', 'characters')


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('game_system', sa.String(32), nullable=False, server_default='cairn'))


def downgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_column('game_system')

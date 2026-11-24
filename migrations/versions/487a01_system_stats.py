"""Stats of other game systems (#487): characters.system_stats and companions.system_stats.

Kettlewright's stats come from its game system (kettlewright). Cairn's (HP, STR, DEX, WIL and their maximums) are
columns and stay where they are. A stat a system adds that has no column of its own is kept in this JSON
object, {"luck": 7, "luck_max": 9}. Existing characters and companions get an empty one: nothing moves.
"""
from alembic import op
import sqlalchemy as sa

revision = '487a01'
down_revision = '514a01'
branch_labels = None
depends_on = None


def upgrade():
    for table in ('characters', 'companions'):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('system_stats', sa.Text(), nullable=False, server_default='{}'))


def downgrade():
    for table in ('characters', 'companions'):
        with op.batch_alter_table(table) as batch:
            batch.drop_column('system_stats')

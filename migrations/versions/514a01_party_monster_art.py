"""Monster art per party: parties.monster_art is the art new bestiary monsters get.

'kettlewright' is Kettlewright's own tokens; 'oozejar' is Oozejar's Illustrated Bestiary, one token for
each Cairn bestiary monster, from the Cairn collection for Atlas VTT (CC BY-SA 4.0). Existing parties
keep Kettlewright's tokens, and monsters already in a party keep the portrait they have.
"""
from alembic import op
import sqlalchemy as sa

revision = '514a01'
down_revision = '513a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('parties') as batch:
        batch.add_column(sa.Column('monster_art', sa.String(20), nullable=False, server_default='kettlewright'))


def downgrade():
    with op.batch_alter_table('parties') as batch:
        batch.drop_column('monster_art')

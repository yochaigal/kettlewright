"""Party monsters reuse companion sheets and keep private and public notes separate."""
from alembic import op
import sqlalchemy as sa

revision = '296a01'
down_revision = '310a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('companions') as batch:
        batch.drop_constraint('companion_parent', type_='check')
        batch.create_check_constraint('companion_parent',
            "(kind IN ('hireling', 'monster') AND party_id IS NOT NULL AND character_id IS NULL AND hireling_id IS NULL) OR "
            "(kind = 'pet' AND party_id IS NULL AND ((character_id IS NOT NULL AND hireling_id IS NULL) OR "
            "(character_id IS NULL AND hireling_id IS NOT NULL)))")
        batch.add_column(sa.Column('public_notes', sa.Text(), nullable=False, server_default=''))
        batch.add_column(sa.Column('in_combat', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # A rollback must not silently delete live monsters or their equipment.
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM companions WHERE kind = 'monster'")).scalar():
        raise RuntimeError('Transfer or delete party monsters before downgrading.')
    with op.batch_alter_table('companions') as batch:
        batch.drop_column('in_combat')
        batch.drop_column('public_notes')
        batch.drop_constraint('companion_parent', type_='check')
        batch.create_check_constraint('companion_parent',
            "(kind = 'hireling' AND party_id IS NOT NULL AND character_id IS NULL AND hireling_id IS NULL) OR "
            "(kind = 'pet' AND party_id IS NULL AND ((character_id IS NOT NULL AND hireling_id IS NULL) OR "
            "(character_id IS NULL AND hireling_id IS NOT NULL)))")

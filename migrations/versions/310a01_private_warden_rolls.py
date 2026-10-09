"""Keep Warden rolls private to their roller."""
from alembic import op
import sqlalchemy as sa

revision = '310a01'
down_revision = '336a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('party_rolls') as batch:
        batch.add_column(sa.Column('private_user_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_party_rolls_private_user', 'users', ['private_user_id'], ['id'], ondelete='CASCADE')


def downgrade():
    with op.batch_alter_table('party_rolls') as batch:
        batch.drop_constraint('fk_party_rolls_private_user', type_='foreignkey')
        batch.drop_column('private_user_id')

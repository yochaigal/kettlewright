from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4306e31dbfaf'
down_revision = 'fe1d96bff89f'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('characters', schema=None) as batch_op:
        batch_op.add_column(sa.Column('party_code', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('party_id', sa.Integer(), nullable=True))
        # Specify a name for the foreign key constraint
        batch_op.create_foreign_key('fk_party_id', 'parties', ['party_id'], ['id'])


def downgrade():
    with op.batch_alter_table('characters', schema=None) as batch_op:
        batch_op.drop_constraint('fk_party_id', type_='foreignkey')
        batch_op.drop_column('party_id')
        batch_op.drop_column('party_code')

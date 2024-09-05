"""add party_code and party_id to character model

Revision ID: 4306e31dbfaf
Revises: fe1d96bff89f
Create Date: 2024-02-19 11:22:48.714483

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '4306e31dbfaf'
down_revision = 'fe1d96bff89f'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()

    with op.batch_alter_table('characters') as batch_op:
        if not conn.execute(text("SELECT * FROM pragma_table_info('characters') WHERE name='party_code'")).fetchone():
            batch_op.add_column(sa.Column('party_code', sa.String(length=64), nullable=True))
        if not conn.execute(text("SELECT * FROM pragma_table_info('characters') WHERE name='party_id'")).fetchone():
            batch_op.add_column(sa.Column('party_id', sa.Integer(), nullable=True))
            # Add an explicit name for the foreign key constraint
            batch_op.create_foreign_key('fk_party_id', 'parties', ['party_id'], ['id'])

def downgrade():
    with op.batch_alter_table('characters') as batch_op:
        batch_op.drop_constraint('fk_party_id', type_='foreignkey')
        batch_op.drop_column('party_id')
        batch_op.drop_column('party_code')


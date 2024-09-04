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
    # Wrap the SQL string with text() for it to be executable
    if not conn.execute(text("SELECT * FROM pragma_table_info('characters') WHERE name='party_code'")).fetchone():
        op.add_column('characters', sa.Column('party_code', sa.String(length=64), nullable=True))
    if not conn.execute(text("SELECT * FROM pragma_table_info('characters') WHERE name='party_id'")).fetchone():
        op.add_column('characters', sa.Column('party_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'characters', 'parties', ['party_id'], ['id'])

def downgrade():
    op.drop_column('characters', 'party_id')
    op.drop_column('characters', 'party_code')

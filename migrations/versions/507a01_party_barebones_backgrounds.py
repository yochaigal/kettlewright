"""Barebones backgrounds per party: whether its Barebones characters may roll on the official d100 table.

Like official_backgrounds (Second Edition): the campaign's module backgrounds are offered in Barebones too.
Existing parties keep the official table.
"""
from alembic import op
import sqlalchemy as sa

revision = '507a01'
down_revision = '506a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('parties') as batch:
        batch.add_column(sa.Column('official_barebones', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('parties') as batch:
        batch.drop_column('official_barebones')

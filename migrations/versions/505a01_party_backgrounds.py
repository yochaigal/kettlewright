"""Backgrounds are set per party: whether its characters may also choose the official ones.

The campaign's setting becomes each of its parties' setting. The modules' own backgrounds
are offered to every party of the campaign, as before.
"""
from alembic import op
import sqlalchemy as sa

revision = '505a01'
down_revision = '504a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('parties') as batch:
        batch.add_column(sa.Column('official_backgrounds', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute('UPDATE parties SET official_backgrounds = (SELECT c.official_backgrounds FROM campaigns c '
               'WHERE c.id = parties.campaign_id) WHERE campaign_id IS NOT NULL')
    with op.batch_alter_table('campaigns') as batch:
        batch.drop_column('official_backgrounds')


def downgrade():
    with op.batch_alter_table('campaigns') as batch:
        batch.add_column(sa.Column('official_backgrounds', sa.Boolean(), nullable=False, server_default=sa.true()))
    # A campaign hides them again only if all its parties did.
    op.execute('UPDATE campaigns SET official_backgrounds = false WHERE EXISTS (SELECT 1 FROM parties p '
               'WHERE p.campaign_id = campaigns.id) AND NOT EXISTS (SELECT 1 FROM parties p '
               'WHERE p.campaign_id = campaigns.id AND p.official_backgrounds)')
    with op.batch_alter_table('parties') as batch:
        batch.drop_column('official_backgrounds')

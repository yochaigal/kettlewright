"""Images (#476): an article, a campaign and a party can each have one picture of its own.

An article's shows above its text and on its card; a campaign's is its cover; a party's shows on its
page and is its wiki's cover. Empty for existing rows: covers keep coming from the articles' pictures.
"""
from alembic import op
import sqlalchemy as sa

revision = '508a01'
down_revision = '507a01'
branch_labels = None
depends_on = None

TABLES = ('content_entries', 'campaigns', 'parties')


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('image', sa.String(length=2000), nullable=False, server_default=''))


def downgrade():
    for table in reversed(TABLES):
        with op.batch_alter_table(table) as batch:
            batch.drop_column('image')

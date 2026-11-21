"""An article's image (#476): one picture of its own, shown above its text and on its card.

Empty for existing articles: their cards keep showing the first picture in their text.
"""
from alembic import op
import sqlalchemy as sa

revision = '508a01'
down_revision = '507a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.add_column(sa.Column('image', sa.String(length=2000), nullable=False, server_default=''))


def downgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_column('image')

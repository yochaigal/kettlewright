"""Store background table answers separately from player notes; no backfill."""
from alembic import op
import sqlalchemy as sa

revision = '103a01'
down_revision = '102a01'
branch_labels = None
depends_on = None

FIELDS = ('background_table1_question', 'background_table1_answer',
          'background_table2_question', 'background_table2_answer')


def upgrade():
    with op.batch_alter_table('characters') as batch:
        for field in FIELDS:
            batch.add_column(sa.Column(field, sa.String(2000), nullable=True))


def downgrade():
    with op.batch_alter_table('characters') as batch:
        for field in reversed(FIELDS):
            batch.drop_column(field)

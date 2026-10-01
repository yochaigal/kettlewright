"""Article hierarchy and owner-bound archive import previews."""
from alembic import op
import sqlalchemy as sa

revision = '318a01'
down_revision = '319a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('content_entries') as batch:
        batch.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_content_parent', 'content_entries', ['parent_id'], ['id'], ondelete='SET NULL')
        batch.create_index('ix_content_entries_parent_id', ['parent_id'])
    op.create_table('campaign_imports',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('consumed', sa.Boolean(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False))
    op.create_index('ix_campaign_imports_owner_id', 'campaign_imports', ['owner_id'])


def downgrade():
    op.drop_table('campaign_imports')
    with op.batch_alter_table('content_entries') as batch:
        batch.drop_index('ix_content_entries_parent_id')
        batch.drop_constraint('fk_content_parent', type_='foreignkey')
        batch.drop_column('parent_id')

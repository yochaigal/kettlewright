"""Optional email MFA and expiring server-side challenges."""
from alembic import op
import sqlalchemy as sa

revision = '115a01'
down_revision = '103a01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table('mfa_challenges',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('nonce', sa.String(64), nullable=False, unique=True),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('binding', sa.String(64), nullable=False),
        sa.Column('purpose', sa.String(10), nullable=False),
        sa.Column('expires', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.Integer(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('mfa_challenges')
    with op.batch_alter_table('users') as batch:
        batch.drop_column('mfa_enabled')

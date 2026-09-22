"""Separate pets and hirelings with small sheets and inventories."""
from alembic import op
import sqlalchemy as sa

revision = '102a01'
down_revision = '63a01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('companions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(10), nullable=False),
        sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE')),
        sa.Column('party_id', sa.Integer(), sa.ForeignKey('parties.id', ondelete='CASCADE')),
        sa.Column('hireling_id', sa.Integer(), sa.ForeignKey('companions.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        *[sa.Column(field, sa.Integer()) for field in ('hp', 'hp_max', 'strength', 'strength_max', 'dexterity', 'dexterity_max', 'willpower', 'willpower_max')],
        sa.Column('armor', sa.Integer(), nullable=False),
        sa.Column('attack', sa.String(200), nullable=False),
        sa.Column('daily_cost', sa.Integer(), nullable=False),
        sa.Column('gold', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('items', sa.Text(), nullable=False),
        sa.Column('containers', sa.Text(), nullable=False),
        sa.Column('shared', sa.Boolean(), nullable=False),
        sa.CheckConstraint("(kind = 'hireling' AND party_id IS NOT NULL AND character_id IS NULL AND hireling_id IS NULL) OR (kind = 'pet' AND party_id IS NULL AND ((character_id IS NOT NULL AND hireling_id IS NULL) OR (character_id IS NULL AND hireling_id IS NOT NULL)))", name='companion_parent'),
    )
    for field in ('character_id', 'party_id', 'hireling_id'):
        op.create_index('ix_companions_' + field, 'companions', [field])


def downgrade():
    op.drop_table('companions')

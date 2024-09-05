"""change column name to user_name.

Revision ID: 038683fc4a59
Revises: 752dc475b25b
Create Date: 2023-08-26 12:32:15.725369

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '038683fc4a59'
down_revision = '752dc475b25b'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'name', new_column_name='user_name')

def downgrade():
    op.alter_column('users', 'user_name', new_column_name='name')
"""chanage user_name to username

Revision ID: a086d904d7cd
Revises: 038683fc4a59
Create Date: 2023-08-26 15:17:33.062103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a086d904d7cd'
down_revision = '038683fc4a59'
branch_labels = None
depends_on = None



def upgrade():
    op.alter_column('users', 'user_name', new_column_name='username')

def downgrade():
    op.alter_column('users', 'username', new_column_name='user_name')

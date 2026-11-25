"""A party's storage is its Stash (#540), not 'Main' like every character's main inventory.

Transferring items listed 'Main' for the party, the character and each hireling. A party's own container (id 0)
still named 'Main' becomes 'Stash'; one a Warden renamed keeps its name.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = '540a01'
down_revision = '487a02'
branch_labels = None
depends_on = None

parties = sa.table('parties', sa.column('id', sa.Integer), sa.column('containers', sa.Text))


def rename(old, new):
    connection = op.get_bind()
    for party_id, text in connection.execute(sa.select(parties.c.id, parties.c.containers)).all():
        try:
            containers = json.loads(text or '[]')
        except ValueError:
            continue
        changed = False
        for container in containers if isinstance(containers, list) else []:
            if isinstance(container, dict) and container.get('id') == 0 and container.get('name') == old:
                container['name'] = new
                changed = True
        if changed:
            connection.execute(parties.update().where(parties.c.id == party_id)
                               .values(containers=json.dumps(containers)))


def upgrade():
    rename('Main', 'Stash')


def downgrade():
    rename('Stash', 'Main')

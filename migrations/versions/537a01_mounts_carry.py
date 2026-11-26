"""Mounts carry for their owner (#537). An Outrider's background mount came twice: a pet with its own slots and a
container of its name in the character's inventory, unrelated. Each such pet (slots, nothing of its own) is linked to
that container ({'mount': pet id}) and keeps no inventory of its own, as app/lib/mounts.py does for new ones.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = '537a01'
down_revision = '533a01'
branch_labels = None
depends_on = None

companions = sa.table('companions', sa.column('id', sa.Integer), sa.column('kind', sa.String),
                      sa.column('name', sa.String), sa.column('character_id', sa.Integer), sa.column('hireling_id', sa.Integer),
                      sa.column('items', sa.Text), sa.column('containers', sa.Text))
characters = sa.table('characters', sa.column('id', sa.Integer), sa.column('containers', sa.Text))


def _list(text):
    try:
        value = json.loads(text or '[]')
    except ValueError:
        return []
    return value if isinstance(value, list) else []


def _main_slots(containers):
    return next((int(c.get('slots') or 0) for c in containers if isinstance(c, dict) and c.get('id') == 0), 0)


def _owners(connection):
    """(table, id) -> containers, for every pet owner."""
    rows = {('characters', i): t for i, t in connection.execute(sa.select(characters.c.id, characters.c.containers))}
    rows.update({('companions', i): t for i, t in connection.execute(
        sa.select(companions.c.id, companions.c.containers).where(companions.c.kind == 'hireling'))})
    return rows


def upgrade():
    connection = op.get_bind()
    owners = _owners(connection)
    pets = connection.execute(sa.select(companions).where(companions.c.kind == 'pet')).all()
    changed_owners = {}
    for pet in pets:
        key = ('characters', pet.character_id) if pet.character_id else ('companions', pet.hireling_id)
        if key not in owners or _list(pet.items):
            continue
        own = _list(pet.containers)
        if _main_slots(own) <= 0:
            continue
        containers = changed_owners.get(key) or _list(owners[key])
        if any(isinstance(c, dict) and c.get('mount') == pet.id for c in containers):
            continue
        match = next((c for c in containers if isinstance(c, dict) and c.get('name') == pet.name and c.get('id') != 0
                      and c.get('mount') is None and not c.get('carried_by') and not c.get('on_the_ground')), None)
        if match is None:
            continue
        match['mount'] = pet.id
        changed_owners[key] = containers
        for c in own:
            if isinstance(c, dict) and c.get('id') == 0:
                c['slots'] = 0
        connection.execute(companions.update().where(companions.c.id == pet.id).values(containers=json.dumps(own)))
    for (table, owner_id), containers in changed_owners.items():
        target = characters if table == 'characters' else companions
        connection.execute(target.update().where(target.c.id == owner_id).values(containers=json.dumps(containers)))


def downgrade():
    connection = op.get_bind()
    for (table, owner_id), text in _owners(connection).items():
        containers = _list(text)
        linked = [c for c in containers if isinstance(c, dict) and c.get('mount') is not None]
        for c in linked:
            pet_id = c.pop('mount')
            row = connection.execute(sa.select(companions.c.containers).where(companions.c.id == pet_id)).first()
            if row is not None:
                own = _list(row[0]) or [{'id': 0, 'name': 'Main', 'slots': 0}]
                for o in own:
                    if isinstance(o, dict) and o.get('id') == 0:
                        o['slots'] = int(c.get('slots') or 0)
                connection.execute(companions.update().where(companions.c.id == pet_id).values(containers=json.dumps(own)))
        if linked:
            target = characters if table == 'characters' else companions
            connection.execute(target.update().where(target.c.id == owner_id).values(containers=json.dumps(containers)))

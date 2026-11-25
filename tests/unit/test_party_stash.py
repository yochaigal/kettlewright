"""#540: a party's storage is its Stash, not 'Main' like every character's main inventory."""
import importlib.util
import json

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def migration():
    spec = importlib.util.spec_from_file_location('m540', 'migrations/versions/540a01_party_stash.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_new_party_s_storage_is_its_stash(app):
    from app.lib.campaign_parties import create_campaign
    from app.models import User, db
    with app.app_context():
        db.session.add(User(id=1, username='warden'))
        db.session.commit()
        party = create_campaign(1, 'Old Roads').parties[0]
        assert json.loads(party.containers) == [{'name': 'Stash', 'slots': 10, 'id': 0}]


def test_existing_parties_storage_becomes_the_stash_unless_renamed():
    rows = {1: [{'id': 0, 'name': 'Main', 'slots': 10}, {'id': 1, 'name': 'Main', 'slots': 4}],
            2: [{'id': 0, 'name': 'Vault', 'slots': 10}], 3: 'not json', 4: None}
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.exec_driver_sql('create table parties (id integer primary key, containers text)')
        for party_id, containers in rows.items():
            connection.exec_driver_sql('insert into parties values (?, ?)', (
                party_id, containers if containers is None or isinstance(containers, str) else json.dumps(containers)))
        stored = lambda: {i: c for i, c in connection.exec_driver_sql('select id, containers from parties').all()}
        with Operations.context(MigrationContext.configure(connection)):
            migration().upgrade()
            after = stored()
            # Only the party's own container (id 0) still named Main: not one a Warden renamed, nor another 'Main'.
            assert json.loads(after[1]) == [{'id': 0, 'name': 'Stash', 'slots': 10}, {'id': 1, 'name': 'Main', 'slots': 4}]
            assert json.loads(after[2]) == rows[2] and after[3] == 'not json' and after[4] is None
            migration().downgrade()
            assert json.loads(stored()[1]) == rows[1]

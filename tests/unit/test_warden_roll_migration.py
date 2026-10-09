import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def test_private_roll_migration_preserves_shared_history():
    path = Path('migrations/versions/310a01_private_warden_rolls.py')
    spec = importlib.util.spec_from_file_location('warden_roll_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY)'))
        connection.execute(text('CREATE TABLE parties (id INTEGER PRIMARY KEY)'))
        connection.execute(text('CREATE TABLE party_rolls (id INTEGER PRIMARY KEY, party_id INTEGER NOT NULL, character_name TEXT NOT NULL, result TEXT NOT NULL, created_at DATETIME NOT NULL)'))
        connection.execute(text("INSERT INTO party_rolls VALUES (1, 1, 'Bran', '6 (d6)', '2026-10-09')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        row = connection.execute(text('SELECT * FROM party_rolls')).mappings().one()
        assert row['result'] == '6 (d6)'
        assert row['private_user_id'] is None
        assert inspect(connection).get_foreign_keys('party_rolls')[0]['referred_table'] == 'users'
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(text('SELECT * FROM party_rolls')).one() == (1, 1, 'Bran', '6 (d6)', '2026-10-09')

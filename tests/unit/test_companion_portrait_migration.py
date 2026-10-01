import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def test_portrait_migration_preserves_existing_companions():
    path = Path('migrations/versions/295a01_companion_portraits.py')
    spec = importlib.util.spec_from_file_location('companion_portrait_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE companions (id INTEGER PRIMARY KEY, name TEXT NOT NULL)'))
        connection.execute(text("INSERT INTO companions VALUES (1, 'Moss')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        row = connection.execute(text('SELECT * FROM companions')).mappings().one()
        assert row['name'] == 'Moss'
        assert row['image_url'] is None
        assert row['custom_image'] == 0
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(text('SELECT * FROM companions')).one() == (1, 'Moss')

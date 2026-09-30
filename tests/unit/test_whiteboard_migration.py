import importlib.util
import json
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def test_migration_preserves_existing_drawing_and_downgrades_cleanly():
    path = Path('migrations/versions/319a01_whiteboard_fog.py')
    spec = importlib.util.spec_from_file_location('whiteboard_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    drawing = '{"elements":[{"id":"original"}],"files":{}}'
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE party_maps (party_id INTEGER PRIMARY KEY, drawing JSON NOT NULL, version INTEGER NOT NULL)'))
        connection.execute(text('INSERT INTO party_maps VALUES (1, :drawing, 7)'), {'drawing': drawing})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        row = connection.execute(text('SELECT * FROM party_maps')).mappings().one()
        assert row['drawing'] == drawing and row['version'] == 7
        assert row['generation'] == 1 and row['fog_version'] == 0
        assert json.loads(row['fog']) == {'enabled': False, 'base': 'covered', 'strokes': [], 'applied': []}
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(text('SELECT * FROM party_maps')).one() == (1, drawing, 7)

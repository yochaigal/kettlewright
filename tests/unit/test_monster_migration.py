import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def test_monster_migration_retains_existing_rows_and_guards_downgrade():
    path = Path('migrations/versions/296a01_party_monsters.py')
    spec = importlib.util.spec_from_file_location('monster_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE companions (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, party_id INTEGER, character_id INTEGER, hireling_id INTEGER, name TEXT, CONSTRAINT companion_parent CHECK ((kind = 'hireling' AND party_id IS NOT NULL AND character_id IS NULL AND hireling_id IS NULL) OR (kind = 'pet' AND party_id IS NULL AND ((character_id IS NOT NULL AND hireling_id IS NULL) OR (character_id IS NULL AND hireling_id IS NOT NULL)))))"))
        connection.execute(text("INSERT INTO companions VALUES (1,'hireling',1,NULL,NULL,'Ada')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        row = connection.execute(text('SELECT * FROM companions')).mappings().one()
        assert row['name'] == 'Ada' and row['public_notes'] == '' and row['in_combat'] == 0
        connection.execute(text("INSERT INTO companions (id,kind,party_id,name) VALUES (2,'monster',1,'Wolf')"))
        with Operations.context(MigrationContext.configure(connection)):
            with pytest.raises(RuntimeError):
                migration.downgrade()
        connection.execute(text('DELETE FROM companions WHERE id=2'))
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(text('SELECT * FROM companions')).one() == (1, 'hireling', 1, None, None, 'Ada')


def test_remove_combat_state_preserves_monsters_and_visibility():
    path = Path('migrations/versions/296a02_remove_monster_combat_state.py')
    spec = importlib.util.spec_from_file_location('remove_combat_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE companions (id INTEGER PRIMARY KEY, name TEXT, hp INTEGER, shared BOOLEAN, public_notes TEXT, in_combat BOOLEAN)'))
        connection.execute(text("INSERT INTO companions VALUES (1,'Wolf',3,1,'Public note',1)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text('SELECT * FROM companions')).one() == (1, 'Wolf', 3, 1, 'Public note')
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.execute(text('SELECT * FROM companions')).one() == (1, 'Wolf', 3, 1, 'Public note', 0)

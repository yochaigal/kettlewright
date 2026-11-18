"""430a01: blank originals of party-made notes get their party version's text."""
import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def test_blank_party_originals_get_their_party_text():
    spec = importlib.util.spec_from_file_location('note_migration', Path('migrations/versions/430a01_fill_party_note_originals.py'))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE content_entries (id INTEGER PRIMARY KEY, title VARCHAR(200) NOT NULL DEFAULT '', "
                                "body TEXT NOT NULL DEFAULT '')"))
        connection.execute(text('CREATE TABLE party_presentations (id INTEGER PRIMARY KEY, entry_id INTEGER, party_id INTEGER, '
                                'title VARCHAR(200), body TEXT)'))
        connection.execute(text("INSERT INTO content_entries VALUES (1, '', ''), (2, 'Private', 'Secret'), (3, '', ''), (4, '', '')"))
        connection.execute(text("INSERT INTO party_presentations VALUES "
                                "(1, 1, 2, 'Rumour', 'Heard in play'), "  # Quick note: blank original, one party.
                                "(2, 2, 1, 'Public', 'Told'), "           # A written original stays as it is.
                                "(3, 3, 1, 'A', 'a'), (4, 3, 2, 'B', 'b')"))  # Several versions: no single source.
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(text('SELECT * FROM content_entries ORDER BY id')).all()
        assert rows == [(1, 'Rumour', 'Heard in play'), (2, 'Private', 'Secret'), (3, '', ''), (4, '', '')]

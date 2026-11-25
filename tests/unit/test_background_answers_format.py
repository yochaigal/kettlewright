"""#536: background table answers carry the Cairn SRD's formatting: items in bold, mechanics in italics."""
import importlib.util
import json
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

BACKGROUNDS = Path('systems/cairn/content/backgrounds')


def migration():
    spec = importlib.util.spec_from_file_location('m536', 'migrations/versions/536a01_formatted_background_answers.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def answers():
    for path in sorted(BACKGROUNDS.glob('*.json')):
        if path.name != 'background_data.json':
            background = next(iter(json.loads(path.read_text()).values()))
            for table in ('table1', 'table2'):
                yield from background.get(table, {}).get('options', [])


def test_answers_name_their_items_in_bold_and_mechanics_in_italics():
    options = list(answers())
    snuff = next(o['description'] for o in options if o['description'].startswith('There was an explosion'))
    assert '**Tin of Snuff**' in snuff and snuff.endswith('become _deprived_.')
    assert sum('**' in o['description'] for o in options) >= 200
    # Balanced marks, so the Markdown renders.
    assert all(o['description'].count('**') % 2 == 0 for o in options)


def test_the_answer_shows_its_formatting_on_the_sheet(app_with_babel):
    app = app_with_babel
    from flask import render_template
    from types import SimpleNamespace
    with app.test_request_context():
        character = SimpleNamespace(background_table1_question='What went horribly wrong?',
                                    background_table1_answer='Take a **Tin of Snuff** or become _deprived_.',
                                    background_table2_question='', background_table2_answer='')
        html = render_template('partial/character_background_answers.html', character=character)
    assert '<strong>Tin of Snuff</strong>' in html and '<em>deprived</em>' in html


def test_existing_characters_answers_get_the_formatting_in_their_language():
    from babel.messages.pofile import read_po
    m = migration()
    english = next(o['description'] for o in answers() if o['description'].startswith('There was an explosion'))
    with open('app/translations/es/LC_MESSAGES/messages.po', 'rb') as file:
        spanish = read_po(file).get(english).string
    assert '**' in spanish  # The translation carries the formatting too.
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.exec_driver_sql('create table characters (id integer primary key, '
                                   'background_table1_answer text, background_table2_answer text)')
        rows = [(1, m.plain(english), 'My own answer'), (2, m.plain(spanish), None), (3, english, '')]
        connection.exec_driver_sql('insert into characters values (?, ?, ?)', rows[0])
        connection.exec_driver_sql('insert into characters values (?, ?, ?)', rows[1])
        connection.exec_driver_sql('insert into characters values (?, ?, ?)', rows[2])
        stored = lambda: connection.exec_driver_sql('select * from characters order by id').all()
        with Operations.context(MigrationContext.configure(connection)):
            m.upgrade()
            assert stored() == [(1, english, 'My own answer'), (2, spanish, None), (3, english, '')]
            m.downgrade()
            assert stored() == [(1, m.plain(english), 'My own answer'), (2, m.plain(spanish), None),
                                (3, m.plain(english), '')]

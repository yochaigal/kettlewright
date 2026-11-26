"""Background table answers with the Cairn SRD's formatting (#536): items in bold, mechanics in italics.

The tables' answers gained their Markdown (system/cairn/content/backgrounds, and their translations); a character
keeps the answer it was created with, so one whose answer is a table answer without that formatting, in any
language, gets the formatted one. The formatting only added marks, so the answer without them is the old one.
"""
import json
import re
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = '536a01'
down_revision = '540a01'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]
characters = sa.table('characters', sa.column('id', sa.Integer),
                      sa.column('background_table1_answer', sa.Text), sa.column('background_table2_answer', sa.Text))


def plain(text):
    return re.sub(r'(?<![\w*])_(.+?)_(?![\w*])', r'\1', text.replace('**', ''))


def formatted_answers():
    """Every table answer that has formatting, in English and in each translation."""
    answers = set()
    for path in (ROOT / 'system/cairn/content/backgrounds').glob('*.json'):
        if path.name == 'background_data.json':
            continue
        background = next(iter(json.loads(path.read_text()).values()))
        for table in ('table1', 'table2'):
            answers.update(option['description'] for option in background.get(table, {}).get('options', []))
    try:
        from babel.messages.pofile import read_po
    except ImportError:
        read_po = None
    if read_po:
        english = set(answers)
        for po in (ROOT / 'app/translations').glob('*/LC_MESSAGES/messages.po'):
            with po.open('rb') as file:
                answers.update(m.string for m in read_po(file) if m.id in english and isinstance(m.string, str) and m.string)
    return {answer for answer in answers if plain(answer) != answer}


def replace(mapping):
    connection = op.get_bind()
    for row in connection.execute(sa.select(characters)).all():
        values = {field: mapping[getattr(row, field)] for field in ('background_table1_answer', 'background_table2_answer')
                  if getattr(row, field) in mapping}
        if values:
            connection.execute(characters.update().where(characters.c.id == row.id).values(**values))


def upgrade():
    replace({plain(answer): answer for answer in formatted_answers()})


def downgrade():
    replace({answer: plain(answer) for answer in formatted_answers()})

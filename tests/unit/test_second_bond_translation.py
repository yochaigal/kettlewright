import json

from flask_babel import force_locale

from app.lib.char_utils import translate_paragraphs


def _bonds():
    with open('app/static/json/bonds.json') as f:
        return json.load(f)['Bonds']


def test_two_bonds_are_translated_one_by_one(app_with_babel):
    # #given: a Fieldwarden's two bonds, joined as the creation form sends them.
    first, second = _bonds()[0]['description'], _bonds()[1]['description']
    text = first + '\n\n' + second
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        saved = translate_paragraphs(text)
    # #then
    parts = saved.split('\n\n')
    assert len(parts) == 2
    assert parts[0].startswith('Heredaste una gema única')
    assert parts[1].startswith('Un primo lejano te dejó')


def test_single_bond_and_empty_text(app_with_babel):
    # #given
    only = _bonds()[0]['description']
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when / #then
        assert translate_paragraphs(only).startswith('Heredaste una gema única')
        assert translate_paragraphs('') == ''
        assert translate_paragraphs(None) == ''

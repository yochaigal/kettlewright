import json

import pytest
from flask_babel import force_locale

from app.lib.character_markdown import parse_character, render_character
from app.models import Character, Companion, User, db

ITEMS = [
    {'id': 'a', 'name': 'Shield', 'tags': ['1 Armor', 'bulky'], 'location': 0},
    {'id': 'b', 'name': 'Torch', 'tags': ['uses'], 'uses': 2, 'max_uses': 3, 'location': 0},
    {'id': 'c', 'name': 'Wand of Sparks', 'tags': ['charges'], 'charges': 1, 'max_charges': 4, 'location': 1,
     'description': 'Sets small things on fire.'},
    {'id': 'd', 'name': 'Rope (50ft)', 'tags': [], 'location': 1},
    {'id': 'e', 'name': 'Dagger', 'tags': ['d6'], 'location': 0},
]
CONTAINERS = [{'id': 0, 'name': 'Main', 'slots': 10}, {'id': 1, 'name': 'Satchel', 'slots': 4}]


def make_character(owner_id, **overrides):
    fields = dict(name='Ada Vell', background='Custom', url_name='ada-vell', owner=owner_id,
        strength=8, strength_max=12, dexterity=14, dexterity_max=14, willpower=9, willpower_max=11,
        hp=2, hp_max=5, gold=17, deprived=True, panicked=False, dead=False, custom_image=False, image_url='',
        description='Tall and *quiet*.', traits='Patient.', bonds='Owes a debt.', omens='A crow follows.',
        scars='Lost a finger.', notes='Line one\n\nLine two', edition='2e',
        background_table1_question='Who taught you?', background_table1_answer='My aunt.',
        background_table2_question='What did you steal?', background_table2_answer='A bell.',
        items=json.dumps(ITEMS), containers=json.dumps(CONTAINERS))
    fields.update(overrides)
    return Character(**fields)


@pytest.fixture
def owner(app_with_babel):
    # Don't keep the app context open: Flask-Login caches the user on it.
    with app_with_babel.app_context():
        user = User(username='md-user')
        db.session.add(user)
        db.session.commit()
        return user.id


def comparable(data):
    keys = ('name', 'background', 'edition', 'strength', 'strength_max', 'dexterity', 'dexterity_max',
            'willpower', 'willpower_max', 'hp', 'hp_max', 'gold', 'deprived', 'panicked', 'dead',
            'description', 'traits', 'bonds', 'omens', 'scars', 'notes',
            'background_table1_question', 'background_table1_answer',
            'background_table2_question', 'background_table2_answer', 'containers')
    result = {key: data[key] for key in keys}
    # Items come back grouped by container, so compare them in that order.
    items = [{k: v for k, v in item.items() if k != 'id'} for item in data['items']]
    result['items'] = sorted(items, key=lambda item: (item['location'], item['name']))
    return result


def test_markdown_round_trip(app_with_babel, owner):
    with app_with_babel.test_request_context():
        character = make_character(owner)
        character.pets.append(Companion(kind='pet', name='Pip', role='Dog', hp=3, hp_max=3, strength=8,
            strength_max=8, dexterity=12, dexterity_max=12, armor=1, attack='d6 bite', notes='Good boy.',
            items=json.dumps([{'id': 'x', 'name': 'Collar', 'tags': ['petty'], 'location': 0}])))
        db.session.add(character)
        db.session.commit()
        data = character.export_data()
        markdown = render_character(data)
        parsed = parse_character(markdown)
    assert markdown.startswith('# Ada Vell\n')
    assert '- Rope (50ft)' in markdown
    assert comparable(parsed) == comparable(data)
    pet = parsed['pets'][0]
    assert (pet['name'], pet['role'], pet['attack'], pet['notes'], pet['armor']) == ('Pip', 'Dog', 'd6 bite', 'Good boy.', 1)
    assert (pet['hp'], pet['strength'], pet['willpower'], pet['willpower_max']) == (3, 8, None, None)
    assert pet['items'][0]['name'] == 'Collar' and pet['items'][0]['tags'] == ['petty']


def test_barebones_edition_and_conditions_round_trip(app_with_babel, owner):
    with app_with_babel.test_request_context():
        data = make_character(owner, edition='barebones', background='Fighter', dead=True, deprived=False).export_data()
        markdown = render_character(data)
        parsed = parse_character(markdown)
    assert '**Background:** Fighter (Barebones)' in markdown
    assert '**Conditions:** Dead' in markdown
    assert parsed['edition'] == 'barebones' and parsed['background'] == 'Fighter'
    assert parsed['dead'] is True and parsed['deprived'] is False


def test_plain_text_has_no_markdown_markup(app_with_babel, owner):
    with app_with_babel.test_request_context():
        text = render_character(make_character(owner).export_data(), markdown=False)
    assert text.startswith('Ada Vell\n========')
    assert 'Background: Custom' in text
    assert 'STR 8/12 · DEX 14/14 · WIL 9/11 · HP 2/5 · Armor 1 · Gold 17' in text
    assert '**' not in text and '\n#' not in text
    assert 'Satchel (4 slots):' in text


def test_hand_written_markdown(app_with_babel):
    markdown = '# Wren\n\nA wandering cartographer.\n\nSTR 10 · DEX 12/13 · HP 4/4\n\n## Inventory\n\n- Map case (petty)\n- Mystery box (sealed)\n'
    with app_with_babel.test_request_context():
        parsed = parse_character(markdown)
    assert parsed['name'] == 'Wren'
    assert (parsed['strength'], parsed['strength_max'], parsed['dexterity'], parsed['dexterity_max']) == (10, 10, 12, 13)
    assert parsed['notes'] == 'A wandering cartographer.'  # Unrecognized lines are kept, not dropped.
    assert parsed['containers'] == [{'id': 0, 'name': 'Main', 'slots': 10}]
    assert [(item['name'], item['tags']) for item in parsed['items']] == [('Map case', ['petty']), ('Mystery box (sealed)', [])]


def test_markdown_without_name_is_rejected(app_with_babel):
    with app_with_babel.test_request_context(), pytest.raises(ValueError):
        parse_character('## Notes\n\nNo heading here.')


@pytest.mark.parametrize('locale', ['de', 'ru'])
def test_round_trip_in_another_language(app_with_babel, owner, locale):
    with app_with_babel.test_request_context(), force_locale(locale):
        data = make_character(owner).export_data()
        markdown = render_character(data)
        parsed = parse_character(markdown)
    assert '## Inventory' not in markdown  # Written in the reader's language...
    assert comparable(parsed)['items'] == comparable(data)['items']
    assert parsed['strength_max'] == 12 and parsed['notes'] == data['notes']  # ...and read back to the stored keys.


@pytest.mark.parametrize('export_format, content_type, extension', [
    ('json', 'application/json', 'json'), ('md', 'text/markdown; charset=utf-8', 'md'),
    ('txt', 'text/plain; charset=utf-8', 'txt')])
def test_export_route_formats(app_with_babel, owner, export_format, content_type, extension):
    with app_with_babel.app_context():
        db.session.add(make_character(owner))
        db.session.commit()
    response = app_with_babel.test_client().get(f'/charedit/export/md-user/ada-vell?format={export_format}')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == content_type
    assert response.headers['Content-Disposition'].endswith(f'md-user_Ada Vell.{extension}"')


def test_export_route_rejects_unknown_format(app_with_babel, owner):
    with app_with_babel.app_context():
        db.session.add(make_character(owner))
        db.session.commit()
    assert app_with_babel.test_client().get('/charedit/export/md-user/ada-vell?format=exe').status_code == 404


def test_markdown_import_end_to_end(app_with_babel, owner):
    """Markdown -> parse endpoint -> the JSON import form -> a stored character."""
    with app_with_babel.test_request_context():
        source = make_character(owner)
        db.session.add(source)
        db.session.commit()
        markdown = render_character(source.export_data())
        expected = comparable(source.export_data())
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(owner)
    parsed = client.post('/new_from_json/markdown', data={'markdown': markdown})
    assert parsed.status_code == 200
    data = parsed.get_json()
    form = {key: json.dumps(value) if isinstance(value, (list, bool)) else value
            for key, value in data.items() if value is not None}
    assert client.post('/new_from_json/', data=form).status_code == 302
    with app_with_babel.app_context():
        imported = Character.query.order_by(Character.id.desc()).first()
        assert imported.url_name != 'ada-vell'
        assert comparable(imported.export_data()) == expected


def test_markdown_parse_endpoint_reports_errors(app_with_babel, owner):
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(owner)
    response = client.post('/new_from_json/markdown', data={'markdown': 'no name'})
    assert response.status_code == 400 and 'error' in response.get_json()


@pytest.mark.parametrize('background', ['', 'barebones'])
def test_generated_character_offers_markdown(app_with_babel, background):
    import html
    import re
    response = app_with_babel.test_client().get('/gen/character', query_string={'background': background, 'view': 'sheet'})
    page = response.text
    snapshot = json.loads(html.unescape(re.search(r'id="json_data" value="([^"]*)"', page)[1]))
    markdown = html.unescape(re.search(r'<template id="pcgen-markdown-source">(.*?)</template>', page, re.S)[1])
    assert markdown.startswith(f"# {snapshot['name']}\n")
    with app_with_babel.test_request_context():
        parsed = parse_character(markdown)
    assert parsed['name'] == snapshot['name']
    assert len(parsed['items']) == len(snapshot['items'])


def test_export_dialog_lists_every_option_for_the_owner(app_with_babel, owner):
    import html
    import re
    with app_with_babel.app_context():
        db.session.add(make_character(owner))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(owner)
    page = client.get('/users/md-user/characters/ada-vell/').get_data(True)
    assert 'id="character-export-dialog"' in page
    for key in ('print', 'pdf-landscape', 'pdf-portrait', 'json', 'md', 'txt'):
        assert f'value="{key}"' in page
    urls = json.loads(html.unescape(re.search(r"data-urls='([^']*)'", page)[1]))
    assert urls['md'].endswith('/charedit/export/md-user/ada-vell?format=md')
    assert urls['pdf-portrait'].endswith('/print/portrait.pdf')
    visitor = app_with_babel.test_client().get('/users/md-user/characters/ada-vell/').get_data(True)
    assert 'value="pdf-portrait"' in visitor
    assert 'value="json"' not in visitor and '?format=md' not in visitor  # Files stay owner-only, as before.

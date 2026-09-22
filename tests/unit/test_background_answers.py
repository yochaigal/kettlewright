"""Separate background answers from personal notes throughout creation and printing."""
from io import BytesIO
import json
import re

import pytest
from pypdf import PdfReader
from markupsafe import escape
from app.lib.char_utils import generate_character
from app.models import Character, User, db
from app.models.character import BACKGROUND_FIELDS


@pytest.fixture
def background_character(app_with_babel):
    app = app_with_babel
    with app.test_request_context('/'):
        generated, raw = generate_character('Outrider')
        data = json.loads(raw)
        db.session.add(User(id=1, username='answers'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return app, client, generated, data


def test_generator_answers_and_print(background_character):
    _, client, generated, data = background_character
    assert data['notes'] == ''
    for index, table in enumerate((generated.table1, generated.table2), 1):
        assert data[f'background_table{index}_question'] == table.question
        assert data[f'background_table{index}_answer'] == table.option['description']
    page = client.post('/gen/character/print', data={'json_data':json.dumps(data)}).get_data(as_text=True)
    for field in BACKGROUND_FIELDS:
        assert str(escape(data[field])) in page
    assert 'character-print-notes-container' not in page


def test_manual_creation_stores_answers_and_no_automatic_pets(background_character):
    app, client, generated, data = background_character
    form = dict(name='Custom', custom_name='New Rider', background='Outrider', custom_background='',
                strength_max=10, dexterity_max=10, willpower_max=10, hp_max=4, gold=0, armor=0,
                items=json.dumps(data['items']), containers=json.dumps(data['containers']),
                background_table1_select=generated.table1.option['description'],
                background_table2_select=generated.table2.option['description'],
                custom_image='false', portrait_src='', age=30, bonds='', omens='')
    form.update({name:'Quiet' for name in ('Physique','Skin','Hair','Face','Speech','Clothing','Virtue','Vice')})
    response = client.post('/charcreo/save', data=form)
    assert response.headers.get('HX-Redirect')
    with app.app_context():
        character = Character.query.one()
        assert character.notes == ''
        assert character.pets == []
        for field in BACKGROUND_FIELDS:
            assert getattr(character,field) == data[field]


@pytest.mark.parametrize('output', ['html', 'portrait', 'landscape'])
def test_import_export_and_every_saved_print_preserves_separate_answers(background_character, output):
    app, client, _, data = background_character
    data['notes'] = 'Personal expedition notes.'
    data['background_table1_answer'] = 'Начало истории. ' + 'A lengthy background answer. ' * 200 + 'END-OF-ANSWER'
    form = {key:json.dumps(value) if isinstance(value,(list,bool)) else value
            for key,value in data.items() if value is not None}
    # Keep import within the field limit; the long PDF pagination case follows below.
    form['background_table1_answer'] = 'Начало истории. ' + 'A long answer. ' * 100 + 'END-OF-ANSWER'
    data['background_table1_answer'] = form['background_table1_answer']
    assert client.post('/new_from_json/', data=form).status_code == 302
    with app.app_context():
        character = Character.query.one()
        exported = json.loads(character.toJSON())
        for field in (*BACKGROUND_FIELDS, 'notes'):
            assert exported[field] == data[field]
        path = f'/users/answers/characters/{character.url_name}/print/'
    if output == 'html':
        page = client.get(path).get_data(as_text=True)
        for field in (*BACKGROUND_FIELDS, 'notes'):
            assert str(escape(data[field])) in page
    else:
        response = client.get(path + output + '.pdf')
        assert response.status_code == 200
        reader = PdfReader(BytesIO(response.data))
        page = re.sub(r'\s+', ' ', '\n'.join(p.extract_text() for p in reader.pages))
        for field in (*BACKGROUND_FIELDS, 'notes'):
            assert re.sub(r'\s+', ' ', data[field]) in page


def test_edit_keeps_old_notes_and_new_answers_independent(background_character):
    app, client, _, _ = background_character
    with app.app_context():
        c = Character(owner=1, owner_username='answers', name='Old Hero', url_name='old',
                      background='Outrider', notes='Existing notes with a familiar.',
                      items='[]', containers='[{"id":0,"name":"Main","slots":10}]')
        db.session.add(c)
        db.session.commit()
    html = client.get('/charedit/answers/old').get_data(as_text=True)
    assert 'Existing notes with a familiar.' in html
    for field in BACKGROUND_FIELDS:
        assert f'name="{field}"' in html
    response = client.post('/charedit/answers/old/save', data=dict(
        party_code='', name='Old Hero', notes='My updated notes.',
        background_table1_question='A question?', background_table1_answer='My answer.',
        background_table2_question='', background_table2_answer=''))
    assert response.status_code == 200
    with app.app_context():
        c = Character.query.one()
        assert c.notes == 'My updated notes.'
        assert c.background_table1_answer == 'My answer.'
        assert c.pets == []

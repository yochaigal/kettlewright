"""Empty bonds and omens stay empty when a character is created in a translated locale."""
import json

import pytest
from flask_babel import Babel

from app import get_locale
from app.lib.char_utils import generate_character
from app.models import Character, User, db


@pytest.fixture
def client(app):
    Babel(app, locale_selector=get_locale)
    with app.test_request_context('/'):
        db.session.add(User(id=1, username='empty'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    client.set_cookie('kw_lang', 'ru')
    return client


def test_empty_bonds_and_omens_are_saved_empty(app, client):
    # #given a Russian visitor who leaves bonds and omens blank
    with app.test_request_context('/'):
        generated, raw = generate_character('Outrider')
    data = json.loads(raw)
    form = dict(name='Custom', custom_name='Blank Rider', background='Outrider', custom_background='',
                strength_max=10, dexterity_max=10, willpower_max=10, hp_max=4, gold=0, armor=0,
                items=json.dumps(data['items']), containers=json.dumps(data['containers']),
                background_table1_select=generated.table1.option['description'],
                background_table2_select=generated.table2.option['description'],
                custom_image='false', portrait_src='', age=30, bonds='', omens='')
    form.update({name: 'Quiet' for name in ('Physique', 'Skin', 'Hair', 'Face', 'Speech', 'Clothing', 'Virtue', 'Vice')})
    # #when the character is saved
    assert client.post('/charcreo/save', data=form).headers.get('HX-Redirect')
    # #then neither field holds the translation catalog header
    with app.app_context():
        character = Character.query.one()
        assert (character.bonds, character.omens) == ('', '')

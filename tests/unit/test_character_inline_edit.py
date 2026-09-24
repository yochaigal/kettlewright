import json

import pytest

from app.models import Character, Party, User, db


@pytest.fixture
def sheet(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='other')])
        db.session.add(Character(
            id=1, owner=1, name='Hero', url_name='hero', background='Test',
            strength=10, strength_max=12, dexterity=8, dexterity_max=8,
            willpower=9, willpower_max=9, hp=3, hp_max=5, gold=11,
            items='[]', containers='[{"id": 0, "name": "Main", "slots": 10}]', notes='Original notes', traits='Quiet',
            image_url='adventurer.webp', custom_image=False))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return app_with_babel, client


def section_path(section):
    return '/charedit/owner/hero/section/' + section


@pytest.mark.parametrize('section', ['name', 'traits', 'description', 'bonds', 'omens', 'scars',
                                      'notes', 'background', 'party'])
def test_open_and_cancel_sections(sheet, section):
    app, client = sheet
    response = client.get(section_path(section))
    assert response.status_code == 200
    assert b'character-inline-form no-space' in response.data
    response = client.get(section_path(section) + '?view=1')
    assert response.status_code == 200
    assert b'character-inline-form no-space' not in response.data
    with app.app_context():
        assert db.session.get(Character, 1).notes == 'Original notes'


def test_save_only_selected_fields_and_keep_character_url(sheet):
    app, client = sheet
    response = client.post(section_path('name'), data={'name': 'Renamed', 'notes': 'Discard me', 'gold': '0'})
    assert response.status_code == 200
    assert b'Renamed' in response.data
    assert 'character-section-saved' in response.headers['HX-Trigger']
    client.post(section_path('notes'), data={'notes': '<b>Journal</b><script>bad()</script>'})
    with app.app_context():
        character = db.session.get(Character, 1)
        assert character.name == 'Renamed'
        assert character.url_name == 'hero'
        assert character.gold == 11
        assert '<b>Journal</b>' in character.notes
        assert '<script>' not in character.notes
        assert character.traits == 'Quiet'


@pytest.mark.parametrize('data', [{'name': ''}, {'name': 'x' * 33}])
def test_invalid_name_retains_editor_and_does_not_write(sheet, data):
    app, client = sheet
    response = client.post(section_path('name'), data=data)
    assert b'role="alert"' in response.data
    assert b'character-inline-form no-space' in response.data
    assert 'HX-Trigger' not in response.headers
    with app.app_context():
        assert db.session.get(Character, 1).name == 'Hero'


@pytest.mark.parametrize('field,value', [('gold', 0), ('hp_max', 7), ('strength_max', 8),
                                         ('deprived', 1), ('panicked', 1), ('dead', 1)])
def test_individual_sheet_stat_save(sheet, field, value):
    app, client = sheet
    response = client.post('/charedit/owner/hero/stat', data={'stat': field, 'value': value})
    assert response.status_code == 204
    with app.app_context():
        character = db.session.get(Character, 1)
        assert getattr(character, field) == value
        assert character.notes == 'Original notes'
        if field == 'strength_max':
            assert character.strength == 8
        else:
            assert character.strength == 10
    if field in ('deprived', 'panicked', 'dead'):
        assert client.post('/charedit/owner/hero/stat', data={'stat': field, 'value': 0}).status_code == 204
        with app.app_context():
            assert not getattr(db.session.get(Character, 1), field)


@pytest.mark.parametrize('field,value', [('hp', 6), ('gold', -1), ('gold', 10000), ('hp_max', 'bad'),
                                         ('strength_max', 100), ('dead', 2), ('owner', 2)])
def test_invalid_individual_stats_do_not_write(sheet, field, value):
    app, client = sheet
    response = client.post('/charedit/owner/hero/stat', data={'stat': field, 'value': value})
    assert response.status_code == 400
    with app.app_context():
        character = db.session.get(Character, 1)
        assert (character.hp, character.hp_max, character.gold, character.strength_max) == (3, 5, 11, 12)
        assert not character.dead


@pytest.mark.parametrize('field', ['hp_max', 'gold', 'dead'])
def test_sheet_resource_controls_require_owner_and_csrf(sheet, field):
    app, client = sheet
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert client.post('/charedit/owner/hero/stat', data={'stat': field, 'value': 0}).status_code == 403
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/charedit/owner/hero/stat', data={'stat': field, 'value': 0}).status_code == 400


def test_party_join_invalid_code_and_leave(sheet):
    app, client = sheet
    with app.app_context():
        db.session.add(Party(id=1, owner=2, name='Party', party_url='party', join_code='JOIN', members='[]', subowners='[]'))
        db.session.commit()
    response = client.post(section_path('party'), data={'party_code': 'wrong'})
    assert b'Invalid party code' in response.data
    response = client.post(section_path('party'), data={'party_code': 'JOIN'})
    assert json.loads(response.headers['HX-Trigger'])['character-section-saved']['partyId'] == 1
    with app.app_context():
        assert db.session.get(Character, 1).party_id == 1
        assert json.loads(db.session.get(Party, 1).members) == [1]
    client.post(section_path('party'), data={'leave_party': '1'})
    with app.app_context():
        assert db.session.get(Character, 1).party_id is None
        assert json.loads(db.session.get(Party, 1).members) == []


def test_owner_only_and_csrf(sheet):
    app, client = sheet
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert client.get(section_path('notes')).status_code == 403
    assert client.post(section_path('notes'), data={'notes': 'No'}).status_code == 403
    with client.session_transaction() as session:
        session.clear()
    assert client.post(section_path('notes'), data={'notes': 'No'}).status_code == 302
    response = client.get('/users/owner/characters/hero/')
    assert response.status_code == 200
    assert b'/section/' not in response.data
    assert b'character-portrait-edit' not in response.data
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(section_path('notes'), data={'notes': 'No'}).status_code == 400
    assert client.post(section_path('owner'), data={'owner': '2'}).status_code == 404


def test_sheet_has_inline_controls_without_global_edit_button(sheet):
    _, client = sheet
    response = client.get('/users/owner/characters/hero/')
    assert response.status_code == 200
    assert b'Click to switch edit/view mode' not in response.data
    assert b'save automatically' not in response.data
    assert section_path('stats').encode() not in response.data
    assert response.data.count(b'class="sheet-stat-form"') == 12
    assert client.get(section_path('stats')).status_code == 404
    for section in ('name', 'traits', 'notes', 'party', 'background'):
        assert section_path(section).encode() in response.data


def test_inline_portrait_cancel_and_save_stay_on_sheet(sheet):
    app, client = sheet
    path = '/charedit/inplace-portrait/owner/hero/'
    response = client.get(path + 'cancel?sheet_context=inline')
    assert 'HX-Redirect' not in response.headers
    assert b'character-portrait-edit' in response.data
    response = client.post(path + 'save', data={
        'sheet_context': 'inline', 'custom-url': '', 'selected-portrait': 'another.webp'})
    assert 'HX-Redirect' not in response.headers
    assert b'another.webp' in response.data
    with app.app_context():
        assert db.session.get(Character, 1).image_url == 'another.webp'

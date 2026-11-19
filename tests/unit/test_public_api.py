"""Public read-only API for the Tools (#137)."""
import json
import random

import pytest

from app.lib.tool_tables import ROLLS, load_tables, roll
from app.models import Character, User, db


@pytest.fixture
def client(app_with_babel):
    return app_with_babel.test_client()


def test_index_lists_every_endpoint(client):
    response = client.get('/api/v1/')
    assert response.status_code == 200 and response.is_json
    endpoints = response.json['endpoints']
    assert set(endpoints['rolls']) == set(ROLLS)
    for url in [endpoints['backgrounds'], endpoints['random_character'], endpoints['monsters'],
                endpoints['tables'], *(r['url'] for r in endpoints['rolls'].values())]:
        assert client.get(url).status_code == 200, url


def test_random_character_for_a_background(client):
    character = client.get('/api/v1/characters/random?background=mountebank').json
    assert character['background'] == 'Mountebank'
    assert isinstance(character['items'], list) and isinstance(character['containers'], list)
    assert any(c['name'] == 'Cart' for c in character['containers'])
    assert character['image_url'].startswith('http')
    assert 3 <= character['strength'] <= 18


def test_random_barebones_character(client):
    packages = client.get('/api/v1/backgrounds').json['barebones_packages']
    assert client.get('/api/v1/characters/random?background=barebones').status_code == 200
    assert client.get(f'/api/v1/characters/random?background=barebones:{packages[0]}').status_code == 200


@pytest.mark.parametrize('background', ['Nope', 'barebones:Nope'])
def test_unknown_background_is_a_json_404(client, background):
    response = client.get(f'/api/v1/characters/random?background={background}')
    assert response.status_code == 404 and response.json['status'] == 404
    assert 'Nope' in response.json['error']


def test_backgrounds_match_the_character_generator(client):
    from app.lib.data import load_backgrounds
    with client.application.test_request_context('/'):
        names = list(load_backgrounds())
    assert [b['name'] for b in client.get('/api/v1/backgrounds').json['backgrounds']] == names


def test_monsters(client):
    monsters = client.get('/api/v1/monsters').json['monsters']
    acolyte = next(m for m in monsters if m['key'] == 'acolyte')
    assert client.get('/api/v1/monsters/acolyte').json == acolyte
    assert acolyte['name'] == 'Acolyte' and acolyte['image_url'].startswith('http')
    assert client.get('/api/v1/monsters/nope').status_code == 404


@pytest.mark.parametrize('table', list(ROLLS))
def test_every_table_rolls(client, table):
    result = client.get(f'/api/v1/roll/{table}').json
    assert set(result) == {'title', 'category', 'fields'} and result['fields']


def test_rolls_match_the_tools_tables(app_with_babel):
    with app_with_babel.test_request_context('/'):
        data = load_tables()
    rng = random.Random(4)
    assert roll('relic', rng=rng, data=data)['fields'] in data['Relics']
    assert roll('dungeon-events', rng=rng, data=data)['fields'] in data['Dungeon Events']
    assert roll('reaction', rng=rng, data=data)['fields']['Reaction'] in data['Reaction Roll']
    weather = roll('weather', {'season': 'winter'}, rng=rng, data=data)['fields']
    assert weather['Season'] == 'Winter' and weather['Type'] in data['Weather']['Types']['Winter']


def test_bad_parameters_and_unknown_paths_are_json(client):
    response = client.get('/api/v1/roll/weather?season=Monsoon')
    assert response.status_code == 400 and 'Monsoon' in response.json['error']
    for path in ['/api/v1/roll/nope', '/api/v1/nope', '/api/v1/a/b']:
        response = client.get(path)
        assert response.status_code == 404 and response.is_json, path


def test_any_origin_may_call_the_api(client):
    response = client.get('/api/v1/roll/reaction', headers={'Origin': 'https://example.org'})
    assert response.headers['Access-Control-Allow-Origin'] in ('*', 'https://example.org')


def test_lang_translates_without_changing_the_site_language(client):
    from flask_babel import Babel
    from app import get_locale
    Babel(client.application, locale_selector=get_locale)
    english = client.get('/api/v1/tables').json['Reaction Roll']
    response = client.get('/api/v1/tables?lang=ru')
    assert response.json['Reaction Roll'] != english
    assert 'kw_lang' not in response.headers.get('Set-Cookie', '')
    assert client.get('/api/v1/tables').json['Reaction Roll'] == english


def test_older_character_endpoint_still_works(client):
    with client.application.app_context():
        db.session.add(User(id=1, username='owner'))
        db.session.add(Character(owner=1, owner_username='owner', name='Ambrose', url_name='ambrose',
                                 background='Mountebank', items='[]', containers='[]'))
        db.session.commit()
    response = client.get('/api/users/owner/characters/ambrose/')
    assert response.status_code == 200 and response.json['name'] == 'Ambrose'
    assert client.get('/api/users/owner/characters/nobody/').status_code == 404

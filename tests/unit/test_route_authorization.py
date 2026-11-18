"""Regression tests for issue #212: character routes must check who is editing."""
import json

import pytest
from app.models import User, Character, Party, db


@pytest.fixture
def setup(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='owner'), User(id=2, username='outsider'),
                            User(id=3, username='warden')])
        db.session.add(Party(id=1, owner=3, name='Party', party_url='party', members='[1]', join_code='JOIN'))
        db.session.add(Character(id=1, owner=1, name='Hero', url_name='hero', background='Test',
                                 gold=10, party_id=1, party_code='JOIN', items='[]',
                                 containers='[{"id":0,"name":"Main","slots":10}]'))
        db.session.commit()
    return app_with_babel, app_with_babel.test_client()


def login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)


def character(app):
    with app.app_context():
        c = db.session.get(Character, 1)
        return c.gold, json.loads(c.items or '[]'), c.party_id


BUY = {'current-gold': '9999', 'current-cart': json.dumps(['Rations'])}


@pytest.mark.parametrize('user_id', [None, 2])
def test_marketplace_buy_rejects_non_editors(setup, user_id):
    app, client = setup
    if user_id:
        login(client, user_id)
    response = client.post('/marketplace/owner/hero/0/buy', data=BUY)
    assert response.status_code in (302, 401, 403)
    assert character(app) == (10, [], 1)


@pytest.mark.parametrize('user_id', [None, 2])
def test_marketplace_show_rejects_non_editors(setup, user_id):
    app, client = setup
    if user_id:
        login(client, user_id)
    assert client.get('/marketplace/owner/hero/0').status_code in (302, 401, 403)


def test_marketplace_buy_allows_owner(setup):
    app, client = setup
    login(client, 1)
    assert client.get('/marketplace/owner/hero/0').status_code == 200
    assert client.post('/marketplace/owner/hero/0/buy', data=BUY).status_code == 200
    gold, items, _ = character(app)
    assert gold == 9999
    assert [item['name'] for item in items] == ['Rations']


def test_marketplace_buy_requires_csrf(setup):
    app, client = setup
    login(client, 1)
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/marketplace/owner/hero/0/buy', data=BUY).status_code == 400
    assert character(app) == (10, [], 1)


@pytest.mark.parametrize('user_id', [None, 2, 3])
def test_leave_party_rejects_non_owners(setup, user_id):
    app, client = setup
    if user_id:
        login(client, user_id)
    response = client.post('/charedit/leave-party/owner/hero')
    assert response.status_code in (302, 401, 403)
    assert character(app)[2] == 1


def test_leave_party_rejects_get(setup):
    app, client = setup
    login(client, 1)
    assert client.get('/charedit/leave-party/owner/hero').status_code == 405
    assert character(app)[2] == 1


def test_leave_party_allows_owner(setup):
    app, client = setup
    login(client, 1)
    assert client.post('/charedit/leave-party/owner/hero').status_code == 200
    assert character(app)[2] is None


def test_clear_party_err_route_is_gone(setup):
    app, client = setup
    assert client.get('/charedit/clear-party-err/owner/hero').status_code == 404


def test_legacy_editor_leave_button_posts_with_csrf(setup):
    app, client = setup
    login(client, 1)
    app.config['WTF_CSRF_ENABLED'] = True
    page = client.get('/charedit/owner/hero').get_data(as_text=True)
    assert 'hx-post="/charedit/leave-party/owner/hero"' in page
    assert '"csrf_token": ""' not in page

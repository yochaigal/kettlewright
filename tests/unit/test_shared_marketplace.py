import json

import pytest
from app.models import User, Character, Party, db


@pytest.fixture
def shared_market(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='player'), User(id=3, username='outsider')])
        db.session.add(Party(id=1, owner=1, name='Party', members='[1]', items='[]',
                            containers='[{"id":0,"name":"Main","slots":10},{"id":3,"name":"Stash","slots":2}]'))
        db.session.add(Character(id=1, owner=2, name='Player', background='Test', gold=10, party_id=1))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return app_with_babel, client


def test_add_catalog_item_to_selected_party_container(shared_market):
    app, client = shared_market
    response = client.post('/marketplace/party/1/3', data={'item': 'Rations'})
    assert response.status_code == 200
    with app.app_context():
        item = json.loads(db.session.get(Party, 1).items)[0]
        assert item['name'] == 'Rations'
        assert item['location'] == 3
        assert item['uses'] == 3
        assert db.session.get(Character, 1).gold == 10


def test_full_container_rejects_addition(shared_market):
    app, client = shared_market
    for _ in range(3):
        response = client.post('/marketplace/party/1/3', data={'item': 'Rations'})
    assert b'Not enough space' in response.data
    with app.app_context():
        assert len(json.loads(db.session.get(Party, 1).items)) == 2


def test_unauthorized_or_unknown_items_do_not_mutate(shared_market):
    app, client = shared_market
    response = client.post('/marketplace/party/1/3', data={'item': 'Invented'})
    assert b'Item not found' in response.data
    with client.session_transaction() as session:
        session['_user_id'] = '3'
    assert client.post('/marketplace/party/1/3', data={'item': 'Rations'}).status_code == 403
    with app.app_context():
        assert db.session.get(Party, 1).items == '[]'


def test_member_can_search_and_add(shared_market):
    app, client = shared_market
    with client.session_transaction() as session:
        session['_user_id'] = '2'
    assert b'Rations' in client.get('/marketplace/party/1/3?filter=rations').data
    assert client.post('/marketplace/party/1/3', data={'item': 'Rations'}).status_code == 200

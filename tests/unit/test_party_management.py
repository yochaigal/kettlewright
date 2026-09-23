import pytest
from flask import g

from app.models import Character, Party, PartyRoll, User, db


@pytest.fixture
def party_setup(app_with_babel):
    with app_with_babel.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='other')])
        db.session.add(Party(id=1, owner=1, name='Party', party_url='party', members='[1]',
                             items='[]', containers='[{"id":0,"name":"Main","slots":10}]', join_code='join-secret'))
        db.session.add(Character(id=1, owner=2, owner_username='other', url_name='member', name='Member', background='Test', party_id=1,
                                 items='[]', image_url='default-portrait.webp', containers='[]'))
        db.session.commit()
        yield app_with_babel.test_client()


def login(client, user_id):
    # The fixture keeps one app context; discard Flask-Login's cached identity.
    g.pop('_login_user', None)
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)


def test_owner_can_remove_member_but_others_cannot(party_setup):
    client = party_setup
    path = '/party/remove-char/1/warden/party'
    assert client.post(path).status_code == 302
    login(client, 2)
    assert client.post(path).status_code == 403
    assert db.session.get(Character, 1).party_id == 1
    login(client, 1)
    assert client.get(path).status_code == 405
    assert client.post(path).status_code == 200
    assert db.session.get(Character, 1).party_id is None


def test_delete_requires_owner_post_and_clears_members(party_setup):
    client = party_setup
    login(client, 2)
    assert client.post('/party/delete/1').status_code == 403
    login(client, 1)
    db.session.add(PartyRoll(party_id=1, character_name='Member', result='4 (d6)'))
    db.session.commit()
    assert client.get('/party/delete/1').status_code == 405
    assert client.post('/party/delete/1').status_code == 200
    assert db.session.get(Party, 1) is None
    assert db.session.get(Character, 1).party_id is None
    assert PartyRoll.query.count() == 0


def test_original_join_code_button_and_warden_label(party_setup):
    login(party_setup, 1)
    page = party_setup.get('/users/warden/parties/party/').get_data(as_text=True)
    assert 'id="join-code-button"' in page
    assert 'id="party-invitation"' not in page
    assert 'Warden' in page
    assert page.index('id="inventory-container"') < page.index('id="party-roll-history"')
    assert 'Latest 20 rolls' in page
    assert 'id="clear-roll-history"' in page
    login(party_setup, 2)
    page = party_setup.get('/users/warden/parties/party/').get_data(as_text=True)
    assert 'join-secret' not in page
    assert 'id="party-roll-history"' in page
    assert 'id="clear-roll-history"' not in page
    db.session.get(Character, 1).party_id = None
    db.session.commit()
    page = party_setup.get('/users/warden/parties/party/').get_data(as_text=True)
    assert 'id="party-roll-history"' not in page

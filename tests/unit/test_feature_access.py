import re

import pytest
from flask import Flask
from flask_login import LoginManager, login_user

from app.lib.feature_access import (init_feature_access, user_features_enabled,
                                    party_features_enabled, require_party_features)
from app.models import db, User, CampaignParty, PartyMap, PartyPresentation
from test_campaigns import setup, login, create_entry, reveal, description_image
from test_shared_map import shared, URL, DRAWING


@pytest.mark.parametrize('raw, expected', [(None, set()), ('', set()), (' , \n ', set()),
    ('1, 2\n3\t2', {1, 2, 3}), ('001,12', {1, 12})])
def test_environment_lists(monkeypatch, raw, expected):
    monkeypatch.setenv('LOCAL_FEATURE_ACCESS', 'False')
    for key in ('FEATURE_TEST_USER_IDS', 'FEATURE_TEST_PARTY_IDS'):
        monkeypatch.delenv(key, raising=False)
        if raw is not None:
            monkeypatch.setenv(key, raw)
    app = Flask(__name__)
    init_feature_access(app)
    assert app.config['FEATURE_TEST_USER_IDS'] == expected
    assert app.config['FEATURE_TEST_PARTY_IDS'] == expected


@pytest.mark.parametrize('key', ['FEATURE_TEST_USER_IDS', 'FEATURE_TEST_PARTY_IDS'])
@pytest.mark.parametrize('raw', ['*', '0', '-1', '1,abc', '1.5', 'True'])
def test_invalid_configuration_fails_closed(monkeypatch, key, raw):
    monkeypatch.setenv('LOCAL_FEATURE_ACCESS', 'False')
    monkeypatch.setenv('FEATURE_TEST_USER_IDS', '')
    monkeypatch.setenv('FEATURE_TEST_PARTY_IDS', '')
    monkeypatch.setenv(key, raw)
    with pytest.raises(ValueError, match=key):
        init_feature_access(Flask(__name__))


def test_audiences_remain_available_for_future_experiments(monkeypatch):
    monkeypatch.setenv('LOCAL_FEATURE_ACCESS', 'False')
    monkeypatch.setenv('FEATURE_TEST_USER_IDS', '1')
    monkeypatch.setenv('FEATURE_TEST_PARTY_IDS', '2')
    app = Flask(__name__)
    app.secret_key = 'test'
    LoginManager(app)
    init_feature_access(app)
    with app.test_request_context():
        login_user(User(id=1))
        assert user_features_enabled()
        assert not party_features_enabled(1)
        assert party_features_enabled(2)
        require_party_features(2)
        from werkzeug.exceptions import NotFound
        with pytest.raises(NotFound):
            require_party_features(1)
        login_user(User(id=2))
        assert not user_features_enabled()


@pytest.mark.parametrize('url', ['/campaigns/', '/campaigns/1/', '/materials/',
    '/materials/new', '/materials/import-archive', '/maps/new', '/maps/tables', '/articles/tables'])
def test_authoring_pages_are_available_without_tester_ids(setup, url):
    _, client = setup
    assert client.get(url, follow_redirects=True).status_code == 200


@pytest.mark.parametrize('url', ['/campaigns/', '/materials/new', '/materials/import-archive',
    '/maps/new', '/party/1/materials/', '/party/1/materials/data',
    '/party/1/shared-map', '/party/1/shared-map/scene'])
def test_released_features_still_require_login(setup, url):
    app, _ = setup
    client = app.test_client()
    assert client.get(url).status_code == 302
    assert client.post(url).status_code in (302, 405)


def test_party_members_can_read_and_author_their_own_campaigns(setup):
    _, client = setup
    entry_id = create_entry(client)
    assert reveal(client, entry_id).status_code == 302
    login(client, 2)
    page = client.get('/party/1/materials/')
    assert page.status_code == 200
    assert 'href="/campaigns/"' in page.text
    assert 'href="/materials/new' not in page.text
    assert client.get('/party/1/materials/data').json['entries'][0]['title'] == 'Known name'
    assert client.get('/campaigns/').status_code == 200
    assert 'Secret campaign' not in client.get('/campaigns/').text
    assert client.get('/campaigns/1/').status_code == 403
    assert client.get(f'/materials/{entry_id}/edit').status_code == 403
    login(client, 3)
    assert client.get('/party/1/materials/data').status_code == 403


def test_publication_and_direct_creation_support_all_owned_parties(setup):
    app, client = setup
    entry_id = create_entry(client)
    assert reveal(client, entry_id, party_id=2).status_code == 302
    assert client.post('/materials/new', data={'party_id': 2, 'category': 'lore',
        'title': 'New lore', 'body': 'Known lore'}).status_code == 302
    assert client.post('/maps/new', data={'party_id': 2, 'title': 'New map',
        'kind': 'freeform'}).status_code == 302
    assert client.post('/campaigns/1/', data={'name': 'New', 'version': 1,
                                           'party_ids': [1, 2]}).status_code == 302
    page = client.get(f'/materials/{entry_id}/reveal').text
    assert 'Party 1' in page and 'Party 2' in page and 'Party 3' not in page
    assert reveal(client, entry_id, party_id=3).status_code == 403
    with app.app_context():
        assert db.session.get(CampaignParty, (1, 2)) is not None


def test_unlinking_any_party_revokes_publications(setup):
    app, client = setup
    entry_id = create_entry(client)
    assert reveal(client, entry_id, party_id=2).status_code == 302
    assert client.post('/campaigns/1/', data={'name': 'New', 'version': 1,
                                           'party_ids': [1]}).status_code == 302
    with app.app_context():
        assert db.session.get(CampaignParty, (1, 2)) is None
        assert not PartyPresentation.query.filter_by(entry_id=entry_id, party_id=2).one().published
    login(client, 3)
    assert client.get('/party/2/materials/data').json['entries'] == []


def test_images_follow_ownership_membership_and_publication(setup):
    app, client = setup
    entry_id = create_entry(client, body=description_image(client))
    from app.models import ContentEntry
    with app.app_context():
        stored = db.session.get(ContentEntry, entry_id).body
    url = re.search(r'src="([^"]+)"', stored)[1]
    assert client.get(url).status_code == 200
    login(client, 2)
    assert client.get(url).status_code == 404
    login(client, 1)
    assert reveal(client, entry_id, body=stored).status_code == 302
    login(client, 2)
    assert client.get(url).status_code == 200
    login(client, 3)
    assert client.get(url).status_code == 404
    login(client, 1)
    assert client.post(f'/materials/{entry_id}/revoke/1', data={'version': 1}).status_code == 302
    login(client, 2)
    assert client.get(url).status_code == 404
    assert app.test_client().get(url).status_code == 302


def test_navigation_and_tools_are_released(setup):
    app, client = setup
    from app.models import Character
    with app.app_context():
        character = db.session.get(Character, 1)
        character.owner_username, character.url_name = 'user2', 'player-a'
        db.session.commit()
    page = client.get('/users/user1/parties/party1/')
    assert page.status_code == 200
    for link in ('/campaigns/', '/party/1/shared-map', '/materials/new'):
        assert f'href="{link}' in page.text
    assert 'id="campaign-details-tab"' in page.text
    assert 'data-content-url="/party/1/materials/?preview=0"' in page.text
    for visitor in (client, app.test_client()):
        tools = visitor.get('/tools/').text
        assert 'src/js/tools.js' in tools
        assert 'src/js/tools_legacy.js' not in tools
    tools = client.get('/tools/').text
    assert 'id="pcgen-save-npc-button"' in tools
    assert '"authenticated": true' in tools
    guest = app.test_client().get('/tools/').text
    assert '"authenticated": false' in guest
    assert 'id="pcgen-save-npc-button"' not in guest
    assert 'href="/campaigns/"' not in guest


def test_shared_map_still_requires_current_membership(shared):
    app, clients, sockets = shared
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 200
    with app.app_context():
        assert PartyMap.query.count() == 1
    assert sockets[2].get_received()[0]['name'] == 'shared_map_changed'
    assert clients[2].get(URL).status_code == 200
    assert clients[2].post(URL, json={'version': 1, 'drawing': DRAWING}).status_code == 200
    assert clients[3].get(URL).status_code == 403
    assert clients[3].post(URL, json={'version': 2, 'drawing': DRAWING}).status_code == 403


def test_content_notifications_reach_all_parties_but_only_current_members(shared):
    from app.lib.campaigns import notify_parties
    app, _, sockets = shared
    with app.app_context():
        notify_parties([1, 2])
    for user_id in (1, 2, 4):
        events = sockets[user_id].get_received()
        assert events[0]['name'] == 'campaign_content_changed'
        assert events[0]['args'][0]['party_id'] == (2 if user_id == 4 else 1)
    assert sockets[3].get_received() == []


def test_local_mode_ignores_even_invalid_lists(monkeypatch):
    monkeypatch.setenv('LOCAL_FEATURE_ACCESS', 'True')
    monkeypatch.setenv('FEATURE_TEST_USER_IDS', '*')
    monkeypatch.setenv('FEATURE_TEST_PARTY_IDS', 'invalid')
    app = Flask(__name__)
    init_feature_access(app)
    assert app.config['LOCAL_FEATURE_ACCESS'] is True

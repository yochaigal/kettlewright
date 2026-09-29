import re

import pytest
from flask import Flask

from app.lib.feature_access import init_feature_access
from app.models import db, CampaignParty, PartyMap, PartyPresentation
from test_campaigns import setup, login, create_entry, reveal, description_image
from test_shared_map import shared, URL, DRAWING


@pytest.mark.parametrize('raw, expected', [(None, set()), ('', set()), (' , \n ', set()),
    ('1, 2\n3\t2', {1, 2, 3}), ('001,12', {1, 12})])
def test_environment_lists(monkeypatch, raw, expected):
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
    monkeypatch.setenv('FEATURE_TEST_USER_IDS', '')
    monkeypatch.setenv('FEATURE_TEST_PARTY_IDS', '')
    monkeypatch.setenv(key, raw)
    with pytest.raises(ValueError, match=key):
        init_feature_access(Flask(__name__))


@pytest.mark.parametrize('url', ['/campaigns/', '/campaigns/1/', '/campaigns/1/delete',
    '/materials/', '/materials/new', '/materials/1/edit', '/materials/1/delete',
    '/materials/bulk-delete', '/materials/1/reveal', '/materials/1/revoke/1',
    '/materials/import', '/maps/new', '/maps/1/edit', '/maps/1/data', '/maps/tables'])
def test_private_routes_require_user_allowlist_for_reads_and_writes(setup, url):
    app, client = setup
    app.config['FEATURE_TEST_USER_IDS'] = set()
    for method in ('GET', 'POST'):
        response = client.open(url, method=method)
        assert response.status_code in (404, 405)


@pytest.mark.parametrize('url', ['/party/1/materials/', '/party/1/materials/data',
    '/party/1/materials/1', '/party/1/maps/1/', '/party/1/maps/1/data',
    '/party/1/shared-map', '/party/1/shared-map/scene'])
def test_personal_tester_cannot_bypass_party_allowlist(setup, url):
    app, client = setup
    app.config['FEATURE_TEST_PARTY_IDS'] = set()
    assert client.get(url).status_code == 404


def test_party_members_can_read_without_personal_authoring_access(setup):
    app, client = setup
    entry_id = create_entry(client)
    assert reveal(client, entry_id).status_code == 302
    app.config.update(FEATURE_TEST_USER_IDS={1}, FEATURE_TEST_PARTY_IDS={1})
    login(client, 2)
    page = client.get('/party/1/materials/')
    assert page.status_code == 200
    assert 'href="/campaigns/"' not in page.text
    assert 'href="/materials/new' not in page.text
    assert client.get('/party/1/materials/data').json['entries'][0]['title'] == 'Known name'
    assert client.get('/campaigns/').status_code == 404
    login(client, 3)
    assert client.get('/party/1/materials/data').status_code == 403


def test_publication_and_direct_creation_require_listed_party(setup):
    app, client = setup
    entry_id = create_entry(client)
    app.config['FEATURE_TEST_PARTY_IDS'] = {1}
    assert reveal(client, entry_id, party_id=2).status_code == 404
    assert client.post('/materials/new', data={'party_id': 2}).status_code == 404
    assert client.post('/maps/new', data={'party_id': 2}).status_code == 404
    assert client.post('/campaigns/1/', data={'name': 'New', 'version': 1,
                                           'party_ids': [1, 2]}).status_code == 404
    page = client.get(f'/materials/{entry_id}/reveal').text
    assert 'Party 1' in page and 'Party 2' not in page


def test_hidden_party_links_and_publications_survive_campaign_save(setup):
    app, client = setup
    entry_id = create_entry(client)
    assert reveal(client, entry_id, party_id=2).status_code == 302
    app.config['FEATURE_TEST_PARTY_IDS'] = {1}
    assert client.post('/campaigns/1/', data={'name': 'New', 'version': 1,
                                           'party_ids': [1]}).status_code == 302
    with app.app_context():
        assert db.session.get(CampaignParty, (1, 2)) is not None
        assert PartyPresentation.query.filter_by(entry_id=entry_id, party_id=2).one().published
    app.config['FEATURE_TEST_PARTY_IDS'] = {2}
    login(client, 3)
    assert client.get('/party/2/materials/data').json['entries'][0]['title'] == 'Known name'


def test_images_follow_both_rollout_audiences(setup):
    app, client = setup
    entry_id = create_entry(client, body=description_image(client))
    from app.models import ContentEntry
    with app.app_context():
        stored = db.session.get(ContentEntry, entry_id).body
    url = re.search(r'src="([^"]+)"', stored)[1]
    assert reveal(client, entry_id, body=stored).status_code == 302
    app.config.update(FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    assert client.get(url).status_code == 404
    app.config['FEATURE_TEST_USER_IDS'] = {1}
    assert client.get(url).status_code == 200
    login(client, 2)
    assert client.get(url).status_code == 404
    app.config['FEATURE_TEST_PARTY_IDS'] = {1}
    assert client.get(url).status_code == 200
    login(client, 3)
    assert client.get(url).status_code == 404


def test_navigation_and_tools_use_independent_lists(setup):
    app, client = setup
    from app.models import Character
    with app.app_context():
        character = db.session.get(Character, 1)
        character.owner_username, character.url_name = 'user2', 'player-a'
        db.session.commit()
    app.config.update(FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    page_url = '/users/user1/parties/party1/'
    page = client.get(page_url)
    assert page.status_code == 200
    for link in ('/campaigns/', '/party/1/shared-map', '/party/1/materials/', '/materials/new'):
        assert f'href="{link}' not in page.text
    assert 'src/js/tools_legacy.js' in client.get('/tools/').text
    app.config['FEATURE_TEST_PARTY_IDS'] = {1}
    page = client.get(page_url).text
    assert 'href="/party/1/shared-map"' in page
    assert 'href="/party/1/materials/"' in page
    assert 'href="/materials/new' not in page
    app.config['FEATURE_TEST_USER_IDS'] = {1}
    assert 'src/js/tools.js' in client.get('/tools/').text
    assert 'href="/materials/new' in client.get(page_url).text
    assert 'src/js/tools_legacy.js' in app.test_client().get('/tools/').text


def test_disabled_shared_map_rejects_writes_without_mutation_or_notifications(shared):
    app, clients, sockets = shared
    app.config['FEATURE_TEST_PARTY_IDS'] = set()
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 404
    with app.app_context():
        assert PartyMap.query.count() == 0
    assert all(client.get_received() == [] for client in sockets.values())
    app.config.update(FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS={1})
    assert clients[1].post(URL, json={'version': 0, 'drawing': DRAWING}).status_code == 200
    assert clients[2].get(URL).status_code == 200
    assert clients[2].post(URL, json={'version': 1, 'drawing': DRAWING}).status_code == 403
    assert clients[3].get(URL).status_code == 403


def test_content_notifications_skip_disabled_parties(shared):
    from app.lib.campaigns import notify_parties
    app, _, sockets = shared
    app.config['FEATURE_TEST_PARTY_IDS'] = {2}
    with app.app_context():
        notify_parties([1, 2])
    assert sockets[1].get_received() == []
    assert sockets[2].get_received() == []
    assert sockets[4].get_received()[0]['name'] == 'campaign_content_changed'


def test_local_mode_ignores_lists_but_preserves_ownership_and_membership(setup):
    app, client = setup
    app.config.update(LOCAL_FEATURE_ACCESS=True, FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    entry_id = create_entry(client)
    assert client.get('/articles/tables').status_code == 200
    assert client.get('/campaigns/').status_code == 200
    assert 'Party 2' in client.get(f'/materials/{entry_id}/reveal').text
    login(client, 3)
    assert client.get(f'/materials/{entry_id}/edit').status_code == 403
    assert client.get('/party/1/materials/').status_code == 403


def test_local_mode_ignores_even_invalid_lists(monkeypatch):
    monkeypatch.setenv('LOCAL_FEATURE_ACCESS', 'True')
    monkeypatch.setenv('FEATURE_TEST_USER_IDS', '*')
    monkeypatch.setenv('FEATURE_TEST_PARTY_IDS', 'invalid')
    app = Flask(__name__)
    init_feature_access(app)
    assert app.config['LOCAL_FEATURE_ACCESS'] is True

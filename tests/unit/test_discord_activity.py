"""The party whiteboard as a Discord Activity (#423): sign-in, scoped tokens, CSP-clean pages."""
import json
import re
import time
from unittest.mock import patch

import pytest

from app import socketio
from app.models import DiscordAccount, DiscordChannel, Party, PartyMap, db
from test_shared_map import shared, DRAWING, URL  # noqa: F401 (fixture)


@pytest.fixture
def activity(shared):
    app, clients, sockets = shared
    app.config.update(DISCORD_APPLICATION_ID='900', DISCORD_PUBLIC_KEY='00' * 32,
                      DISCORD_CLIENT_SECRET='secret', DISCORD_BASE_URL='https://kw.example')
    with app.app_context():
        db.session.add_all([DiscordAccount(user_id=1, discord_id='1001', display_name='Warden'),
                            DiscordAccount(user_id=2, discord_id='1002', display_name='Player'),
                            DiscordAccount(user_id=3, discord_id='1003', display_name='Outsider'),
                            DiscordChannel(guild_id='10', channel_id='20', party_id=1, linked_by=1)])
        db.session.commit()
    return app, clients, sockets


def issue(app, kind, user=2, party=1, discord='1002', csrf=None):
    from app.lib.activity import issue as make
    with app.app_context():
        return make(kind, user, party, discord, csrf)


def page_config(html):
    return json.loads(re.search(r'id="shared-map-config" type="application/json">(.*?)</script>', html, re.S)[1])


def executable_scripts(html):
    """Inline scripts Discord's CSP would refuse: anything but JSON data blocks or external files."""
    scripts = re.findall(r'<script([^>]*)>(.*?)</script>', html, re.S)
    return [attrs for attrs, body in scripts if 'src=' not in attrs and 'application/json' not in attrs]


class Discord:
    """Stands in for Discord's OAuth token and identity endpoints."""
    def __init__(self, discord_id='1002', fail=False):
        self.discord_id, self.fail, self.calls = discord_id, fail, []

    def post(self, url, data=None, timeout=None):
        self.calls.append(('post', url, data))
        return self.Response({'access_token': 'access'}, self.fail)

    def get(self, url, headers=None, timeout=None):
        self.calls.append(('get', url, headers))
        return self.Response({'id': self.discord_id})

    class Response:
        def __init__(self, data, fail=False):
            self.data, self.fail = data, fail

        def raise_for_status(self):
            if self.fail:
                import requests
                raise requests.HTTPError('denied')

        def json(self):
            return self.data


def exchange(app, monkeypatch, discord=None, **body):
    discord = discord or Discord()
    monkeypatch.setattr('app.blueprints.activity.requests.post', discord.post)
    monkeypatch.setattr('app.blueprints.activity.requests.get', discord.get)
    payload = {'code': 'code', 'guild_id': '10', 'channel_id': '20', **body}
    return app.test_client().post('/activity/token', json=payload), discord


def test_discord_launch_opens_the_activity_page(activity):
    app, _, _ = activity
    client = app.test_client()
    launched = client.get('/?frame_id=f&instance_id=i&platform=desktop&guild_id=10&channel_id=20')
    assert launched.status_code == 302
    assert launched.location.startswith('/activity?') and 'frame_id=f' in launched.location
    page = client.get(launched.location)
    assert page.status_code == 200 and page.headers['Cache-Control'] == 'no-store'
    html = page.get_data(as_text=True)
    assert executable_scripts(html) == []
    assert '"clientId": "900"' in html and '/activity/static/src/js/activity/launch.js' in html
    # A normal visit to the site is unchanged.
    assert client.get('/').location.endswith('/login')


def test_activity_is_off_without_discord(app):
    assert app.test_client().get('/activity').status_code == 404
    assert app.test_client().post('/activity/token', json={}).status_code == 404


def test_code_exchange_opens_the_channels_party_for_a_member(activity, monkeypatch):
    app, _, _ = activity
    response, discord = exchange(app, monkeypatch)
    assert response.status_code == 200 and response.headers['Cache-Control'] == 'no-store'
    assert response.json['party'] == 'Party'
    assert response.json['board'].startswith('/activity/board/1?ticket=')
    # Only the code goes to Discord, with the app's secret; no redirect URI for an Activity.
    assert discord.calls[0][2] == {'client_id': '900', 'client_secret': 'secret',
                                   'grant_type': 'authorization_code', 'code': 'code'}
    assert discord.calls[1][2] == {'Authorization': 'Bearer access'}
    # The Discord access token never reaches the page.
    assert 'access' not in response.get_data(as_text=True)


@pytest.mark.parametrize('discord_id, body, reason', [
    ('9999', {}, 'not_linked'),
    ('1003', {}, 'not_member'),
    ('1002', {'channel_id': '21'}, 'not_bound'),
])
def test_code_exchange_explains_why_it_cannot_open(activity, monkeypatch, discord_id, body, reason):
    app, _, _ = activity
    response, _ = exchange(app, monkeypatch, Discord(discord_id), **body)
    assert response.status_code == 403 and response.json['reason'] == reason
    assert response.json['message'] and 'board' not in response.json
    if reason == 'not_linked':
        assert response.json['link'] == 'https://kw.example/account/discord'


def test_code_exchange_rejects_bad_input_and_failed_sign_in(activity, monkeypatch):
    app, _, _ = activity
    for body in ({'code': ''}, {'guild_id': 'x'}, {'channel_id': None}):
        response, discord = exchange(app, monkeypatch, **body)
        assert response.status_code == 400 and discord.calls == []
    response, _ = exchange(app, monkeypatch, Discord(fail=True))
    assert response.status_code == 502 and response.json['reason'] == 'discord'


def test_binding_from_a_former_warden_does_not_open(activity, monkeypatch):
    app, _, _ = activity
    with app.app_context():
        db.session.get(Party, 1).owner = 4
        db.session.commit()
    response, _ = exchange(app, monkeypatch)
    assert response.json['reason'] == 'not_bound'


def test_board_page_needs_a_valid_ticket_for_its_party(activity):
    app, _, _ = activity
    client = app.test_client()
    ticket = issue(app, 'ticket')
    page = client.get(f'/activity/board/1?ticket={ticket}')
    assert page.status_code == 200 and page.headers['Referrer-Policy'] == 'no-referrer'
    html = page.get_data(as_text=True)
    config = page_config(html)
    assert config['activityToken'] and config['partyId'] == 1 and config['warden'] is False
    # Discord's CSP: no inline script, nothing loaded from other sites.
    assert executable_scripts(html) == []
    assert not re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', html)
    assert 'class=" in-activity"' in html
    assert client.get('/activity/board/1').status_code == 302
    assert client.get('/activity/board/1?ticket=nonsense').status_code == 302
    assert client.get(f'/activity/board/2?ticket={ticket}').status_code == 302
    # A session token is not a ticket.
    assert client.get(f'/activity/board/1?ticket={config["activityToken"]}').status_code == 302
    with patch('itsdangerous.timed.time.time', return_value=time.time() + 300):
        assert client.get(f'/activity/board/1?ticket={ticket}').status_code == 302


def test_board_token_works_without_cookies_for_its_board_only(activity):
    app, _, _ = activity
    ticket = issue(app, 'ticket')
    client = app.test_client()
    config = page_config(client.get(f'/activity/board/1?ticket={ticket}').get_data(as_text=True))
    bearer = {'Authorization': 'Bearer ' + config['activityToken']}
    fresh = app.test_client()  # no session cookie at all
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        read = fresh.get(URL, headers=bearer)
        assert read.status_code == 200 and read.headers['X-CSRF-Token']
        saved = fresh.post(URL, headers=bearer, json={'version': 0, 'drawing': DRAWING, 'csrf_token': config['csrfToken']})
        assert saved.status_code == 200
        # The CSRF token still has to match the one made for this board.
        forged = fresh.post(URL, headers=bearer, json={'version': 1, 'drawing': DRAWING, 'csrf_token': 'forged'})
        assert forged.status_code == 400
        assert fresh.get('/party/1/shared-map/tokens', headers=bearer).status_code == 200
    finally:
        app.config['WTF_CSRF_ENABLED'] = False
    # Never another party's board, nor the rest of the site.
    assert fresh.get('/party/2/shared-map/scene', headers=bearer).status_code == 302
    assert fresh.get('/account/discord', headers=bearer).get_data(as_text=True).count('Disconnect') == 0
    assert fresh.get('/party/1/shared-map', headers=bearer).status_code == 302
    assert fresh.get(URL).status_code == 302
    # A ticket is not a session token.
    assert fresh.get(URL, headers={'Authorization': 'Bearer ' + ticket}).status_code == 302


def test_disconnecting_discord_or_leaving_the_party_closes_the_board(activity):
    app, _, _ = activity
    bearer = {'Authorization': 'Bearer ' + issue(app, 'session')}
    client = app.test_client()
    assert client.get(URL, headers=bearer).status_code == 200
    with app.app_context():
        from app.models import Character
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert client.get(URL, headers=bearer).status_code == 403
    with app.app_context():
        db.session.delete(db.session.get(DiscordAccount, 2))
        db.session.add(DiscordAccount(user_id=2, discord_id='2002', display_name='Relinked'))
        db.session.commit()
    assert client.get(URL, headers=bearer).status_code == 302


def test_warden_rolls_need_the_tokens_party(activity):
    app, _, _ = activity
    bearer = {'Authorization': 'Bearer ' + issue(app, 'session', user=1, discord='1001')}
    client = app.test_client()
    rolled = client.post('/warden/roll', headers=bearer, data={'party_id': '1', 'kind': 'fate'})
    assert rolled.status_code == 200 and 'Die of Fate' in rolled.json['result']
    assert client.post('/warden/roll', headers=bearer, data={'party_id': '2', 'kind': 'fate'}).status_code == 302
    assert client.post('/warden/roll', headers=bearer, data={'kind': 'fate'}).status_code == 302


def test_activity_socket_signs_in_with_its_token(activity):
    app, _, sockets = activity
    token = issue(app, 'session')
    csrf_page = page_config(app.test_client().get(f'/activity/board/1?ticket={issue(app, "ticket")}').get_data(as_text=True))
    assert socketio.test_client(app, auth={'activity': 'nonsense'}).is_connected() is False
    assert socketio.test_client(app).is_connected() is False
    player = socketio.test_client(app, auth={'activity': csrf_page['activityToken']})
    assert player.is_connected()
    for socket in sockets.values():
        socket.get_received()
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        packet = {'party_id': 1, 'generation': 1, 'pointer': {'x': 1, 'y': 2, 'tool': 'laser'}, 'button': 'down',
                  'csrf_token': csrf_page['csrfToken']}
        player.emit('whiteboard_laser', packet)
        received = sockets[1].get_received()
        assert [event['name'] for event in received] == ['whiteboard_laser']
        assert received[0]['args'][0]['username'] == 'map2'
        player.emit('whiteboard_laser', {**packet, 'party_id': 2})
        assert sockets[4].get_received() == []
    finally:
        app.config['WTF_CSRF_ENABLED'] = False
    # The board rolls over HTTP; dice from other pages stay closed to an Activity's socket.
    assert not player.emit('roll_dice', {'character_id': 1, 'party_id': 1, 'dice': 'd6'}, callback=True)
    with app.app_context():
        from app.models import PartyRoll
        assert PartyRoll.query.count() == 0
    player.disconnect()
    assert token


def test_esm_paths_go_to_the_esm_mapping(activity):
    app, _, _ = activity
    client = app.test_client()
    for path, target in [
        ('/react@18.3.1', '/esm/react@18.3.1'),
        ('/react-dom@18.3.1/X-ZHJl/es2022/client.mjs', '/esm/react-dom@18.3.1/X-ZHJl/es2022/client.mjs'),
        ('/scheduler@%5E0.23.2?target=es2022', '/esm/scheduler@%5E0.23.2?target=es2022'),
        ('/@excalidraw/excalidraw@0.18.0/dist/prod/index.js?deps=react@18.3.1',
         '/esm/@excalidraw/excalidraw@0.18.0/dist/prod/index.js?deps=react@18.3.1'),
        ('/node/process.mjs', '/esm/node/process.mjs'),
    ]:
        response = client.get(path)
        assert response.status_code == 301, path
        assert response.location == target
        assert 'immutable' in response.headers['Cache-Control']
    assert client.get('/node/anything').status_code == 404
    assert client.get('/static/src/css/shared_map.css').status_code == 200


def test_activity_modules_import_esm_paths_instead_of_the_import_map(activity):
    from app.lib.activity import ESM_IMPORTS, rewrite_imports
    app, _, _ = activity
    client = app.test_client()
    source = client.get('/activity/static/src/js/maps/shared_map.js').get_data(as_text=True)
    assert "from 'excalidraw'" not in source and "from 'react'" not in source
    assert f"from '{ESM_IMPORTS['excalidraw']}'" in source and f"from '{ESM_IMPORTS['react-dom/client']}'" in source
    assert rewrite_imports("import {x} from \"react\";\nimport('excalidraw')") == (
        f"import {{x}} from \"{ESM_IMPORTS['react']}\";\nimport('{ESM_IMPORTS['excalidraw']}')")
    assert rewrite_imports("from 'reactive'; from './react.js'") == "from 'reactive'; from './react.js'"
    # Other static files are served as they are; nothing outside the static folder.
    assert client.get('/activity/static/src/css/shared_map.css').status_code == 200
    assert client.get('/activity/static/src/js/../../../../wsgi.py').status_code == 404
    assert client.get('/activity/static/src/js/missing.js').status_code == 404


SHEET = '/party/1/shared-map/sheets'


@pytest.fixture
def hero(activity):
    app, clients, sockets = activity
    with app.app_context():
        from app.models import Character
        character = db.session.get(Character, 1)
        character.hp, character.hp_max, character.willpower, character.willpower_max = 4, 6, 8, 9
        character.containers = json.dumps([{'id': 0, 'name': 'Main', 'slots': 10}, {'id': 1, 'name': 'Backpack', 'slots': 6}])
        character.items = json.dumps([
            {'id': 1, 'name': 'Torch', 'tags': ['uses'], 'uses': 1, 'max_uses': 3, 'location': 0},
            {'id': 2, 'name': 'Tent', 'tags': ['bulky'], 'location': 1},
            {'id': 3, 'name': 'Rope', 'tags': [], 'location': 0}])
        db.session.commit()
    return app, clients, sockets


def item(container, name):
    return next(entry for entry in container['items'] if entry['name'] == name)


def change(client, headers=None, character=1, **body):
    return client.post(f'{SHEET}/{character}', headers=headers or {}, json=body)


def test_compact_sheet_shows_your_characters_only(hero):
    app, clients, _ = hero
    mine = clients[2].get(SHEET)
    assert mine.status_code == 200 and mine.headers['Cache-Control'] == 'no-store'
    (sheet,) = mine.json['characters']
    assert sheet['hp'] == {'value': 4, 'stored': 4, 'max': 6} and sheet['willpower'] == {'value': 8, 'max': 9}
    main, backpack = sheet['containers']
    assert (main['name'], main['used'], main['slots']) == ('Main', 2, 10)
    assert (backpack['used'], backpack['items'][0]['bulky']) == (2, True)
    assert item(main, 'Torch') == {'id': 1, 'name': 'Torch', 'fatigue': False, 'bulky': False, 'petty': False,
                                'uses': 1, 'max_uses': 3}
    # The Warden has no character here, and nobody sees someone else's inventory.
    assert clients[1].get(SHEET).json == {'characters': []}
    assert clients[3].get(SHEET).status_code == 403
    assert change(clients[1], action='stat', stat='hp', value=-1).status_code == 403


def test_compact_sheet_changes_use_the_kw_rules(hero):
    app, clients, _ = hero
    player = clients[2]
    assert change(player, action='stat', stat='hp', value=-1).json['hp']['stored'] == 3
    refused = change(player, action='stat', stat='wil', value=2)
    assert refused.status_code == 400 and refused.json['reason'] == 'invalid' and 'between 0 and 9' in refused.json['message']
    assert change(player, action='condition', condition='panicked', active=True).json['hp']['value'] == 0
    sheet = change(player, action='fatigue', amount=1).json
    fatigue = next(i for i in sheet['containers'][0]['items'] if i['fatigue'])
    assert sheet['containers'][0]['used'] == 3
    used = change(player, action='use', item=1, resource='uses').json
    assert item(used['containers'][0], 'Torch')['uses'] == 0  # an empty Torch stays on the sheet
    assert change(player, action='use', item=1, resource='uses').json['reason'] == 'invalid'
    # Only Fatigue is removed here; other items are removed on the full sheet.
    assert change(player, action='remove', item=3).json['message'] == 'Only Fatigue can be cleared here.'
    cleared = change(player, action='remove', item=fatigue['id']).json
    assert not any(i['fatigue'] for i in cleared['containers'][0]['items'])
    for body in ({'action': 'drop', 'item': 1, 'place': 'here'}, {'action': 'note', 'text': 'x'}, {}):
        assert change(player, **body).json['message'] == 'Unknown action.'


def test_compact_sheet_works_in_the_activity_and_needs_csrf(hero):
    app, _, _ = hero
    config = page_config(app.test_client().get(f'/activity/board/1?ticket={issue(app, "ticket")}').get_data(as_text=True))
    assert config['sheetsUrl'] == SHEET
    bearer = {'Authorization': 'Bearer ' + config['activityToken']}
    client = app.test_client()
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        assert client.get(SHEET, headers=bearer).json['characters'][0]['name'] == 'Player'
        assert change(client, bearer, action='stat', stat='hp', value=-1).json['reason'] == 'csrf'
        saved = change(client, bearer, action='stat', stat='hp', value=-1, csrf_token=config['csrfToken'])
        assert saved.status_code == 200 and saved.json['hp']['stored'] == 3
    finally:
        app.config['WTF_CSRF_ENABLED'] = False
    # The button and dialog are only on the Activity's board, for players with a character.
    site = hero[1][2].get('/party/1/shared-map').get_data(as_text=True)
    assert 'id="board-sheet"' not in site and page_config(site)['sheetsUrl'] is None
    warden = app.test_client().get(f'/activity/board/1?ticket={issue(app, "ticket", user=1, discord="1001")}').get_data(as_text=True)
    assert 'id="board-sheet"' not in warden

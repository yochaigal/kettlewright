import itertools
import json
import time
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock

import pytest
from nacl.signing import SigningKey

from app import socketio
from app.lib.character_rolls import parse_dice
from app.models import (Character, DiscordAccount, DiscordChannel, DiscordInteraction,
                        DiscordSelection, Party, PartyRoll, User, db)


@pytest.fixture
def game(app_with_babel):
    app = app_with_babel
    signing_key = SigningKey.generate()
    app.config.update(DISCORD_APPLICATION_ID='900', DISCORD_PUBLIC_KEY=signing_key.verify_key.encode().hex(),
                      DISCORD_CLIENT_SECRET='test-client-secret', DISCORD_BASE_URL='https://kw.example')
    with app.app_context():
        db.session.add_all([User(id=1, username='player'), User(id=2, username='other'), User(id=3, username='warden')])
        db.session.add_all([DiscordAccount(user_id=i, discord_id=str(i + 100), display_name=str(i)) for i in (1, 2, 3)])
        db.session.add_all([Party(id=1, owner=3, name='Party', party_url='party', members='[1, 2, 3]'),
                            Party(id=2, owner=2, name='Other party', members='[4]')])
        db.session.add_all([Character(id=i, owner=1 if i < 3 else 2, name=name, background='Test',
                            url_name=name.lower(), party_id=1 if i < 4 else 2, hp=5, hp_max=6,
                            strength=12, strength_max=14, dexterity=9, dexterity_max=9,
                            willpower=8, willpower_max=8, items='[]')
                            for i, name in enumerate(['Bran', 'Ada', 'Other', 'Far away'], 1)])
        db.session.add(DiscordChannel(guild_id='10', channel_id='20', party_id=1, linked_by=3))
        db.session.commit()
    return app, signing_key


ids = itertools.count(1000)


def command(game, name, user=101, channel='20', guild='10', kind=2, permissions='0', interaction_id=None, **options):
    app, key = game
    payload = dict(id=str(interaction_id or next(ids)), application_id='900', type=kind, guild_id=guild,
                   channel_id=channel, member=dict(user=dict(id=str(user)), permissions=permissions),
                   data=dict(name='kw', options=[dict(name=name, type=1, options=[
                       dict(name=k, value=v, type=3) for k, v in options.items()])]))
    return signed(app, key, payload)


def signed(app, key, payload, timestamp=None, **headers):
    body = json.dumps(payload).encode()
    timestamp = str(timestamp if timestamp is not None else int(time.time()))
    signature = key.sign(timestamp.encode() + body).signature.hex()
    return app.test_client().post('/discord/interactions', data=body, content_type='application/json', headers={
        'X-Signature-Timestamp': timestamp, 'X-Signature-Ed25519': signature, **headers})


def content(response):
    assert response.status_code == 200
    return response.json['data']['content']


def logged_in(app, user=1):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(user)
        session['_fresh'] = True
    return client


def test_ping_signature_and_freshness(game):
    app, key = game
    ping = dict(application_id='900', type=1)
    assert signed(app, key, ping).json == {'type': 1}
    assert signed(app, key, ping, **{'X-Signature-Ed25519': '00' * 64}).status_code == 401
    assert signed(app, key, ping, timestamp=int(time.time()) - 301).status_code == 401
    assert signed(app, key, ping, timestamp=int(time.time()) + 301).status_code == 401
    assert signed(app, key, dict(application_id='901', type=1)).status_code == 400
    assert signed(app, key, []).status_code == 400
    assert app.test_client().post('/discord/interactions', json=ping).status_code == 401


def test_disabled_endpoint(app):
    assert app.test_client().post('/discord/interactions', json={}).status_code == 503


def test_select_then_roll_and_switch_character(game, monkeypatch):
    app, _ = game
    monkeypatch.setattr('app.lib.character_rolls.secrets.randbelow', lambda sides: sides - 1)
    assert '/kw select' in content(command(game, 'roll', dice='d20'))
    assert 'Bran' in content(command(game, 'select', character='Bran'))
    response = command(game, 'roll', dice='d6+d8')
    assert 'Bran' in content(response) and '6, 8 (d6+d8)' in content(response)
    assert 'flags' not in response.json['data']
    assert response.json['data']['allowed_mentions'] == {'parse': []}
    assert 'Ada' in content(command(game, 'select', character='2'))
    assert 'Ada' in content(command(game, 'roll', dice='2d6'))
    with app.app_context():
        assert [r.character_name for r in PartyRoll.query.order_by(PartyRoll.id)] == ['Bran', 'Ada']


@pytest.mark.parametrize('user,character', [(101, '3'), (103, '1'), (102, '1'), (101, '4')])
def test_only_owner_can_select_even_warden(game, user, character):
    response = command(game, 'select', user=user, character=character)
    assert response.json['data']['flags'] == 64
    assert 'Selected' not in content(response)
    with game[0].app_context():
        assert DiscordSelection.query.count() == 0
        assert PartyRoll.query.count() == 0


def test_selection_is_personal_and_scoped_to_channel_and_guild(game):
    app, _ = game
    with app.app_context():
        db.session.add_all([DiscordChannel(guild_id='10', channel_id='21', party_id=1, linked_by=3),
                            DiscordChannel(guild_id='11', channel_id='20', party_id=1, linked_by=3)])
        db.session.commit()
    command(game, 'select', character='1')
    assert '/kw select' in content(command(game, 'character', user=102))
    assert '/kw select' in content(command(game, 'character', channel='21'))
    assert '/kw select' in content(command(game, 'character', guild='11'))
    command(game, 'select', channel='21', character='2')
    assert 'Bran' in content(command(game, 'character'))
    assert 'Ada' in content(command(game, 'character', channel='21'))


@pytest.mark.parametrize('change', ['owner', 'party_id', 'members', 'delete', 'unlink', 'warden_unlink', 'party_owner'])
def test_stale_selection_never_grants_roll_access(game, change):
    app, _ = game
    command(game, 'select', character='1')
    with app.app_context():
        character = db.session.get(Character, 1)
        if change == 'owner':
            character.owner = 2
        elif change == 'party_id':
            character.party_id = 2
        elif change == 'members':
            db.session.get(Party, 1).members = '[2, 3]'
        elif change == 'delete':
            db.session.delete(character)
        elif change == 'unlink':
            db.session.delete(db.session.get(DiscordAccount, 1))
        elif change == 'warden_unlink':
            db.session.delete(db.session.get(DiscordAccount, 3))
        else:
            db.session.get(Party, 1).owner = 2
        db.session.commit()
    assert command(game, 'roll', dice='d20').json['data']['flags'] == 64
    with app.app_context():
        assert PartyRoll.query.count() == 0


def test_duplicate_interaction_reuses_result_and_does_not_broadcast_twice(game):
    app, _ = game
    socket = socketio.test_client(app, flask_test_client=logged_in(app, 3))
    command(game, 'select', character='1')
    first = command(game, 'roll', dice='d20', interaction_id='123456')
    assert [event['name'] for event in socket.get_received()] == ['dice_rolled', 'roll_history_changed']
    second = command(game, 'roll', dice='d20', interaction_id='123456')
    assert first.json == second.json
    assert socket.get_received() == []
    with app.app_context():
        assert PartyRoll.query.count() == 1
    socket.disconnect()


def test_autocomplete_returns_only_own_party_characters(game):
    choices = command(game, 'select', kind=4, character='').json['data']['choices']
    assert [c['value'] for c in choices] == ['1', '2']
    assert command(game, 'select', user=103, kind=4, character='').json['data']['choices'] == []
    assert command(game, 'select', user=999, kind=4, character='').json['data']['choices'] == []


def test_bind_needs_both_kw_ownership_and_discord_permission(game):
    assert 'Manage Channels' in content(command(game, 'bind', user=103, party='1', channel='21'))
    assert 'matching entry' in content(command(game, 'bind', user=101, party='1', channel='21', permissions='16'))
    assert 'Bound to' in content(command(game, 'bind', user=103, party='1', channel='21', permissions='16'))
    assert 'current party' in content(command(game, 'bind', user=102, party='2', channel='21', permissions='8'))
    command(game, 'select', character='1', channel='21')
    assert 'unbound' in content(command(game, 'unbind', user=103, channel='21', permissions='16'))
    with game[0].app_context():
        assert db.session.get(DiscordChannel, ('10', '21')) is None
        assert DiscordSelection.query.filter_by(channel_id='21').count() == 0


def test_party_roster_and_character_use_live_stats_without_notes(game):
    app, _ = game
    with app.app_context():
        db.session.get(Party, 1).notes = 'private party note'
        c = db.session.get(Character, 1)
        c.notes, c.panicked = 'private character note', True
        db.session.commit()
    assert 'Bran' in content(command(game, 'party', user=103))
    assert 'private' not in content(command(game, 'party'))
    command(game, 'select', character='1')
    card = content(command(game, 'character'))
    assert 'HP 0/6' in card and 'Panicked' in card and '/users/player/characters/bran/' in card
    assert 'private' not in card
    assert 'between 1 and' in content(command(game, 'party', page=99))


def test_duplicate_names_use_autocomplete_ids(game):
    with game[0].app_context():
        db.session.get(Character, 2).name = 'Bran'
        db.session.commit()
    assert 'names may not be unique' in content(command(game, 'select', character='Bran'))
    assert 'Selected' in content(command(game, 'select', character='2'))


@pytest.mark.parametrize('dice', ['0d6', '3d6', 'd0', 'd7', 'd6+d6+d6', '999999d6', '<script>', None, 20])
def test_invalid_dice_do_not_create_rolls(game, dice):
    command(game, 'select', character='1')
    assert command(game, 'roll', dice=dice).json['data']['flags'] == 64
    with game[0].app_context():
        assert PartyRoll.query.count() == 0


@pytest.mark.parametrize('dice,expected', [('d20', [20]), ('2d6', [6, 6]), ('d6+d8', [6, 8]), (' D100 ', [100])])
def test_dice_parser(dice, expected):
    assert parse_dice(dice) == expected


def test_oauth_state_links_verified_identity_and_disconnect_clears_context(game, monkeypatch):
    app, _ = game
    client = logged_in(app)
    command(game, 'select', character='1')
    client.post('/account/discord', data={'action': 'disconnect'})
    with app.app_context():
        assert DiscordSelection.query.count() == 0
    response = client.post('/account/discord', data={'action': 'connect'})
    query = parse_qs(urlparse(response.location).query)
    assert query['scope'] == ['identify']
    assert query['redirect_uri'] == ['https://kw.example/account/discord/callback']
    post, get = Mock(), Mock()
    post.return_value.json.return_value = {'access_token': 'ephemeral-token'}
    get.return_value.json.return_value = {'id': '105', 'username': 'verified'}
    monkeypatch.setattr('app.blueprints.discord.requests.post', post)
    monkeypatch.setattr('app.blueprints.discord.requests.get', get)
    callback = '/account/discord/callback?code=code&state=' + query['state'][0]
    assert client.get(callback).status_code == 302
    assert get.call_args.kwargs['headers'] == {'Authorization': 'Bearer ephemeral-token'}
    with app.app_context():
        assert db.session.get(DiscordAccount, 1).discord_id == '105'
    assert client.get(callback).status_code == 400


def test_oauth_rejects_wrong_state_and_existing_discord_owner(game, monkeypatch):
    app, _ = game
    client = logged_in(app)
    client.post('/account/discord', data={'action': 'disconnect'})
    client.post('/account/discord', data={'action': 'connect'})
    post = Mock()
    monkeypatch.setattr('app.blueprints.discord.requests.post', post)
    assert client.get('/account/discord/callback?state=wrong&code=code').status_code == 400
    post.assert_not_called()
    response = client.post('/account/discord', data={'action': 'connect'})
    state = parse_qs(urlparse(response.location).query)['state'][0]
    post.return_value.json.return_value = {'access_token': 'temporary'}
    get = Mock()
    get.return_value.json.return_value = {'id': '102', 'username': 'other'}
    monkeypatch.setattr('app.blueprints.discord.requests.get', get)
    assert client.get('/account/discord/callback?state=' + state + '&code=code').status_code == 302
    with app.app_context():
        assert db.session.get(DiscordAccount, 1) is None
        assert db.session.get(DiscordAccount, 2).discord_id == '102'


def test_settings_csrf_and_warden_disconnect(game):
    app, _ = game
    client = logged_in(app, 3)
    assert client.get('/account/discord').status_code == 200
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/account/discord', data={'action': 'disconnect'}).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = False
    assert client.post('/account/discord', data={'action': 'disconnect'}).status_code == 302
    with app.app_context():
        assert DiscordChannel.query.count() == 0


def test_cli_dry_run_never_contacts_discord(game, monkeypatch):
    post = Mock()
    monkeypatch.setattr('app.blueprints.discord.requests.post', post)
    result = game[0].test_cli_runner().invoke(args=['discord', 'register', '--dry-run'])
    assert result.exit_code == 0
    assert json.loads(result.output)['name'] == 'kw'
    post.assert_not_called()


def test_user_deletion_cleans_identity_and_context(game):
    app, _ = game
    command(game, 'select', character='1')
    with app.app_context():
        db.session.delete(db.session.get(User, 1))
        db.session.commit()
        assert db.session.get(DiscordAccount, 1) is None
        assert DiscordSelection.query.filter_by(user_id=1).count() == 0
    assert 'Connect your' in content(command(game, 'roll', dice='d20'))


def test_rate_limit_does_not_roll_or_break_autocomplete(game, monkeypatch):
    app, _ = game
    command(game, 'select', character='1')
    limiter = app.extensions['discord_limiter']
    monkeypatch.setattr(limiter, 'allow', lambda *args: False)
    assert 'Too many' in content(command(game, 'roll', dice='d20'))
    assert command(game, 'select', kind=4, character='').json == {'type': 8, 'data': {'choices': []}}
    with app.app_context():
        assert PartyRoll.query.count() == 0
    monkeypatch.setattr(limiter, 'allow', Mock(side_effect=ConnectionError))
    assert 'temporarily unavailable' in content(command(game, 'roll', dice='d20'))
    assert command(game, 'select', kind=4, character='').json == {'type': 8, 'data': {'choices': []}}

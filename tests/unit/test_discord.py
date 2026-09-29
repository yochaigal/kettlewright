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
                            willpower=8, willpower_max=8, items='[]',
                            containers='[{"id": 0, "name": "Main", "slots": 10}]')
                            for i, name in enumerate(['Bran', 'Ada', 'Other', 'Far away'], 1)])
        db.session.add(DiscordChannel(guild_id='10', channel_id='20', party_id=1, linked_by=3))
        db.session.commit()
    return app, signing_key


ids = itertools.count(1000)


def command(game, subcommand, user=101, channel='20', guild='10', kind=2, permissions='0', interaction_id=None, focused=None, **options):
    app, key = game
    payload = dict(id=str(interaction_id or next(ids)), application_id='900', type=kind, guild_id=guild,
                   channel_id=channel, member=dict(user=dict(id=str(user)), permissions=permissions),
                   data=dict(name='kw', options=[dict(name=subcommand, type=1, options=[
                       dict(name=k, value=v, type=3, focused=k == focused) for k, v in options.items()])]))
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


def test_public_discord_guide_and_account_actions_require_login(app_with_babel):
    client = app_with_babel.test_client()
    page = client.get('/account/discord')
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'id="discord-toggle"' in html
    assert 'https://discord.gg/T5Ykgw74DF' in html
    assert 'https://discord.com/oauth2/authorize?client_id=1553017013016723556' in html
    for command in ('login', 'bind', 'unbind', 'select', 'character', 'party', 'roll'):
        assert '/kw ' + command in html
    assert 'name="action" value="connect"' not in html
    assert 'name="action" value="disconnect"' not in html
    assert client.post('/account/discord', data={'action': 'connect'}).status_code == 302


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


def button(game, custom_id, user=101, interaction_id=None, channel='20'):
    app, key = game
    return signed(app, key, dict(id=str(interaction_id or next(ids)), application_id='900', type=3,
        guild_id='10', channel_id=channel, member=dict(user=dict(id=str(user))),
        data=dict(component_type=2, custom_id=custom_id)))


def stored_character(game, character_id=1):
    with game[0].app_context():
        c = db.session.get(Character, character_id)
        return dict(hp=c.hp, strength=c.strength, dexterity=c.dexterity, willpower=c.willpower,
                    deprived=c.deprived, panicked=c.panicked, notes=c.notes,
                    items=json.loads(c.items), containers=json.loads(c.containers))


def test_mobile_dice_panel_uses_same_roll_history_and_deduplicates(game):
    command(game, 'select', character='1')
    panel = command(game, 'roll').json['data']
    assert panel['flags'] == 64
    buttons = [b for row in panel['components'] for b in row['components']]
    assert [b['label'] for b in buttons] == ['d4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100', '2d6']
    first = button(game, buttons[5]['custom_id'], interaction_id='987654')
    assert 'Bran' in content(first) and '(d20)' in content(first)
    assert 'flags' not in first.json['data']
    assert button(game, buttons[5]['custom_id'], interaction_id='987654').json == first.json
    with game[0].app_context():
        assert PartyRoll.query.count() == 1


def test_dice_buttons_cannot_roll_another_or_stale_selection(game):
    command(game, 'select', character='1')
    command(game, 'select', user=102, character='3')
    assert 'another selection' in content(button(game, 'kw:roll:1:1:d20', user=102))
    command(game, 'select', character='2')
    assert 'another selection' in content(button(game, 'kw:roll:1:1:d20'))
    assert 'Unknown button' in content(button(game, 'kw:roll:1:2:d7'))
    with game[0].app_context():
        db.session.get(Character, 2).owner = 2
        db.session.commit()
    assert '/kw select' in content(button(game, 'kw:roll:1:2:d20'))
    with game[0].app_context():
        assert PartyRoll.query.count() == 0


def test_player_stats_conditions_and_private_notes(game):
    command(game, 'select', character='1')
    result = command(game, 'stat', stat='hp', value=-2, interaction_id='88001')
    assert '5 → 3/6' in content(result)
    assert result.json['data']['flags'] == 64
    assert command(game, 'stat', stat='hp', value=-2, interaction_id='88001').json == result.json
    assert stored_character(game)['hp'] == 3
    assert '12 → 7/14' in content(command(game, 'stat', stat='str', value=7, mode='set'))
    assert 'No changes' in content(command(game, 'stat', stat='hp', value=-99))
    assert stored_character(game)['hp'] == 3
    assert 'Effective HP: 0' in content(command(game, 'condition', condition='panicked', active=True))
    assert stored_character(game)['hp'] == 3
    command(game, 'condition', condition='panicked', active=False)
    command(game, 'condition', condition='deprived', active=True)
    assert stored_character(game)['deprived'] is True
    for text in ('first note', '<script>alert(1)</script> @everyone'):
        response = command(game, 'note', text=text)
        assert text not in content(response)
        assert response.json['data']['flags'] == 64
    notes = stored_character(game)['notes']
    assert notes.startswith('first note\n') and '<script>' not in notes
    assert 'exceed 2000' in content(command(game, 'note', text='x' * 2000))
    assert stored_character(game)['notes'] == notes


@pytest.mark.parametrize('name,values', [
    ('stat', dict(stat='hp', value=True)), ('stat', dict(stat='owner', value=2)),
    ('stat', dict(stat='hp', value=99, mode='set')),
    ('condition', dict(condition='dead', active=True)),
    ('condition', dict(condition='deprived', active='false')),
    ('fatigue', dict(amount=0)), ('fatigue', dict(amount=1.5)),
    ('add', dict(name='Invalid', tags='petty,bulky')),
])
def test_invalid_player_input_leaves_sheet_unchanged(game, name, values):
    command(game, 'select', character='1')
    before = stored_character(game)
    assert command(game, name, **values).json['data']['flags'] == 64
    assert stored_character(game) == before


def test_fatigue_batch_rollback_and_duplicate_receipt(game):
    command(game, 'select', character='1')
    command(game, 'fatigue', amount=9)
    before = stored_character(game)
    assert 'Nothing was added' in content(command(game, 'fatigue', amount=2))
    assert stored_character(game) == before
    first = command(game, 'fatigue', interaction_id='88002')
    assert command(game, 'fatigue', interaction_id='88002').json == first.json
    assert len(stored_character(game)['items']) == 10
    assert 'HP 0/6' in content(command(game, 'character'))
    fatigue = stored_character(game)['items'][0]['id']
    for action in ('drop', 'move', 'transfer'):
        assert 'Fatigue cannot' in content(command(game, action, item=fatigue, container='0', character='3'))
    command(game, 'remove', item=fatigue)
    assert len(stored_character(game)['items']) == 9


def test_items_uses_charges_remove_and_catalog(game):
    command(game, 'select', character='1')
    assert 'added 1' in content(command(game, 'add', name='Torch', interaction_id='88003'))
    command(game, 'add', name='Torch', interaction_id='88003')
    items = stored_character(game)['items']
    assert len(items) == 1 and items[0]['uses'] > 0 and 'uses' in items[0]['tags']
    uses = items[0]['uses']
    assert 'Nothing was changed' in content(command(game, 'use', item='Torch', amount=uses + 1))
    first = command(game, 'use', item='Torch', interaction_id='88004')
    command(game, 'use', item='Torch', interaction_id='88004')
    assert stored_character(game)['items'][0]['uses'] == uses - 1
    assert stored_character(game)['items'][0]['max_uses'] == uses
    command(game, 'add', name='Wand', charges=2)
    command(game, 'use', item='Wand', resource='charges', amount=2, **{'remove-empty': True})
    assert [i['name'] for i in stored_character(game)['items']] == ['Torch']
    command(game, 'remove', item='Torch')
    assert stored_character(game)['items'] == []


def test_drop_and_pickup_preserve_item_and_reject_full_destination(game):
    command(game, 'select', character='1')
    command(game, 'add', name='Shield')
    original = stored_character(game)['items'][0]
    assert '1–200' in content(command(game, 'drop', item=original['id']))
    assert stored_character(game)['items'][0] == original
    first = command(game, 'drop', item=original['id'], place='Old bridge', interaction_id='88010')
    assert 'on the ground' in content(first)
    assert command(game, 'drop', item=original['id'], place='Old bridge', interaction_id='88010').json == first.json
    assert stored_character(game)['items'] == []
    assert 'Old bridge' in content(command(game, 'ground'))
    command(game, 'fatigue', amount=10)
    assert 'insufficient free slots' in content(command(game, 'pickup', item=original['id']))
    command(game, 'select', user=102, character='3')
    command(game, 'pickup', user=102, item=original['id'])
    restored = stored_character(game, 3)['items'][0]
    assert {k: v for k, v in restored.items() if k != 'slot'} == {k: v for k, v in original.items() if k != 'slot'}
    assert 'No items' in content(command(game, 'ground'))


def test_transfer_is_atomic_and_only_to_current_party_member(game):
    command(game, 'select', character='1')
    command(game, 'add', name='Torch')
    original = stored_character(game)['items'][0]
    assert 'matching entry' in content(command(game, 'transfer', item='Torch', character='4'))
    with game[0].app_context():
        db.session.get(Character, 3).containers = '[{"id":0,"name":"Main","slots":0}]'
        db.session.commit()
    assert 'insufficient free slots' in content(command(game, 'transfer', item='Torch', character='3'))
    assert stored_character(game)['items'][0] == original
    assert stored_character(game, 3)['items'] == []
    with game[0].app_context():
        db.session.get(Character, 3).containers = '[{"id":0,"name":"Main","slots":10}]'
        db.session.commit()
    first = command(game, 'transfer', item='Torch', character='3', interaction_id='88005')
    assert 'gave Torch' in content(first)
    assert command(game, 'transfer', item='Torch', character='3', interaction_id='88005').json == first.json
    assert stored_character(game)['items'] == []
    assert stored_character(game, 3)['items'] == [original]
    assert 'matching entry' in content(command(game, 'remove', item=original['id']))


@pytest.mark.parametrize('name,values', [
    ('stat', dict(stat='hp', value=-1)), ('condition', dict(condition='deprived', active=True)),
    ('fatigue', {}), ('add', dict(name='Torch')), ('note', dict(text='private')),
    ('remove', dict(item='x')), ('use', dict(item='x')), ('drop', dict(item='x')),
    ('transfer', dict(item='x', character='3')), ('move', dict(item='x', container='0')),
    ('pickup', dict(item='x')), ('ground', {}), ('drop-container', dict(container='1', place='Bridge')),
])
def test_every_player_action_rechecks_ownership(game, name, values):
    command(game, 'select', character='1')
    with game[0].app_context():
        db.session.get(Character, 1).owner = 2
        db.session.commit()
    before = stored_character(game)
    assert '/kw select' in content(command(game, name, **values))
    assert stored_character(game) == before


def test_player_mutation_publishes_only_after_outer_commit(game, monkeypatch):
    app, _ = game
    command(game, 'select', character='1')
    emitted = []
    def capture(event, *args, **kwargs):
        if event == 'party_members_changed':
            assert not db.session().in_nested_transaction()
            emitted.append(event)
    monkeypatch.setattr(socketio, 'emit', capture)
    command(game, 'stat', stat='hp', value=-1, interaction_id='88006')
    assert len(emitted) == 3
    command(game, 'stat', stat='hp', value=-1, interaction_id='88006')
    assert len(emitted) == 3
    emitted.clear()
    command(game, 'fatigue', amount=9)
    emitted.clear()
    command(game, 'fatigue', amount=2)
    assert emitted == []


def test_inventory_autocomplete_is_private_scoped_and_unambiguous(game):
    command(game, 'select', character='1')
    command(game, 'add', name='Torch')
    command(game, 'add', name='Torch')
    response = command(game, 'use', kind=4, item='torch', focused='item')
    choices = response.json['data']['choices']
    assert len(choices) == 2 and choices[0]['value'] != choices[1]['value']
    assert 'names may not be unique' in content(command(game, 'remove', item='Torch'))
    assert command(game, 'use', user=102, kind=4, item='', focused='item').json['data']['choices'] == []
    targets = command(game, 'transfer', kind=4, character='', focused='character').json['data']['choices']
    assert [t['value'] for t in targets] == ['2', '3']
    catalog = command(game, 'add', kind=4, name='torch', focused='name').json['data']['choices']
    assert {'name': 'Torch', 'value': 'Torch'} in catalog
    command(game, 'drop', item=choices[0]['value'], place='Old bridge')
    containers = command(game, 'move', kind=4, container='', focused='container').json['data']['choices']
    assert len(containers) == 1
    choices = command(game, 'pickup', kind=4, item='', focused='item').json['data']['choices']
    assert len(choices) == 1 and 'Old bridge' in choices[0]['name']
    with game[0].app_context():
        db.session.get(Party, 1).members = '[2, 3]'
        db.session.commit()
    assert command(game, 'use', kind=4, item='', focused='item').json['data']['choices'] == []
    before = stored_character(game)
    assert '/kw select' in content(command(game, 'fatigue'))
    assert stored_character(game) == before


def test_discord_drop_container_and_pickup_restore_contents(game):
    command(game, 'select', character='1')
    with game[0].app_context():
        c = db.session.get(Character, 1)
        c.containers = '[{"id":0,"name":"Main","slots":10},{"id":2,"name":"Chest","slots":4}]'
        c.items = '[{"id":"torch","name":"Torch","location":2,"tags":["uses"],"uses":3}]'
        db.session.commit()
    choices = command(game, 'drop-container', kind=4, container='', focused='container').json['data']['choices']
    assert [c['value'] for c in choices] == ['2']
    assert 'main inventory' in content(command(game, 'drop-container', container='0', place='Bridge'))
    first = command(game, 'drop-container', container='2', place='Bridge cellar', interaction_id='88011')
    assert 'with its contents' in content(first)
    assert command(game, 'drop-container', container='2', place='Bridge cellar', interaction_id='88011').json == first.json
    assert len(stored_character(game)['containers']) == 1
    assert stored_character(game)['items'] == []
    command(game, 'select', user=102, character='3')
    assert 'Bridge cellar' in content(command(game, 'ground', user=102))
    assert 'picked up' in content(command(game, 'pickup', user=102, item='Chest'))
    assert stored_character(game, 3)['containers'][1]['name'] == 'Chest'
    assert stored_character(game, 3)['items'][0]['uses'] == 3


def test_legacy_item_ids_and_carrying_markers(game):
    command(game, 'select', character='1')
    with game[0].app_context():
        db.session.get(Character, 1).items = json.dumps([
            dict(id=123, name='Old torch', tags=['uses'], uses=1, location=0),
            dict(id='carry', name='Carrying bag', tags=[], carrying=1, location=0)])
        db.session.commit()
    assert 'carrying markers' in content(command(game, 'remove', item='carry'))
    command(game, 'use', item='123', **{'remove-empty': True})
    assert [i['id'] for i in stored_character(game)['items']] == ['carry']

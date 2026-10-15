from io import BytesIO
from copy import deepcopy

import pytest

from app.lib.monsters import parse_monster, monster_catalog
from app.models import Companion, Character, Party, PartyRoll, db
from test_shared_map import shared, DRAWING, URL


def summon(clients):
    response = clients[1].post('/parties/1/monsters', data={'template': 'creeping-vines'})
    assert response.status_code == 302
    return int(response.location.rsplit('/', 1)[1])


def test_cairn_markdown_and_catalog():
    data = parse_monster('---\nlayout: default\n---\n# Vine\n\n8 HP, vines (d4, _blast_)\n\n- **Critical Damage**: Asphyxiation.')
    assert data['hp'] == 8 and data['strength'] == data['dexterity'] == data['willpower'] == 10
    assert data['attack'] == 'vines (d4, _blast_)'
    assert '**Critical Damage**' in data['notes']
    assert len(monster_catalog()) == 145
    for data in monster_catalog().values():
        assert all(type(data[stat]) is int for stat in ('hp', 'strength', 'dexterity', 'willpower', 'armor'))
    for source in ('bad', '# Bad\nno HP', '# Bad\n8 HP, 4 Armor', '# Bad\n8 HP, 9 HP'):
        with pytest.raises(ValueError):
            parse_monster(source)


def test_categorized_portraits_work_for_creation_and_companions(shared):
    from app.lib.data import load_images
    from app.lib.portraits import validate_portrait_reference
    app, clients, _ = shared
    with app.app_context():
        assert all('/' not in path for path in load_images())
        assert len(load_images(include_categories=True)) == len(load_images()) + 298
        validate_portrait_reference('beast/beast1.png', False)
        with pytest.raises(ValueError):
            validate_portrait_reference('../beast1.png', False)
    response = clients[1].post('/charcreo/portrait/save', data={'custom-url': '', 'selected-portrait': 'beast/beast1.png'})
    assert response.status_code == 200 and 'beast/beast1.png' in response.text and '%2F' not in response.text
    cid = summon(clients)
    response = clients[1].post(f'/companions/{cid}/portrait', data={'custom-url': '', 'selected-portrait': 'beast/beast1.png'})
    assert response.status_code == 200 and '/static/images/portraits/beast/beast1.png' in response.text
    picker = clients[1].get(f'/companions/{cid}/portrait')
    assert 'Portrait categories' in picker.text and 'Beasts' in picker.text


def test_summon_private_sheet_and_board_visibility(shared):
    app, clients, _ = shared
    for user in (2, 3, 4):
        assert clients[user].get('/parties/1/monsters').status_code == 403
        assert clients[user].post('/parties/1/monsters', data={'template': 'creeping-vines'}).status_code == 403
    cid = summon(clients)
    sheet = clients[1].get(f'/companions/{cid}')
    assert sheet.status_code == 200
    assert 'Show stats to players' not in sheet.text and 'In combat' not in sheet.text
    assert clients[2].get(f'/companions/{cid}').status_code == 403
    assert any(t.get('kind') == 'monster' for t in clients[1].get('/party/1/shared-map/tokens').json['tokens'])
    assert not any(t.get('kind') == 'monster' for t in clients[2].get('/party/1/shared-map/tokens').json['tokens'])
    visibility_url = f'/party/1/shared-map/monsters/{cid}/visibility'
    assert clients[1].get(visibility_url).json['shared'] is False
    assert clients[1].post(visibility_url, json={'shared': True, 'public_notes': 'Visible note'}).status_code == 200
    page = clients[2].get(f'/party/1/shared-map/actors/{cid}')
    assert page.status_code == 200 and 'Visible note' in page.text
    assert 'asphyxiate' not in page.text and 'fertilizer' not in page.text
    assert clients[2].get(f'/companions/{cid}/stats').status_code == 403
    assert clients[2].get(f'/companions/{cid}/containers/0').status_code == 403
    with app.app_context():
        party = db.session.get(Party, 1)
        assert not party.hirelings and len(party.monsters) == 1


def test_transfer_preserves_record_and_inventory(shared):
    app, clients, _ = shared
    cid = summon(clients)
    with app.app_context():
        character = db.session.get(Character, 1)
        character.owner_username, character.url_name = 'map2', 'player'
        c = db.session.get(Companion, cid)
        c.hp = 3
        c.image_url = 'beast/beast1.png'
        c.items = '[{"id":"book","name":"Spellbook","tags":[],"location":0}]'
        db.session.commit()
    assert clients[2].post(f'/companions/{cid}/monster', data={'action': 'give', 'character_id': 1}).status_code == 403
    result = clients[1].post(f'/companions/{cid}/monster', data={'action': 'give', 'character_id': 1})
    assert result.status_code == 302
    with app.app_context():
        c = db.session.get(Companion, cid)
        assert c.kind == 'pet' and c.character_id == 1 and c.party_id is None
        assert c.hp == 3 and c.hp_max == 8 and c.image_url == 'beast/beast1.png'
        assert 'Spellbook' in c.items and 'asphyxiate' in c.notes
    assert clients[2].get(f'/companions/{cid}').status_code == 200
    assert clients[1].post(f'/companions/{cid}/monster', data={'action': 'give', 'character_id': 1}).status_code == 403


def test_visibility_is_warden_owned_and_cannot_be_changed_from_sheet(shared):
    app, clients, sockets = shared
    cid = summon(clients)
    path = f'/party/1/shared-map/monsters/{cid}/visibility'
    payload = {'shared': True, 'public_notes': 'Known to players'}
    for user in (2, 3, 4):
        assert clients[user].get(path).status_code == 403
        assert clients[user].post(path, json=payload).status_code == 403
    assert clients[4].get(f'/party/2/shared-map/monsters/{cid}/visibility').status_code == 404
    for action in ('combat', 'visibility'):
        assert clients[1].post(f'/companions/{cid}/monster', data={'action': action, 'shared': 'on'}).status_code == 400
    for data in ({'shared': 'true', 'public_notes': ''}, {}, {'shared': True, 'public_notes': 'x' * 10001}):
        assert clients[1].post(path, json=data).status_code == 400
    assert clients[1].get(path).json['shared'] is False
    for socket in sockets.values():
        socket.get_received()
    assert clients[1].post(path, json=payload).status_code == 200
    assert not any(t.get('kind') == 'monster' for t in clients[2].get('/party/1/shared-map/tokens').json['tokens'])
    assert any(e['name'] == 'party_actors_changed' for e in sockets[2].get_received())
    assert sockets[3].get_received() == sockets[4].get_received() == []
    assert clients[1].post(path, json={'shared': False, 'public_notes': 'Known to players'}).status_code == 200
    assert clients[2].get(f'/party/1/shared-map/actors/{cid}').status_code == 403
    assert not any(t.get('kind') == 'monster' for t in clients[2].get('/party/1/shared-map/tokens').json['tokens'])
    app.config['WTF_CSRF_ENABLED'] = True
    assert clients[1].post(path, json=payload).status_code == 400


def test_import_atomic_and_private_rolls(shared):
    app, clients, sockets = shared
    response = clients[1].post('/parties/1/monsters', data={'monster_file': (BytesIO(b'# Wolf\n4 HP, 12 STR, bite (d6)\n- Secret'), 'wolf.md')})
    assert response.status_code == 302
    cid = int(response.location.rsplit('/', 1)[1])
    for s in sockets.values():
        s.get_received()
    assert clients[1].post('/parties/1/monsters', data={'monster_file': (BytesIO(b'bad'), 'bad.md')}).status_code == 400
    data = {'companion_id': cid, 'dice': 'd6'}
    assert clients[2].post('/party/1/shared-map/roll', data=data).status_code == 403
    assert clients[1].post('/party/1/shared-map/roll', data=data).status_code == 200
    assert sockets[2].get_received() == []
    assert 'Wolf' not in clients[2].get('/party/1/roll-history').text
    assert clients[1].post('/party/1/shared-map/roll', data=dict(data, public_roll='on')).status_code == 200
    assert 'Wolf' in clients[2].get('/party/1/roll-history').text
    with app.app_context():
        assert Companion.query.count() == 1 and PartyRoll.query.count() == 2


def test_locked_map_and_unlocked_tokens(shared):
    _, clients, _ = shared
    locked = deepcopy(DRAWING)
    locked['elements'][0]['locked'] = True
    assert clients[1].post(URL, json={'version': 0, 'drawing': locked}).status_code == 200
    moved = deepcopy(locked)
    moved['elements'][0]['x'] += 10
    assert clients[2].post(URL, json={'version': 1, 'drawing': moved}).status_code == 400
    assert clients[2].post(URL, json={'version': 1, 'drawing': {'elements': [], 'files': {}}}).status_code == 400
    added = deepcopy(locked)
    added['elements'].append({'id': 'free-token', 'type': 'ellipse', 'x': 40, 'y': 40, 'width': 20, 'height': 20})
    assert clients[2].post(URL, json={'version': 1, 'drawing': added}).status_code == 200
    assert clients[1].post(URL, json={'version': 2, 'drawing': moved}).status_code == 200


def test_monster_portraits_cover_catalog_and_preserve_custom_choice(shared):
    from app.lib.monsters import CATALOG, monster_portrait, monster_portraits
    app, clients, _ = shared
    catalog = monster_catalog()
    assert set(monster_portraits()) == set(catalog)
    for template in catalog.values():
        assert (CATALOG.parents[1] / 'images/portraits' / template['image_url']).is_file()
    for key, template in catalog.items():
        if 'dragon' in key or key == 'wyvern':
            assert template['image_url'] == 'coldblooded/coldblooded3.png'
    assert monster_portrait('Wolf') == 'beast/beast1.png'
    assert monster_portrait('Vampire Bat') == 'beast/beast40.png'
    assert monster_portrait('Unknown imported creature') == 'monster/monster11.png'
    cid = summon(clients)
    with app.app_context():
        c = db.session.get(Companion, cid)
        assert c.image_url == monster_portrait('Creeping Vines')
        c.image_url = 'beast/beast1.png'
        db.session.commit()
    assert '/static/images/portraits/beast/beast1.png' in clients[1].get(f'/companions/{cid}').text


def test_party_tabs_embed_monsters_for_warden_only(shared):
    app, clients, _ = shared
    with app.app_context():
        db.session.get(Party, 1).containers = '[{"id":0,"name":"Main","slots":10}]'
        character = db.session.get(Character, 1)
        character.owner_username, character.url_name = 'map2', 'player'
        character.items, character.containers = '[]', '[{"id":0,"name":"Main","slots":10}]'
        db.session.commit()
    url = '/users/map1/parties/party/'
    page = clients[1].get(url)
    assert page.status_code == 200
    assert 'id="characters-tab"' in page.text
    assert 'id="monsters-tab"' in page.text
    assert 'id="roll-history-tab"' in page.text
    assert 'id="monster-catalog"' in page.text
    assert 'action="/parties/1/monsters"' in page.text
    assert 'id="monster-import-format"' in page.text
    assert 'aria-describedby="monster-import-format"' in page.text
    assert '3 HP, 0 Armor, 6 STR, 14 DEX, 3 WIL, bite (d8)' in page.text
    cid = summon(clients)
    assert '/users/map1/parties/party/#monsters' in clients[1].get(f'/companions/{cid}').text
    for user in (2, 3, 4):
        page = clients[user].get(url)
        assert page.status_code == 200
        assert 'id="monsters-tab"' not in page.text
        assert 'id="monster-catalog"' not in page.text


def test_board_stats_are_viewer_specific_live_and_never_in_scene(shared):
    app, clients, _ = shared
    cid = summon(clients)
    path = '/party/1/shared-map/stats'
    with app.app_context():
        character = db.session.get(Character, 1)
        character.hp, character.hp_max = 4, 7
        character.strength, character.strength_max = 9, 12
        character.notes = 'PRIVATE CHARACTER NOTES'
        monster = db.session.get(Companion, cid)
        monster.notes = 'PRIVATE MONSTER NOTES'
        monster.public_notes = 'Existing public notes'
        db.session.commit()
    for user in (1, 2):
        result = clients[user].get(path)
        assert result.status_code == 200 and result.headers['Cache-Control'] == 'no-store'
        actor = next(a for a in result.json['actors'] if a['id'] == '1')
        assert actor['stats']['hp'] == [4, 7] and actor['stats']['strength'] == [9, 12]
        assert 'NOTES' not in result.text and 'items' not in result.text
    assert any(a['id'] == f'companion:{cid}' and a['shared'] is False for a in clients[1].get(path).json['actors'])
    assert not any(a['kind'] == 'monster' for a in clients[2].get(path).json['actors'])
    visibility = f'/party/1/shared-map/monsters/{cid}/visibility'
    revealed = clients[1].post(visibility, json={'shared': True})
    assert revealed.status_code == 200 and revealed.json['public_notes'] == 'Existing public notes'
    assert any(a['id'] == f'companion:{cid}' for a in clients[2].get(path).json['actors'])
    with app.app_context():
        db.session.get(Companion, cid).hp = 2
        db.session.commit()
    assert next(a for a in clients[2].get(path).json['actors'] if a['id'] == f'companion:{cid}')['stats']['hp'][0] == 2
    assert clients[1].post(visibility, json={'shared': False}).status_code == 200
    assert not any(a['kind'] == 'monster' for a in clients[2].get(path).json['actors'])
    assert 'stats' not in clients[2].get(URL).text
    for user in (3, 4):
        assert clients[user].get(path).status_code == 403
    with app.app_context():
        db.session.get(Party, 1).members = '[]'
        db.session.commit()
    assert clients[2].get(path).status_code == 403


def test_board_stats_include_companions_and_omit_missing_stats(shared):
    app, clients, _ = shared
    with app.app_context():
        hireling = Companion(kind='hireling', party_id=1, name='Ada', hp=3, hp_max=4, shared=False)
        db.session.add_all([hireling,
            Companion(kind='pet', character_id=1, name='Moss', strength=7, strength_max=8),
            Companion(kind='pet', character_id=1, name='No stats')])
        db.session.flush()
        db.session.add(Companion(kind='pet', hireling_id=hireling.id, name='Pip', hp=1, hp_max=2))
        db.session.commit()
    for user in (1, 2):
        actors = clients[user].get('/party/1/shared-map/stats').json['actors']
        assert {a['name'] for a in actors} == {'Ada', 'Moss', 'Pip'}
        assert not any('shared' in a for a in actors)


def test_board_party_and_shared_dice_modal_for_both_roles(shared):
    _, clients, _ = shared
    for user in (1, 2):
        html = clients[user].get('/party/1/shared-map').text
        assert 'id="board-party"' in html and 'id="party-frame"' in html
        assert '/users/map1/parties/party/' in html
        assert 'fa-users' in html and 'fa-circle-half-stroke' in html
        assert 'id="dice-modal-d20-button"' in html
        assert 'Token stats' not in html and 'Everyone in the party can edit' not in html
        assert 'board-roll-history' not in html and 'board-roll-form' not in html
        assert ('id="lock-map"' in html) is (user == 1)
        assert ('id="warden-public-roll"' in html) is (user == 1)


@pytest.mark.parametrize('attack,expected', [
    ('claws (d6+d6), bite (d8)', ['d6+d6', 'd8']),
    ('claws (2d6), bite (d6 + d6)', ['d6+d6']),
    ('touch (d4, blast)', ['d4']),
    ('no attack', []), ('blast (3d6)', []), ('bite (d60)', []),
])
def test_attack_damage_expressions(attack, expected):
    from app.lib.monsters import attack_dice
    assert attack_dice(attack) == expected


def test_monster_saves_use_current_stat_and_private_history(shared, monkeypatch):
    app, clients, sockets = shared
    cid = summon(clients)
    monkeypatch.setattr('secrets.randbelow', lambda side: 9)
    with app.app_context():
        db.session.get(Companion, cid).strength = 10
        db.session.commit()
    body = dict(companion_id=cid, dice='d20', save='strength')
    result = clients[1].post('/party/1/shared-map/roll', data=body)
    assert result.status_code == 200 and 'STR 10' in result.json['result'] and 'Success' in result.json['result']
    assert 'STR 10' not in clients[2].get('/party/1/roll-history').text
    with app.app_context():
        db.session.get(Companion, cid).strength = 9
        db.session.commit()
    result = clients[1].post('/party/1/shared-map/roll', data=body)
    assert 'Failure' in result.json['result']
    for data in (dict(body, dice='d6'), dict(body, save='hp'), dict(dice='d20', save='strength')):
        assert clients[1].post('/party/1/shared-map/roll', data=data).status_code == 400
    assert clients[2].post('/party/1/shared-map/roll', data=body).status_code == 403


def test_warden_creates_and_deletes_pets_only_for_current_members(shared):
    app, clients, _ = shared
    with app.app_context():
        character = db.session.get(Character, 1)
        character.owner_username, character.url_name = 'map2', 'player'
        db.session.commit()
    assert clients[1].get('/characters/1/pets/add').status_code == 200
    result = clients[1].post('/characters/1/pets/add', data=dict(template='Custom', name='Test pet'))
    assert result.status_code == 302
    path = result.location
    assert 'Delete pet' in clients[1].get(path).text
    assert clients[3].post(path + '/delete').status_code == 403
    with app.app_context():
        db.session.get(Party, 1).members = '[]'
        db.session.commit()
    assert clients[1].get('/characters/1/pets/add').status_code == 403
    assert clients[1].post(path + '/delete').status_code == 403
    with app.app_context():
        db.session.get(Party, 1).members = '[1]'
        db.session.commit()
    assert clients[1].post(path + '/delete').status_code == 302

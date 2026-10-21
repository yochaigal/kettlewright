import html
import json
import re

import pytest

from app.models import db, User, Party, Campaign, Character, Companion, ContentEntry


@pytest.fixture
def generated(app_with_babel):
    app = app_with_babel
    app.config.update(WTF_CSRF_ENABLED=True, LOCAL_FEATURE_ACCESS=False,
                      FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    with app.app_context():
        db.session.add_all([User(id=i, username=f'generator{i}') for i in (1,2)])
        db.session.add_all([Party(id=i, owner=i, owner_username=f'generator{i}', name=f'Party{i}', party_url=f'party{i}') for i in (1,2)])
        db.session.add_all([Campaign(id=i, owner_id=i, name=f'Campaign{i}') for i in (1,2)])
        db.session.commit()
    clients = {}
    for i in (1,2):
        client = app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
        clients[i] = client
    page = clients[1].get('/tools/').text
    csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)[1]
    page = clients[1].get('/gen/character?view=sheet&background=Outrider').text
    snapshot = html.unescape(re.search(r'id="pcgen-snapshot" value="([^"]+)"', page)[1])
    data = json.loads(html.unescape(re.search(r'id="json_data" value="([^"]+)"', page)[1]))
    return app, clients, {'snapshot':snapshot, 'csrf_token':csrf, 'target_id':1}, data


@pytest.mark.parametrize('kind', ['hireling', 'monster'])
def test_save_character_to_party_preserves_stats_portrait_inventory_and_pet(generated, kind):
    app, clients, form, data = generated
    form['companion_kind'] = kind
    response = clients[1].post('/gen/character/save/party', data=form)
    assert response.status_code == 302
    assert clients[1].get(response.location).status_code == 200
    with app.app_context():
        monster = db.session.get(Companion, int(response.location.rsplit('/',1)[1]))
        assert monster.kind == kind and monster.party_id == 1
        assert monster.shared == (kind == 'hireling')
        assert monster.name == data['name'] and monster.role == data['background']
        for field in ('hp','hp_max','strength','strength_max','dexterity','dexterity_max','willpower','willpower_max','gold','image_url'):
            assert getattr(monster, field) == data[field]
        assert monster.armorValue() == data['armor']
        assert [(i['name'],i['location']) for i in json.loads(monster.items)] == [(i['name'],i['location']) for i in data['items']]
        assert json.loads(monster.containers) == data['containers']
        assert len(monster.pets) == len(data['pets']) == 1
        assert monster.pets[0].name == data['pets'][0]['name']
        assert data['description'] in monster.notes
        assert Character.query.count() == 0


def test_save_character_as_npc_creates_private_campaign_article(generated):
    app, clients, form, data = generated
    response = clients[1].post('/gen/character/save/npc', data=form)
    assert response.status_code == 302
    assert clients[1].get(response.location).status_code == 200
    with app.app_context():
        entry = ContentEntry.query.one()
        assert entry.owner_id == entry.campaign_id == 1 and entry.category == 'npc'
        assert entry.title == data['name']
        assert data['image_url'] in entry.body
        assert data['background'] in entry.body and data['description'] in entry.body
        assert data['background_table1_answer'] in entry.body
        for item in data['items']:
            assert item['name'] in entry.body
        assert not entry.presentations
        assert Character.query.count() == Companion.query.count() == 0


@pytest.mark.parametrize('kind', ['party','monster','npc'])
@pytest.mark.parametrize('problem', ['target','tampered','csrf','other-user'])
def test_generated_character_saves_reject_unauthorized_or_invalid_requests(generated, kind, problem):
    app, clients, form, _ = generated
    client = clients[1]
    if problem == 'target':
        form['target_id'] = 2
        expected = 403
    elif problem == 'tampered':
        form['snapshot'] += 'bad'
        expected = 400
    elif problem == 'csrf':
        form.pop('csrf_token')
        expected = 400
    else:
        client = clients[2]
        page = client.get('/tools/').text
        form['csrf_token'] = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)[1]
        form['target_id'] = 2
        expected = 400
    assert client.post(f'/gen/character/save/{kind}', data=form).status_code == expected
    with app.app_context():
        assert Character.query.count() == Companion.query.count() == ContentEntry.query.count() == 0


def test_npc_save_is_available_without_tester_ids(generated):
    app, clients, form, _ = generated
    app.config['FEATURE_TEST_USER_IDS'] = set()
    assert clients[1].post('/gen/character/save/npc', data=form).status_code == 302
    with app.app_context():
        assert ContentEntry.query.one().owner_id == 1


@pytest.mark.parametrize('kind', ['party', 'monster', 'npc'])
def test_all_backgrounds_can_be_saved(generated, kind):
    from app.lib.char_utils import load_backgrounds
    app, clients, form, _ = generated
    for background in load_backgrounds():
        page = clients[1].get('/gen/character', query_string={'view':'sheet','background':background}).text
        form['snapshot'] = html.unescape(re.search(r'id="pcgen-snapshot" value="([^"]+)"', page)[1])
        response = clients[1].post(f'/gen/character/save/{kind}', data=form)
        assert response.status_code == 302, (background, response.text)
    with app.app_context():
        assert Character.query.count() == 0
        if kind == 'npc':
            assert ContentEntry.query.count() == len(load_backgrounds())
        else:
            assert Companion.query.filter_by(kind='hireling' if kind == 'party' else 'monster').count() == len(load_backgrounds())


@pytest.mark.parametrize('kind', ['pet', 'npc', '', 'invalid'])
def test_party_save_rejects_invalid_companion_kind(generated, kind):
    app, clients, form, _ = generated
    form['companion_kind'] = kind
    assert clients[1].post('/gen/character/save/party', data=form).status_code == 400
    with app.app_context():
        assert Companion.query.count() == 0


def test_party_save_available_without_tester_ids_and_defaults_to_hireling(generated):
    app, clients, form, _ = generated
    app.config['FEATURE_TEST_USER_IDS'] = set()
    page = clients[1].get('/tools/').text
    assert 'Save to Party' in page and 'Plain Text' in page
    assert 'id="pcgen-save-npc-button"' in page
    response = clients[1].post('/gen/character/save/party', data=form)
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Companion, int(response.location.rsplit('/', 1)[1])).kind == 'hireling'


def test_tools_offers_npc_save_to_all_authenticated_users(generated):
    _, clients, _, _ = generated
    assert 'id="pcgen-save-npc-button"' in clients[1].get('/tools/').text


@pytest.mark.parametrize('kind', ['party', 'monster', 'npc'])
def test_anonymous_cannot_save_generated_characters(generated, kind):
    app, _, form, _ = generated
    assert app.test_client().post(f'/gen/character/save/{kind}', data=form).status_code == 302

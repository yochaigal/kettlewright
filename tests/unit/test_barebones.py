"""Cairn Barebones Edition characters (#292)."""
import html
import io
import json
import re

import pytest

from app.lib import barebones
from app.models import Character, User, db


def form_values(text):
    """Collect the values the rendered creation form would post back."""
    data = {}
    for match in re.finditer(r'<input[^>]*type="(?:hidden|text|number)"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', text):
        data[match.group(1)] = html.unescape(match.group(2))
    for match in re.finditer(r'<select[^>]*name="([^"]+)".*?</select>', text, re.S):
        selected = re.search(r'<option value="([^"]*)"\s*selected', match.group(0))
        data[match.group(1)] = selected.group(1) if selected else ''
    return data


@pytest.fixture
def client(app_with_babel):
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='bare'))
        db.session.commit()
    client = app_with_babel.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
    return client


def rolled(client):
    page = client.get('/new_character/barebones/')
    assert page.status_code == 200
    response = client.post('/charcreo/barebones/roll/all', data=form_values(page.get_data(True)))
    assert response.status_code == 200
    return form_values(response.get_data(True))


def test_tables_match_the_rules():
    data = barebones.barebones_data()
    assert len(data['names']) == len(data['backgrounds']) == len(data['gear']) == 100
    assert len(data['armor']) == len(data['weapons']) == 6
    assert barebones.gear_packages() == ['Fighter', 'Thief', 'Magic-User', 'Cleric']
    assert data['backgrounds'][0]['name'] == 'Acolyte'
    assert data['backgrounds'][99]['name'] == 'Witchfinder'
    assert all(len(b['items']) == 3 for b in data['backgrounds'])


def test_random_entries_resolve_to_concrete_items(app_with_babel):
    with app_with_babel.app_context():
        acolyte = barebones.background_items(1)  # Incense, Parchment & Ink (3 uses), Spellbook
        assert acolyte[1] == {'name': 'Parchment & Ink', 'tags': ['uses'], 'uses': 3}
        assert acolyte[2]['name'].startswith('Spellbook (') and acolyte[2]['description']
        cultist = barebones.background_items(30)
        assert cultist[2]['name'].startswith('Scroll (') and cultist[2]['tags'] == ['petty']
        fence = barebones.background_items(38)  # Bolt Cutters, Random Additional Gear, Sack
        assert len(fence) == 3 and all('random' not in item for item in fence)
        assert len(barebones.armor_items(1)) == 1  # "None" grants an extra gear roll
        assert barebones.armor_items(6) == [{'name': 'Plate', 'tags': ['3 Armor', 'bulky']}]
        assert barebones.weapon_items(3)[0]['name'] in ('Halberd', 'War Hammer', 'Long Sword')


def test_wagon_and_cart_add_containers():
    items, containers = barebones.build_inventory([barebones.gear_items(15), barebones.gear_items(95)])
    assert [c['name'] for c in containers] == ['Main', 'Cart', 'Wagon']
    assert [c['slots'] for c in containers] == [10, 4, 8]
    assert [c['id'] for c in containers] == [0, 1, 2]
    assert all(item['location'] == 0 for item in items)


def test_build_inventory_keeps_items_past_ten_slots():
    plate = barebones.armor_items(6)
    items, _ = barebones.build_inventory([plate] * 6)
    assert len(items) == 6 and barebones.slots_used(items) == 12


def test_roll_all_and_save_barebones_character(app_with_babel, client):
    data = rolled(client)
    for field in ('name', 'age', 'strength', 'dexterity', 'willpower', 'hp', 'gold', 'background', 'armor', 'weapon', 'gear'):
        assert data[field], field
    response = client.post('/charcreo/barebones/save', data=data)
    assert response.headers['HX-Redirect'].startswith('/users/bare/characters/')
    with app_with_babel.app_context():
        character = Character.query.one()
        assert character.edition == 'barebones' and character.is_barebones
        assert character.background == barebones.background_name(int(data['background']))
        assert (character.bonds, character.omens, character.description) == ('', '', '')
        assert character.strength == character.strength_max == int(data['strength'])
        names = [item['name'] for item in json.loads(character.items)]
        assert names[:2] == ['Rations', 'Torch']
        assert character.armor == str(character.armorValue())


def test_rerolling_one_table_keeps_the_others(client):
    data = rolled(client)
    response = client.post('/charcreo/barebones/roll/weapon', data=data)
    after = form_values(response.get_data(True))
    for group in ('bkg_items', 'armor_items', 'gear_items', 'start_items'):
        assert after[group] == data[group]


def test_gear_package_replaces_rolled_gear(app_with_babel, client):
    data = rolled(client)
    data['gear_source'] = 'Cleric'
    data = form_values(client.post('/charcreo/barebones/change/gear_source', data=data).get_data(True))
    client.post('/charcreo/barebones/save', data=data)
    with app_with_babel.app_context():
        character = Character.query.one()
        assert character.background == 'Cleric'
        names = [item['name'] for item in json.loads(character.items)]
        assert names == ['Rations', 'Torches', 'War Hammer', 'Helmet', 'Spellbook (Cure Wounds)', 'Bandages', 'Bone Charm']
        assert character.armorValue() == 1


def test_swap_attributes(client):
    data = rolled(client)
    data.update(strength='3', dexterity='17', swap_attribute_1='str', swap_attribute_2='dex')
    after = form_values(client.post('/charcreo/barebones/swap', data=data).get_data(True))
    assert (after['strength'], after['dexterity']) == ('17', '3')


def test_save_requires_name_background_and_attributes(app_with_babel, client):
    response = client.post('/charcreo/barebones/save', data={})
    page = response.get_data(True)
    assert 'id="error-modal"' in page
    for message in ('Required background selection', 'Required character name', 'Required STR attribute',
                    'Required DEX attribute', 'Required WIL attribute', 'Required HP attribute'):
        assert message in page
    assert 'HX-Redirect' not in response.headers
    with app_with_babel.app_context():
        assert Character.query.count() == 0


def test_creation_requires_login(app_with_babel):
    client = app_with_babel.test_client()
    assert client.get('/new_character/barebones/').status_code in (302, 401)
    assert client.post('/charcreo/barebones/save', data={}).status_code in (302, 401)


def test_barebones_sheet_hides_bonds_omens_and_background_tables(app_with_babel, client):
    client.post('/charcreo/barebones/save', data=rolled(client))
    with app_with_babel.app_context():
        url_name = Character.query.one().url_name
    page = client.get(f'/users/bare/characters/{url_name}/').get_data(True)
    assert 'edition-badge' in page
    for container in ('character-bonds-container', 'character-omens-container', 'character-background-container'):
        assert container not in page
    assert 'character-scars-container' in page


def test_second_edition_sheet_keeps_bonds_and_omens(app_with_babel, client):
    with app_with_babel.app_context():
        db.session.add(Character(name='Old Hand', background='Outrider', owner=1, owner_username='bare',
                                 url_name='old-hand', items='[]', containers='[{"id": 0, "name": "Main", "slots": 10}]',
                                 hp=3, hp_max=3, strength=10, strength_max=10, dexterity=10, dexterity_max=10,
                                 willpower=10, willpower_max=10, gold=0))
        db.session.commit()
        assert Character.query.one().edition == '2e'
    page = client.get('/users/bare/characters/old-hand/').get_data(True)
    assert 'character-bonds-container' in page and 'edition-badge' not in page


def test_json_export_import_keeps_edition(app_with_babel, client):
    client.post('/charcreo/barebones/save', data=rolled(client))
    with app_with_babel.app_context():
        data = json.loads(Character.query.one().toJSON())
    assert data['edition'] == 'barebones'
    form = {key: json.dumps(value) if isinstance(value, (list, bool)) else value
            for key, value in data.items() if value is not None}
    assert client.post('/new_from_json/', data=form).status_code == 302
    form['edition'] = 'bogus'
    client.post('/new_from_json/', data=form)
    with app_with_babel.app_context():
        editions = [c.edition for c in Character.query.order_by(Character.id)]
    assert editions == ['barebones', 'barebones', '2e']


# Tools generator

def generator_snapshot(page):
    return json.loads(html.unescape(re.search(r'id="json_data" value="([^"]*)"', page)[1]))


@pytest.mark.parametrize('choice', ['barebones', 'barebones:Fighter', 'barebones:Thief',
                                    'barebones:Magic-User', 'barebones:Cleric'])
def test_tools_generator_previews_barebones_characters(app_with_babel, choice):
    client = app_with_babel.test_client()
    for _ in range(10):
        page = client.get('/gen/character', query_string={'background': choice, 'view': 'sheet'}).text
        data = generator_snapshot(page)
        assert data['edition'] == 'barebones'
        assert (data['bonds'], data['omens'], data['background_table1_question']) == ('', '', '')
        assert 3 <= data['strength'] <= 18 and 1 <= data['hp'] <= 6 and 3 <= data['gold'] <= 18
        if choice != 'barebones':
            assert data['background'] == choice.partition(':')[2]
        assert 'edition-badge' in page
        for container in ('character-bonds-container', 'character-omens-container', 'background-table-answers'):
            assert container not in page
    with app_with_babel.app_context():
        assert Character.query.count() == 0


def test_tools_generator_text_json_and_print_outputs(app_with_babel):
    client = app_with_babel.test_client()
    data = client.get('/gen/character?output=json&background=barebones:Cleric').json
    assert data['edition'] == 'barebones' and data['armor'] == 1
    text = client.get('/gen/character?background=barebones').text
    assert 'json_data' in text and 'Bonds' not in text and 'Omens' not in text
    printed = client.post('/gen/character/print', data={'json_data': json.dumps(data)})
    assert printed.status_code == 200
    assert client.get('/gen/character?background=barebones:Bard').status_code == 400


def test_tools_page_offers_barebones_options(app_with_babel):
    page = app_with_babel.test_client().get('/tools/').text
    assert 'value="barebones"' in page and 'value="barebones:Magic-User"' in page


def test_barebones_generator_saves_to_party_as_hireling(app_with_babel):
    from app.models import Companion, Party
    app = app_with_babel
    app.config.update(LOCAL_FEATURE_ACCESS=False, FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    with app.app_context():
        db.session.add(User(id=1, username='warden'))
        db.session.add(Party(id=1, owner=1, owner_username='warden', name='Party', party_url='party'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    page = client.get('/gen/character?view=sheet&background=barebones:Fighter').text
    snapshot = html.unescape(re.search(r'id="pcgen-snapshot" value="([^"]+)"', page)[1])
    data = generator_snapshot(page)
    response = client.post('/gen/character/save/party', data={'snapshot': snapshot, 'target_id': 1,
                                                               'companion_kind': 'hireling'})
    assert response.status_code == 302
    with app.app_context():
        hireling = Companion.query.one()
        assert (hireling.name, hireling.role) == (data['name'], 'Fighter')
        assert hireling.armorValue() == 2 and 'Sword (d8)' in hireling.attack



def test_one_new_character_button_and_edition_tabs_on_both_creators(client):
    page = client.get('/users/bare/characters/').get_data(True)
    assert 'href="/new_character/ "' in page and '/new_character/barebones/' not in page
    second = client.get('/new_character/').get_data(True)
    bare = client.get('/new_character/barebones/').get_data(True)
    for html_page in (second, bare):
        assert 'class="edition-tabs"' in html_page
        assert 'href="/new_character/"' in html_page and 'href="/new_character/barebones/"' in html_page
    assert re.search(r'href="/new_character/"\s+aria-current="page"', second)
    assert re.search(r'href="/new_character/barebones/"\s+aria-current="page"', bare)


# PDF sheet

def test_split_traits_reads_both_sentence_forms():
    from app.lib.character_pdf import split_traits
    word_by_word = ('You have a Lanky Physique, Oily Skin, and Oily Hair. Your Face is Rakish, your Speech Blunt. '
                    'You have Filthy Clothing. You are Cautious and Deceitful. You are 31 years old.')
    sentence = ('You have a lanky physique, oily skin, and oily hair. Your face is rakish, your speech blunt. '
                'You have filthy clothing. You are cautious and deceitful. You are 31 years old.')
    for text in (word_by_word, sentence):
        traits, age = split_traits(text)
        assert traits == {'Physique': 'Lanky', 'Skin': 'Oily', 'Hair': 'Oily', 'Face': 'Rakish', 'Speech': 'Blunt',
                          'Clothing': 'Filthy', 'Virtue': 'Cautious', 'Vice': 'Deceitful'}
        assert age == '31'
    assert split_traits('A rewritten description.') == (None, '')


def test_barebones_pdf_uses_the_a4_barebones_sheet(app_with_babel, client):
    from pypdf import PdfReader
    client.post('/charcreo/barebones/save', data=rolled(client))
    with app_with_babel.app_context():
        character = Character.query.one()
        url_name, name, background = character.url_name, character.name, character.background
    for route in ('portrait', 'landscape'):
        response = client.get(f'/users/bare/characters/{url_name}/print/{route}.pdf')
        assert response.status_code == 200 and response.mimetype == 'application/pdf'
        assert f'{url_name}-barebones-a4.pdf' in response.headers['Content-Disposition']
        pdf = PdfReader(io.BytesIO(response.data))
        page = pdf.pages[0]
        assert (round(float(page.mediabox.width)), round(float(page.mediabox.height))) == (595, 842)
        widgets = [a for a in page.get('/Annots') or [] if a.get_object().get('/Subtype') == '/Widget']
        assert widgets == [] and '/AcroForm' not in pdf.trailer['/Root']  # values are drawn, not left in form fields
        text = page.extract_text()
        assert 'Physique' in text  # trait labels stored as pre-filled fields survive flattening
        assert name in text and background in text and 'Rations' in text
    view = client.get(f'/users/bare/characters/{url_name}/').get_data(True)
    assert 'character-pdf-barebones' in view and 'Print PDF (landscape)' not in view


def test_second_edition_pdf_keeps_a4_sheets(app_with_babel, client):
    from pypdf import PdfReader
    with app_with_babel.app_context():
        db.session.add(Character(name='Old Hand', background='Outrider', owner=1, owner_username='bare',
                                 url_name='old-hand', items='[]', containers='[{"id": 0, "name": "Main", "slots": 10}]',
                                 hp=3, hp_max=3, strength=10, strength_max=10, dexterity=10, dexterity_max=10,
                                 willpower=10, willpower_max=10, gold=0, traits='', notes=''))
        db.session.commit()
    response = client.get('/users/bare/characters/old-hand/print/landscape.pdf')
    assert 'old-hand-landscape-a4.pdf' in response.headers['Content-Disposition']
    page = PdfReader(io.BytesIO(response.data)).pages[0]
    assert round(float(page.mediabox.width)) == 842

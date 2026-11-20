"""Party backgrounds: a campaign's modules bring backgrounds (Markdown) for its parties' characters;
each party says whether the official ones are offered too."""
import io
import json
import zipfile

import pytest

from app.lib.campaign_backgrounds import (BackgroundError, BACKGROUND_TEMPLATE, background_markdown, party_backgrounds,
                                          official_backgrounds, parse_background_text, validate_background)
from app.lib.campaign_import import preview_archive, import_preview
from app.models import db, Campaign, Character, ContentEntry, Module, Party, User

TIDEWATCHER = {
    'background_description': 'You keep the lighthouse of a drowned town.',
    'names': ['Mara', 'Oskel'],
    'starting_gear': [{'name': 'Storm Lantern', 'tags': []}, {'name': 'Gaff', 'tags': ['d6']}],
    'table1': {'question': 'What did the sea take?', 'options': [
        {'description': 'Your sister. Take her Locket.', 'items': [{'name': 'Locket', 'tags': ['petty']}]},
        {'description': 'Your name.', 'bonus_gold': 5}]},
    'table2': {'question': 'Who still writes to you?', 'options': [
        {'description': 'A smuggler.', 'pets': ['Raven Familiar']}]},
    'image': 'not-ours.webp',  # Unknown keys are dropped.
}


def validate_backgrounds(data):
    """{name: background}, each cleaned like a saved background."""
    return dict(validate_background(name, background) for name, background in data.items())


def module_zip(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return stream.getvalue()


@pytest.fixture
def warden(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='player')])
        db.session.add(Campaign(id=1, owner_id=1, name='Drowned Coast'))
        db.session.add(Module(id=1, campaign_id=1, title='Coast Kit'))
        db.session.add(Party(id=1, owner=1, owner_username='warden', name='Lamplighters', party_url='lamplighters',
                             campaign_id=1, join_code='coast-code', members='[]', items='[]',
                             containers='[{"name":"Main","slots":10,"id":0}]'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    return app, client


def login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_validation_keeps_only_what_creation_reads():
    clean = validate_backgrounds({'Tidewatcher': TIDEWATCHER})['Tidewatcher']
    assert 'image' not in clean and clean['names'] == ['Mara', 'Oskel']
    assert clean['table1']['options'][1] == {'description': 'Your name.', 'bonus_gold': 5}
    # The official file validates too: modules use the same format.
    assert set(validate_backgrounds(official_backgrounds())) == set(official_backgrounds())


@pytest.mark.parametrize('broken, message', [
    ({'Custom': TIDEWATCHER}, 'reserved'),
    ({'Nameless': dict(TIDEWATCHER, names=[])}, 'at least one character name'),
    ({'Tableless': {k: v for k, v in TIDEWATCHER.items() if k != 'table2'}}, 'table2 is missing'),
    ({'Bad gear': dict(TIDEWATCHER, starting_gear=[{'tags': []}])}, 'expected text'),
    ({'Bad gold': dict(TIDEWATCHER, table1={'question': 'Q', 'options': [{'description': 'x', 'bonus_gold': -1}]})}, 'whole number'),
    ({'Petless': dict(TIDEWATCHER, table2={'question': 'Q', 'options': [{'description': 'x', 'pets': ['Gull']}]})}, 'unknown pet "Gull"'),
    ({'Not an object': []}, 'expected an object'),
])
def test_invalid_backgrounds_are_rejected(broken, message):
    with pytest.raises(BackgroundError, match=message):
        validate_backgrounds(broken)


TIDEWATCHER_MD = """---
layout: default
title: Tidewatcher
type: Background
---
You keep the lighthouse of a drowned town.

## Names
Mara, Oskel

## Starting gear
- Storm Lantern
- Gaff [d6]

## What did the sea take?
- Your sister. Take her Locket.
  - Locket [petty]
- Your name.
  - 5 gold

## Who still writes to you?
- A smuggler.
  - pet: Raven Familiar
"""


def test_markdown_is_the_only_background_format_and_round_trips():
    expected = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
    assert parse_background_text(TIDEWATCHER_MD) == expected
    assert parse_background_text(background_markdown('Tidewatcher', expected['Tidewatcher'])) == expected
    with pytest.raises(BackgroundError, match='Markdown'):  # JSON is not a format people write any more.
        parse_background_text(json.dumps({'Tidewatcher': TIDEWATCHER}))
    assert list(parse_background_text(BACKGROUND_TEMPLATE)) == ['Tidewatcher']  # "New background" starts valid.
    # Markdown says everything a background holds: every official one round-trips.
    for name, background in validate_backgrounds(official_backgrounds()).items():
        assert parse_background_text(background_markdown(name, background)) == {name: background}
    rich = parse_background_text(BACKGROUND_TEMPLATE.replace('- Gaff [d6]', '- Whistle [charges 2/3, petty] — Recharge: blow at dawn.\n'
                                                            '- Shield [armor active, 1 Armor]'))['Tidewatcher']
    whistle, shield = rich['starting_gear'][2:]
    assert whistle == {'name': 'Whistle', 'tags': ['charges', 'petty'], 'charges': 2, 'max_charges': 3,
                       'description': 'Recharge: blow at dawn.'}
    assert shield == {'name': 'Shield', 'tags': ['1 Armor'], 'armor_active': True}


@pytest.mark.parametrize('text, message', [
    (TIDEWATCHER_MD.replace('## Who still writes to you?', 'Who still writes?'), 'exactly two tables'),
    (TIDEWATCHER_MD.replace('pet: Raven Familiar', 'pet: Gull'), 'unknown pet'),
    (TIDEWATCHER_MD.replace('type: Background', 'type: Note'), 'type: Background'),
    (TIDEWATCHER_MD.replace('Mara, Oskel', ''), 'at least one character name'),
])
def test_markdown_background_errors_say_what_to_fix(text, message):
    with pytest.raises(BackgroundError, match=message):
        parse_background_text(text)


def test_party_offers_official_and_module_backgrounds_or_only_module_ones(warden):
    app, _ = warden
    with app.app_context():
        party = db.session.get(Party, 1)
        assert party_backgrounds(party) == official_backgrounds()
        db.session.get(Module, 1).backgrounds = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
        assert 'Tidewatcher' in party_backgrounds(party) and 'Aurifex' in party_backgrounds(party)
        party.official_backgrounds = False
        assert list(party_backgrounds(party)) == ['Tidewatcher']
        db.session.get(Module, 1).backgrounds = None  # Never empty: the official ones come back.
        assert party_backgrounds(party) == official_backgrounds()


def test_warden_writes_edits_uploads_and_removes_module_backgrounds(warden):
    app, client = warden
    page = client.get('/campaigns/1/modules/1/').get_data(as_text=True)
    assert 'No backgrounds in this module' in page and 'New background' in page
    editor = client.get('/campaigns/1/modules/1/background').get_data(as_text=True)
    assert 'type: Background' in editor and '## Names' in editor  # Starts from the template.
    saved = client.post('/campaigns/1/modules/1/background', data={'action': 'save', 'version': 1, 'text': TIDEWATCHER_MD})
    assert saved.status_code == 302 and saved.location.endswith('/campaigns/1/modules/1/#backgrounds')
    editor = client.get('/campaigns/1/modules/1/background?name=Tidewatcher').get_data(as_text=True)
    assert '## What did the sea take?' in editor and '  - pet: Raven Familiar' in editor
    # Renaming in the editor replaces it.
    renamed = TIDEWATCHER_MD.replace('title: Tidewatcher', 'title: Lampkeeper')
    client.post('/campaigns/1/modules/1/background?name=Tidewatcher', data={'action': 'save', 'version': 2, 'text': renamed})
    bad = client.post('/campaigns/1/modules/1/background', data={'action': 'save', 'version': 3, 'text': 'nonsense'})
    assert bad.status_code == 200 and 'role="alert"' in bad.get_data(as_text=True)
    # Background files are added with Add files (the module import), like every module part; Markdown only.
    page = client.get('/campaigns/1/modules/1/').get_data(as_text=True)
    assert 'module-upload' not in page and 'name="backgrounds"' not in page
    assert page.index('id="module-maps-title"') < page.index('id="module-backgrounds-title"') < page.index('id="module-articles-title"')
    header = page[:page.index('id="module-maps-title"')]
    assert 'href="/materials/import-archive?module_id=1"' in header and 'Add files' in header
    assert 'Add files' not in page[page.index('id="module-articles-title"'):]
    files = {'tide.md': TIDEWATCHER_MD, 'ferryman.md': renamed.replace('Lampkeeper', 'Ferryman')}
    preview = client.post('/materials/import-archive', data={'module_id': '1', 'archive': (io.BytesIO(module_zip(files)), 'more.zip')},
                          content_type='multipart/form-data').get_data(as_text=True)
    preview_id = preview.split('name="preview_id" value="')[1].split('"')[0]
    assert client.post('/materials/import-archive', data={'preview_id': preview_id, 'module_id': '1'}).status_code == 302
    with app.app_context():
        assert sorted(db.session.get(Module, 1).backgrounds) == ['Ferryman', 'Lampkeeper', 'Tidewatcher']
        version = db.session.get(Module, 1).version
    assert client.post('/campaigns/1/modules/1/background?name=Ferryman', data={'action': 'remove', 'version': version}).status_code == 302
    assert client.post('/campaigns/1/modules/1/background?name=Ferryman', data={'action': 'remove', 'version': version + 1}).status_code == 404
    # The party sets what its characters choose from, on the party page (Characters).
    off = client.post('/party/1/backgrounds', data={})  # Official ones off.
    assert off.location.endswith('/users/warden/parties/lamplighters/#backgrounds')
    page = client.get('/users/warden/parties/lamplighters/').get_data(as_text=True)
    assert 'id="party-backgrounds-button"' in page and 'aria-controls="backgrounds-dialog"' in page  # A button opens it.
    section = page[page.index('id="backgrounds-dialog"'):page.index('</dialog>', page.index('id="backgrounds-dialog"'))]
    assert 'Coast Kit' in section and 'Lampkeeper' in section and 'Aurifex' not in section.split('What players choose from')[1]
    assert 'name="official"' in section and 'checked' not in section.split('name="official"')[1].split('>')[0]
    assert 'id="backgrounds-dialog"' not in client.get('/campaigns/1/').get_data(as_text=True)
    login(client, 2)
    assert client.get('/campaigns/1/modules/1/').status_code == 403
    assert client.post('/party/1/backgrounds', data={}).status_code == 403


def test_module_export_brings_its_backgrounds_back(warden):
    app, client = warden
    with app.app_context():
        module = db.session.get(Module, 1)
        module.backgrounds = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
        db.session.add(ContentEntry(owner_id=1, campaign_id=1, module=module, category='npc', title='Keeper Ilsa', body='She watches.'))
        db.session.commit()
    exported = client.get('/campaigns/1/modules/1/export')
    assert exported.status_code == 200 and 'coast-kit.zip' in exported.headers['Content-Disposition']
    with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
        names = archive.namelist()
        assert 'backgrounds/tidewatcher.md' in names and 'type: Module' in archive.read('module.md').decode()
    with app.app_context():
        payload = preview_archive(exported.data, 1)
        assert payload['errors'] == [] and list(payload['backgrounds']) == ['Tidewatcher']
        import_preview(payload, 1, into=db.session.get(Campaign, 1))
        db.session.commit()
        copy = Module.query.filter(Module.id != 1).one()
        assert copy.title == 'Coast Kit' and copy.backgrounds == db.session.get(Module, 1).backgrounds
        assert [entry.title for entry in copy.entries] == ['Keeper Ilsa']


def test_module_upload_loads_its_articles_and_backgrounds(warden):
    app, client = warden
    archive = module_zip({
        'module.md': '---\nlayout: default\ntitle: Harbor Kit\ntype: Module\n---\nA kit for the harbor.',
        'npc.md': '---\nlayout: default\ntitle: Harbormaster\ntype: NPC\nparent: Harbor Kit\n---\nStern.',
        'backgrounds/tidewatcher.md': TIDEWATCHER_MD,
        'backgrounds/ferry.md': TIDEWATCHER_MD.replace('title: Tidewatcher', 'title: Ferryman'),
    })
    page = client.post('/materials/import-archive', data={'campaign_id': '1', 'archive': (io.BytesIO(archive), 'harbor.zip')},
                       content_type='multipart/form-data').get_data(as_text=True)
    assert '2 backgrounds' in page and '<option value="1" selected>Drowned Coast</option>' in page
    preview_id = page.split('name="preview_id" value="')[1].split('"')[0]
    response = client.post('/materials/import-archive', data={'preview_id': preview_id, 'target_campaign': '1'})
    with app.app_context():
        module = Module.query.filter_by(title='Harbor Kit').one()
        assert response.location.endswith(f'/campaigns/1/modules/{module.id}/')
        assert sorted(module.backgrounds) == ['Ferryman', 'Tidewatcher']
        assert {e.title for e in module.entries} == {'Harbor Kit', 'Harbormaster'}
        assert Campaign.query.count() == 1


def test_backgrounds_only_module(warden):
    app, client = warden
    archive = module_zip({'backgrounds/tidewatcher.md': TIDEWATCHER_MD})
    with app.app_context():
        payload = preview_archive(archive, 1)
        assert payload['errors'] == [] and payload['rows'] == []
        import_preview(payload, 1, into=db.session.get(Campaign, 1), name='coast')
        assert list(Module.query.filter_by(title='coast').one().backgrounds) == ['Tidewatcher']
    bad = module_zip({'backgrounds.json': json.dumps({'Tidewatcher': TIDEWATCHER})})  # JSON is not imported.
    with app.app_context():
        assert any('Markdown' in error for error in preview_archive(bad, 1)['errors'])
    bad = module_zip({'x.md': TIDEWATCHER_MD.replace('pet: Raven Familiar', 'pet: Gull')})
    with app.app_context():
        assert any('unknown pet' in error for error in preview_archive(bad, 1)['errors'])


def creation_form(**values):
    form = dict(name='Custom', custom_name='Mara', background='Tidewatcher', custom_background='',
                strength_max=10, dexterity_max=10, willpower_max=10, hp_max=4, gold=0, armor=0,
                items='[]', containers='', background_table1_select='Your name.',
                background_table2_select='A smuggler.', custom_image='false', portrait_src='', age=30,
                bonds='', omens='')
    form.update({name: 'Quiet' for name in ('Physique', 'Skin', 'Hair', 'Face', 'Speech', 'Clothing', 'Virtue', 'Vice')})
    form.update(values)
    return form


def test_character_created_with_a_join_code_uses_the_campaign_and_joins_the_party(warden):
    app, client = warden
    with app.app_context():
        db.session.get(Module, 1).backgrounds = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
        db.session.get(Party, 1).official_backgrounds = False
        db.session.commit()
    login(client, 2)
    page = client.get('/new_character/?party=coast-code').get_data(as_text=True)
    assert 'Creating a character for Lamplighters' in page and 'Drowned Coast' not in page  # Campaign stays private.
    assert '<option value="Tidewatcher">' in page and 'value="Aurifex"' not in page
    assert 'name="party_code" type="hidden" value="coast-code"' in page
    # Each creation step carries the code, so rolls use the campaign's list.
    fields = client.post('/charcreo/roll-background', data=creation_form(party_code='coast-code')).get_data(as_text=True)
    assert 'You keep the lighthouse of a drowned town.' in fields
    rolled = client.get('/charcreo/roll-all?party_code=coast-code').get_data(as_text=True)
    assert 'lighthouse of a drowned town' in rolled and 'value="coast-code"' in rolled

    response = client.post('/charcreo/save', data=creation_form(party_code='coast-code'))
    assert response.headers.get('HX-Redirect')
    with app.app_context():
        character = Character.query.one()
        assert character.background == 'Tidewatcher' and character.party_id == 1
        assert character.background_table1_question == 'What did the sea take?'
        assert [pet.name for pet in character.pets] == ['Raven Familiar']
        assert json.loads(db.session.get(Party, 1).members) == [character.id]


def test_without_a_code_creation_uses_official_backgrounds(warden):
    app, client = warden
    with app.app_context():
        db.session.get(Module, 1).backgrounds = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
        db.session.commit()
    login(client, 2)
    page = client.get('/new_character/').get_data(as_text=True)
    assert 'Tidewatcher' not in page and 'value="Aurifex"' in page and 'create-party-box' not in page
    assert 'No party has this join code' in client.get('/new_character/?party=nope').get_data(as_text=True)
    client.post('/charcreo/save', data=creation_form(background='Aurifex', background_table1_select='',
                                                     background_table2_select=''))
    with app.app_context():
        assert Character.query.one().party_id is None


def test_characters_page_joins_a_party_with_a_new_character(warden):
    """Join a party (Characters page): a new character for that party, with its campaign's backgrounds."""
    app, client = warden
    login(client, 2)
    page = client.get('/users/player/characters/').get_data(as_text=True)
    dialog = page[page.index('id="join-party-dialog"'):page.index('</dialog>', page.index('id="join-party-dialog"'))]
    assert 'Join a party' in page and 'action="/new_character/"' in dialog and 'name="party"' in dialog
    assert 'method="get"' in dialog and 'its Party section' in dialog
    assert 'Creating a character for Lamplighters' in client.get('/new_character/?party=coast-code').get_data(as_text=True)
    # Without a code, creation shows no party box; a wrong code can be corrected there.
    assert 'create-party-box' not in client.get('/new_character/').get_data(as_text=True)
    assert 'No party has this join code' in client.get('/new_character/?party=nope').get_data(as_text=True)
    party_page = client.get('/users/warden/parties/lamplighters/').get_data(as_text=True)
    assert 'invite-link-button' not in party_page


def test_existing_character_joins_with_the_code_and_keeps_its_background(warden):
    app, client = warden
    with app.app_context():
        db.session.get(Module, 1).backgrounds = validate_backgrounds({'Tidewatcher': TIDEWATCHER})
        db.session.add(Character(id=5, owner=2, name='Old Hand', background='Aurifex', url_name='old-hand',
                                 owner_username='player'))
        db.session.commit()
    login(client, 2)
    response = client.post('/charedit/player/old-hand/section/party', data={'party_code': 'coast-code'})
    assert response.status_code == 200
    with app.app_context():
        character = db.session.get(Character, 5)
        assert character.party_id == 1 and character.background == 'Aurifex'


def test_barebones_characters_join_the_party_too(warden):
    """Join a party carries over to the Barebones creator: no campaign backgrounds there, but it joins on save."""
    app, client = warden
    login(client, 2)
    page = client.get('/new_character/?party=coast-code').get_data(as_text=True)
    assert 'href="/new_character/barebones/?party=coast-code"' in page
    barebones = client.get('/new_character/barebones/?party=coast-code').get_data(as_text=True)
    assert 'Creating a character for Lamplighters' in barebones and 'name="party_code" value="coast-code"' in barebones
    form = {'party_code': 'coast-code', 'name': 'Rook', 'background': '1', 'strength': '10', 'dexterity': '10',
            'willpower': '10', 'hp': '4', 'gold': '5', 'age': '20'}
    response = client.post('/charcreo/barebones/save', data=form)
    assert response.headers.get('HX-Redirect'), response.get_data(as_text=True)
    with app.app_context():
        character = Character.query.one()
        assert character.edition == 'barebones' and character.party_id == 1
        assert json.loads(db.session.get(Party, 1).members) == [character.id]

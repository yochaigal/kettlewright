"""Module items (#476): gear and relics a module holds, sent as copies to a party's storage or a character."""
import io
import json
import zipfile

import pytest

from app.lib.campaign_import import import_preview, preview_archive
from app.lib.module_items import ItemError, item_markdown, items_from_markdown, items_file, parse_item_text
from app.lib.modules import BUNDLES, bundle_archive, bundle_contents
from app.models import db, Campaign, Character, Module, Party
from tests.helpers import login
from tests.unit.test_campaigns import setup  # noqa: F401

RELICS = """---
layout: default
title: Relics
type: Items
---
### The Eye of Vuk
A heavy iron medallion.
- A WIL save is required every time it is put on.

### Fletcher's Ire [bulky, charges 3/3]
A heavy bar of tungsten.

### Moon Cloth [petty]
Very warm.
"""


def body(text):
    return text.split('---\n', 2)[2]


def module_zip(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return stream.getvalue()


@pytest.fixture
def warden(setup):  # noqa: F811
    """The Warden (user 1) of campaign 1, with a module holding the relics; party 1 has Player A."""
    app, client = setup
    with app.app_context():
        module = Module(id=1, campaign_id=1, title='Twin Lakes', items=items_from_markdown(body(RELICS)))
        db.session.add(module)
        character = db.session.get(Character, 1)
        character.items, character.containers = '[]', '[{"id":0,"name":"Main","slots":10}]'
        party = db.session.get(Party, 1)
        party.containers = '[{"id":0,"name":"Cart","slots":10},{"id":1,"name":"Pouch","slots":0}]'
        db.session.commit()
    return app, client


def module_version(app):
    with app.app_context():
        return db.session.get(Module, 1).version


def test_items_read_and_write_as_markdown():
    items = items_from_markdown(body(RELICS))
    assert list(items) == ['The Eye of Vuk', "Fletcher's Ire", 'Moon Cloth']
    assert items['The Eye of Vuk'] == {'name': 'The Eye of Vuk', 'tags': [],
                                       'description': 'A heavy iron medallion.\n- A WIL save is required every time it is put on.'}
    assert items["Fletcher's Ire"] == {'name': "Fletcher's Ire", 'tags': ['bulky', 'charges'], 'charges': 3,
                                       'max_charges': 3, 'description': 'A heavy bar of tungsten.'}
    assert item_markdown(items["Fletcher's Ire"]) == "### Fletcher's Ire [bulky, charges 3/3]\nA heavy bar of tungsten.\n"
    # A file of them reads back as the same items.
    assert items_from_markdown(body(items_file('Relics', items))) == items
    assert parse_item_text('### Rope [uses 3]\n') == ('Rope', {'name': 'Rope', 'tags': ['uses'], 'uses': 3})


@pytest.mark.parametrize('text, message', [
    ('Some text first\n### Rope', 'write each item as a ### heading'),
    ('### Rope\n### Rope', 'written twice'),
    ('', 'no items found'),
    ('#### Not an item', 'write each item'),
    ('### ' + 'x' * 101, 'at most 100 characters'),
])
def test_bad_items_are_refused(text, message):
    with pytest.raises(ItemError, match=message):
        items_from_markdown(text)


def test_items_file_type_items_is_a_module_part_and_type_item_a_note(warden):
    app, client = warden
    archive = module_zip({'module.md': '---\nlayout: default\ntitle: Harbor Kit\ntype: Module\n---\nA kit.',
                          'items/relics.md': RELICS,
                          'articles/lamp.md': '---\nlayout: default\ntitle: The Lamp\ntype: Item\n---\nAn article.'})
    page = client.post('/materials/import-archive', data={'campaign_id': '1', 'archive': (io.BytesIO(archive), 'kit.zip')},
                       content_type='multipart/form-data').get_data(as_text=True)
    assert '3 items' in page and 'Fletcher&#39;s Ire' in page
    preview_id = page.split('name="preview_id" value="')[1].split('"')[0]
    assert client.post('/materials/import-archive', data={'preview_id': preview_id, 'target_campaign': '1'}).status_code == 302
    with app.app_context():
        module = Module.query.filter_by(title='Harbor Kit').one()
        assert list(module.items) == ['The Eye of Vuk', "Fletcher's Ire", 'Moon Cloth']
        # An old Item article is a Note now: only module items are items.
        assert [(entry.title, entry.category) for entry in module.entries if entry.title == 'The Lamp'] == [('The Lamp', 'note')]


def test_duplicate_items_across_files_are_an_error(app_with_babel):
    with app_with_babel.app_context():
        payload = preview_archive(module_zip({'a.md': RELICS, 'b.md': RELICS}))
        assert any('item "Moon Cloth" is defined twice' in error for error in payload['errors'])


def test_module_export_brings_its_items_back(warden):
    app, client = warden
    exported = client.get('/campaigns/1/modules/1/export')
    with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
        assert 'type: Items' in archive.read('items/items.md').decode()
    with app.app_context():
        payload = preview_archive(exported.data, 1)
        assert payload['errors'] == []
        import_preview(payload, 1, into=db.session.get(Campaign, 1))
        db.session.commit()
        copy = Module.query.filter(Module.id != 1).one()
        assert copy.items == db.session.get(Module, 1).items


def test_bundled_modules_bring_their_relics():
    assert bundle_contents('cas-1')['items'] == 5 and bundle_contents('cas-2')['items'] == 1
    payload = preview_archive(bundle_archive(BUNDLES / 'cas-1'))
    assert payload['errors'] == []
    assert payload['items']["Fletcher’s Ire"]['tags'] == ['bulky', 'charges']
    assert payload['items']['Curved Dagger']['tags'] == ['d6']


def test_warden_writes_edits_and_removes_items(warden):
    app, client = warden
    page = client.get('/campaigns/1/modules/1/').get_data(as_text=True)
    assert page.index('id="module-backgrounds-title"') < page.index('id="module-items-title"') < page.index('id="module-articles-title"')
    items = page[page.index('id="module-items-title"'):page.index('id="module-articles-title"')]
    assert '<span class="wiki-badge">bulky</span><span class="wiki-badge">charges 3/3</span>' in items and 'Send' in items
    # The description is below the name, tags and actions, at full width.
    assert items.index('module-item-actions') < items.index('class="module-item-description"')
    assert 'Lantern of the Drowned' in client.get('/campaigns/1/modules/1/item').get_data(as_text=True)
    saved = client.post('/campaigns/1/modules/1/item', data={'action': 'save', 'version': module_version(app),
                                                             'text': '### Rope [uses 3]\nFifty feet.'})
    assert saved.status_code == 302 and saved.location.endswith('/campaigns/1/modules/1/#items')
    # Renaming replaces it; a name already in the module is refused.
    client.post('/campaigns/1/modules/1/item?name=Rope', data={'action': 'save', 'version': module_version(app),
                                                               'text': '### Silk Rope [uses 3]\nFifty feet.'})
    taken = client.post('/campaigns/1/modules/1/item?name=Silk Rope', data={'action': 'save', 'version': module_version(app),
                                                                            'text': '### Moon Cloth\nTaken.'})
    assert taken.status_code == 200 and 'already has an item named' in taken.get_data(as_text=True)
    with app.app_context():
        items = db.session.get(Module, 1).items
        assert 'Rope' not in items and items['Silk Rope']['description'] == 'Fifty feet.'
    assert client.post('/campaigns/1/modules/1/item?name=Silk Rope',
                       data={'action': 'remove', 'version': module_version(app)}).status_code == 302
    with app.app_context():
        assert 'Silk Rope' not in db.session.get(Module, 1).items
    # The module's wiki lists them, for the Warden.
    wiki = client.get('/campaigns/1/modules/1/wiki/').get_data(as_text=True)
    assert 'id="wiki-home-items"' in wiki and 'id="item-the-eye-of-vuk"' in wiki
    # Open cards: the whole description, its tags and the buttons; nothing to unfold.
    items = wiki[wiki.index('id="wiki-home-items"'):wiki.index('</section>', wiki.index('id="wiki-home-items"'))]
    assert '<details' not in items and items.count('class="wiki-item-card"') == 3
    assert '<span class="wiki-badge">bulky</span><span class="wiki-badge">charges 3/3</span>' in items
    assert 'A WIL save is required every time it is put on.' in items
    assert 'name=Moon+Cloth&amp;next=wiki' in items and 'Remove' not in items  # Remove is in its editor.
    editor = client.get('/campaigns/1/modules/1/item?name=Moon Cloth&next=wiki').get_data(as_text=True)
    assert 'name="action" value="remove"' in editor and editor.count('name="next" value="wiki"') == 2
    assert 'value="remove"' not in client.get('/campaigns/1/modules/1/item').get_data(as_text=True)  # Not for a new one.
    removed = client.post('/campaigns/1/modules/1/item?name=Moon Cloth',
                          data={'action': 'remove', 'version': module_version(app), 'next': 'wiki'})
    assert removed.location.endswith('/campaigns/1/modules/1/wiki/#wiki-home-items')
    edited = client.post('/campaigns/1/modules/1/item?name=The Eye of Vuk&next=wiki',
                         data={'action': 'save', 'version': module_version(app), 'text': '### The Eye of Vuk\nIron.'})
    assert edited.location.endswith('/campaigns/1/modules/1/wiki/#wiki-home-items')
    wiki = client.get('/campaigns/1/modules/1/wiki/').get_data(as_text=True)
    # Its sidebar lists them on every page of the module's wiki, each opening on the home.
    sidebar = wiki[wiki.index('id="wiki-sidebar"'):wiki.index('</aside>')]
    assert sidebar.index('id="wiki-items-title"') < sidebar.index('wiki-articles-title')  # Articles last.
    # On the home, the module's items come after its articles.
    assert wiki.index('wiki-related') < wiki.index('id="wiki-home-items"')
    assert 'wiki-part' not in sidebar and '?part=' not in sidebar  # Its headings are labels.
    assert 'href="/campaigns/1/modules/1/wiki/#item-the-eye-of-vuk"' in sidebar and 'item-moon-cloth' not in sidebar
    with app.app_context():
        from app.models import ContentEntry
        entry = ContentEntry(owner_id=1, campaign_id=1, module_id=1, category='npc', title='Keeper', body='')
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id
    article = client.get(f'/campaigns/1/modules/1/wiki/{entry_id}/').get_data(as_text=True)
    assert 'href="/campaigns/1/modules/1/wiki/#item-the-eye-of-vuk"' in article
    login(client, 2)
    assert client.get('/campaigns/1/modules/1/item?name=Moon Cloth').status_code == 403


def test_send_copies_an_item_to_party_storage(warden):
    app, client = warden
    page = client.get('/campaigns/1/modules/1/item/send?name=Fletcher%27s Ire').get_data(as_text=True)
    assert '<optgroup label="Party 1">' in page and 'value="party:1:0"' in page and 'value="character:1:0"' in page
    assert 'party:2:' not in page and 'party:3:' not in page  # Only this campaign's parties.
    sent = client.post('/campaigns/1/modules/1/item/send', data={'name': "Fletcher's Ire", 'to': 'party:1:0'})
    assert sent.status_code == 302 and sent.location.endswith('/campaigns/1/modules/1/#items')
    client.post('/campaigns/1/modules/1/item/send', data={'name': "Fletcher's Ire", 'to': 'party:1:0', 'next': 'wiki'})
    with app.app_context():
        items = json.loads(db.session.get(Party, 1).items)
        assert [(i['name'], i['tags'], i['charges'], i['max_charges'], i['location']) for i in items] == \
            [("Fletcher's Ire", ['bulky', 'charges'], 3, 3, 0)] * 2
        assert items[0]['id'] != items[1]['id']
        assert "Fletcher's Ire" in db.session.get(Module, 1).items  # The module keeps its item.


def test_send_opens_a_modal_on_the_module_page_and_wiki(warden):
    app, client = warden
    for url in ('/campaigns/1/modules/1/', '/campaigns/1/modules/1/wiki/'):
        page = client.get(url).get_data(as_text=True)
        assert page.count('id="item-send-dialog"') == 1 and 'data-send-item="Moon Cloth"' in page
        dialog = page[page.index('id="item-send-dialog"'):page.index('</dialog>', page.index('id="item-send-dialog"'))]
        assert 'value="party:1:0"' in dialog and 'value="character:1:0"' in dialog and 'name="csrf_token"' in dialog
        assert f'name="next" value="{"wiki" if "wiki" in url else "module"}"' in dialog


def test_send_copies_an_item_to_a_character(warden):
    app, client = warden
    sent = client.post('/campaigns/1/modules/1/item/send', data={'name': 'The Eye of Vuk', 'to': 'character:1:0',
                                                                 'next': 'wiki'})
    assert sent.location.endswith('/campaigns/1/modules/1/wiki/#item-the-eye-of-vuk')
    with app.app_context():
        items = json.loads(db.session.get(Character, 1).items)
        assert [(i['name'], i['description']) for i in items] == \
            [('The Eye of Vuk', 'A heavy iron medallion.\n- A WIL save is required every time it is put on.')]


def test_send_refuses_full_containers_and_other_parties(warden):
    app, client = warden
    full = client.post('/campaigns/1/modules/1/item/send', data={'name': 'The Eye of Vuk', 'to': 'party:1:1'})
    assert full.status_code == 302 and full.location.endswith('/campaigns/1/modules/1/#items')
    with app.app_context():
        assert json.loads(db.session.get(Party, 1).items) == []
    # A petty item takes no slot: it fits.
    client.post('/campaigns/1/modules/1/item/send', data={'name': 'Moon Cloth', 'to': 'party:1:1'})
    with app.app_context():
        assert [i['name'] for i in json.loads(db.session.get(Party, 1).items)] == ['Moon Cloth']
    for to in ('party:2:0', 'party:3:0', 'character:2:0', 'party:1:9', 'party:1', 'ground:1:0'):
        assert client.post('/campaigns/1/modules/1/item/send', data={'name': 'Moon Cloth', 'to': to}).status_code == 400
    assert client.post('/campaigns/1/modules/1/item/send', data={'name': 'Nothing', 'to': 'party:1:0'}).status_code == 404
    login(client, 2)  # A player cannot send the Warden's items.
    assert client.post('/campaigns/1/modules/1/item/send', data={'name': 'Moon Cloth', 'to': 'character:1:0'}).status_code == 403


@pytest.mark.parametrize('kind', ['Relic', 'Spellbook', 'Item', 'Gear'])
def test_old_item_article_files_import_as_notes(app_with_babel, kind):
    with app_with_babel.app_context():
        payload = preview_archive(module_zip({'relic.md': f'---\nlayout: default\ntitle: Bell\ntype: {kind}\n---\nIt rings.'}))
        assert payload['errors'] == [] and payload['rows'][0]['category'] == 'note'


def test_old_item_articles_migrate_to_notes(app_with_babel):
    """Migration 511a01: item, relic and spellbook articles become Notes, their text kept."""
    import importlib.util
    from pathlib import Path
    from unittest.mock import patch
    from app.models import ContentEntry, User
    spec = importlib.util.spec_from_file_location('items_migration', Path('migrations/versions/511a01_item_articles_to_notes.py'))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='warden'))
        db.session.add(Campaign(id=1, owner_id=1, name='C'))
        for i, category in enumerate(('item', 'relic', 'spellbook', 'npc'), 1):
            db.session.add(ContentEntry(id=i, owner_id=1, campaign_id=1, category=category, title=category, body='Text'))
        db.session.commit()
        with patch.object(migration.op, 'execute', side_effect=lambda sql: db.session.execute(db.text(sql))):
            migration.upgrade()
        db.session.commit()
        assert [(e.category, e.body) for e in ContentEntry.query.order_by(ContentEntry.id)] == \
            [('note', 'Text'), ('note', 'Text'), ('note', 'Text'), ('npc', 'Text')]


def test_tools_saves_a_relic_as_a_module_item(warden):
    app, client = warden
    page = client.get('/materials/import-item').get_data(as_text=True)
    assert 'kw-item-result' in page and '<optgroup label="Secret campaign">' in page and 'Twin Lakes' in page
    text = '### Bloodmap [charges 1/1]\nA blank leather parchment.\n'
    saved = client.post('/materials/import-item', data={'module_id': 1, 'text': text})
    assert saved.status_code == 302 and saved.location.endswith('/campaigns/1/modules/1/#items')
    with app.app_context():
        assert db.session.get(Module, 1).items['Bloodmap'] == {
            'name': 'Bloodmap', 'tags': ['charges'], 'charges': 1, 'max_charges': 1, 'description': 'A blank leather parchment.'}
    again = client.post('/materials/import-item', data={'module_id': 1, 'text': text})
    assert again.status_code == 200 and 'already has an item named Bloodmap' in again.get_data(as_text=True)
    bad = client.post('/materials/import-item', data={'module_id': 1, 'text': 'No heading'})
    assert bad.status_code == 200 and 'role="alert"' in bad.get_data(as_text=True)
    login(client, 2)  # Only into my own modules.
    assert client.post('/materials/import-item', data={'module_id': 1, 'text': text}).status_code in (403, 404)


def test_wiki_sidebar_lists_maps_backgrounds_items_then_articles(warden):
    from app.lib.campaign_backgrounds import BACKGROUND_TEMPLATE, parse_background_text
    from app.models import ContentEntry
    app, client = warden
    with app.app_context():
        module = db.session.get(Module, 1)
        module.backgrounds = parse_background_text(BACKGROUND_TEMPLATE)
        entry = ContentEntry(owner_id=1, campaign_id=1, module_id=1, category='npc', title='Keeper', body='')
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id
    # On every page of the module's wiki, not only its home.
    page = client.get(f'/campaigns/1/modules/1/wiki/{entry_id}/').get_data(as_text=True)
    sidebar = page[page.index('id="wiki-sidebar"'):page.index('</aside>')]
    assert sidebar.index('id="wiki-backgrounds-title"') < sidebar.index('id="wiki-items-title"') < sidebar.index('wiki-articles-title')
    assert 'href="/campaigns/1/modules/1/wiki/#background-tidewatcher"' in sidebar

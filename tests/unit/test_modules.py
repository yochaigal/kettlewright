import re
from unittest.mock import patch

import pytest

from app.lib import modules
from app.lib.campaign_import import preview_archive
from app.lib.modules import BUNDLES, SOURCE, MODULES, add_module, bundle_archive
from app.models import db, Campaign, ContentEntry, Module, Party, User

DIRS = sorted(path for path in BUNDLES.glob('cas-*') if (path / 'campaign.md').is_file())
COUNT = len(MODULES)
FIRST, SECOND = DIRS[:2]


def title_of(path):
    return MODULES[path.name]['title']


@pytest.fixture
def user(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add(User(id=1, username='warden', email='warden@example.com'))
        db.session.add(Campaign(id=7, owner_id=1, name='Homebrew'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    return app, client


def home(client, campaign_id=7):
    """The campaign lobby, where the Modules Marketplace opens."""
    return client.get(f'/campaigns/{campaign_id}/').get_data(as_text=True)


def marketplace(page):
    start = page.index('id="marketplace-dialog"')
    return page[start:page.index('</dialog>', start)]


def add(client, slug, campaign_id=7):
    return client.post(f'/campaigns/{campaign_id}/marketplace/{slug}')


def test_cards_match_bundles_and_front_matter_titles():
    assert {path.name for path in DIRS} == set(MODULES)
    assert len({info['title'] for info in MODULES.values()}) == COUNT
    for path in DIRS:
        assert f'title: "{title_of(path)}"\n' in (path / 'campaign.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('path', DIRS, ids=lambda path: path.name)
def test_bundle_previews_clean_with_unique_titles(app, path):
    with app.app_context():
        payload = preview_archive(bundle_archive(path), None)
    assert payload['errors'] == [] and payload['warnings'] == []
    titles = [row['title'] for row in payload['rows']]
    assert len(titles) == len(set(titles)) and len(titles) > 1


@pytest.mark.parametrize('path', DIRS, ids=lambda path: path.name)
def test_card_link_matches_bundle_original(path):
    text = (path / 'campaign.md').read_text(encoding='utf-8')
    assert f'Original: {SOURCE.format(path.name)}' in text


def test_marketplace_offers_every_module_in_the_campaign_without_adding_any(user):
    app, client = user
    assert 'Free modules' not in client.get('/campaigns/').get_data(as_text=True)  # Not on the main view.
    dialog = marketplace(home(client))
    assert 'Modules Marketplace' in dialog
    for path in DIRS:
        assert title_of(path) in dialog and f'href="{SOURCE.format(path.name)}"' in dialog
        assert f'action="/campaigns/7/marketplace/{path.name}"' in dialog
    assert dialog.count('>Added<') == 0 and dialog.count('cairnrpg.com/adventures/first-party/img/') >= COUNT  # Covers.
    assert re.search(r'\d+ articles', dialog) and 'Yochai Gal' in dialog and 'CC-BY-SA 4.0' in dialog
    assert 'Upload module' in dialog and 'name="campaign_id" value="7"' in dialog
    with app.app_context():
        assert Module.query.count() == 0 and ContentEntry.query.count() == 0


def test_add_copies_the_module_into_the_campaign(user):
    app, client = user
    response = add(client, SECOND.name)
    with app.app_context():
        module = Module.query.one()
        assert module.campaign_id == 7 and module.slug == SECOND.name and module.title == title_of(SECOND)
        count = ContentEntry.query.filter_by(module_id=module.id).count()
        assert count > 1 and ContentEntry.query.count() == count
        # Its front page is its description, not an article named like the module.
        assert ContentEntry.query.filter_by(module_id=module.id, title=title_of(SECOND)).count() == 0
        assert 'CC-BY-SA 4.0' in module.description
        assert Campaign.query.count() == 1  # Never a new campaign.
        module_id = module.id
    assert response.status_code == 302 and response.location.endswith(f'/campaigns/7/modules/{module_id}/')
    page = client.get(response.location).get_data(as_text=True)
    assert f'{title_of(SECOND)} was added to Homebrew.' in page and 'class="toast"' in page
    dialog = marketplace(home(client))
    assert dialog.count('Added') == 1 and f'href="/campaigns/7/modules/{module_id}/"' in dialog
    assert f'action="/campaigns/7/marketplace/{SECOND.name}"' not in dialog


def test_adding_twice_does_not_duplicate(user):
    app, client = user
    add(client, FIRST.name)
    with app.app_context():
        count = ContentEntry.query.count()
    add(client, FIRST.name)
    with app.app_context():
        assert Module.query.count() == 1 and ContentEntry.query.count() == count


def test_older_module_named_after_the_adventure_counts_as_added(user):
    app, client = user
    with app.app_context():
        db.session.add(Module(campaign_id=7, title=title_of(FIRST)))
        db.session.commit()
    assert marketplace(home(client)).count('Added') == 1
    add(client, FIRST.name)
    with app.app_context():
        assert Module.query.count() == 1


def test_module_page_renames_exports_and_deletes(user):
    app, client = user
    add(client, FIRST.name)
    with app.app_context():
        module = Module.query.one()
        module_id, version = module.id, module.version
    page = client.get(f'/campaigns/7/modules/{module_id}/').get_data(as_text=True)
    assert 'category=note' not in page  # No New note on the module page.
    for link in (f'/materials/new?module_id={module_id}',
                 f'/materials/generate?module_id={module_id}',
                 f'/campaigns/7/modules/{module_id}/background'):
        assert link in page
    assert client.post(f'/campaigns/7/modules/{module_id}/', data={'name': 'Twin Lakes, my way', 'version': version}).status_code == 302
    assert 'Twin Lakes, my way' in home(client)
    assert f'/campaigns/7/modules/{module_id}/export' not in page  # Export is on the lobby's module card.
    assert f'/campaigns/7/modules/{module_id}/export' in home(client)
    assert client.get(f'/campaigns/7/modules/{module_id}/export').mimetype == 'application/zip'
    response = client.post(f'/campaigns/7/modules/{module_id}/delete', data={'version': version + 1})
    assert response.status_code == 302 and response.location.endswith('/campaigns/7/')
    with app.app_context():
        assert Module.query.count() == 0 and ContentEntry.query.count() == 0 and Campaign.query.count() == 1
    assert dialog_has_add(client, FIRST.name)


def dialog_has_add(client, slug):
    return f'action="/campaigns/7/marketplace/{slug}"' in marketplace(home(client))


def test_unknown_slug_foreign_campaign_and_logged_out(user):
    app, client = user
    with app.app_context():
        db.session.add(User(id=2, username='other'))
        db.session.add(Campaign(id=8, owner_id=2, name='Theirs'))
        db.session.commit()
    assert add(client, 'cas-99').status_code == 404
    assert client.post('/campaigns/7/marketplace/../../etc').status_code == 404
    assert add(client, FIRST.name, campaign_id=8).status_code == 403
    assert app.test_client().post(f'/campaigns/7/marketplace/{FIRST.name}').status_code == 302
    with app.app_context():
        assert ContentEntry.query.count() == 0


def test_csrf_token_is_required(user):
    app, client = user
    app.config['WTF_CSRF_ENABLED'] = True
    assert add(client, FIRST.name).status_code == 400
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', home(client)).group(1)
    assert client.post(f'/campaigns/7/marketplace/{FIRST.name}', data={'csrf_token': token}).status_code == 302


def test_failed_import_is_rolled_back_and_reported(user):
    app, client = user
    real = modules.import_preview

    def fail(payload, owner_id, **options):
        real(payload, owner_id, **options)
        raise RuntimeError('boom')

    with patch.object(modules, 'import_preview', fail):
        response = add(client, FIRST.name)
    assert response.status_code == 302 and response.location.endswith('/campaigns/7/')
    with app.app_context():
        assert Module.query.count() == 0 and ContentEntry.query.count() == 0
        assert db.session.get(Campaign, 7) is not None
    page = home(client)
    assert f'Could not add {title_of(FIRST)}' in page
    assert 'role="alert"' in page


def test_add_module_rejects_unknown_slug(user):
    app, _ = user
    with app.app_context(), pytest.raises(KeyError):
        add_module(db.session.get(Campaign, 7), 'cas-99')


def test_signup_adds_no_campaigns(app):
    with app.test_client() as client, app.app_context(), patch('app.blueprints.auth.send_email'):
        client.post('/signup', data={'email': 'new@example.com', 'user_name': 'newwarden',
                                     'password': 'Sup3r-secret-pass', 'password2': 'Sup3r-secret-pass'})
        created = User.query.filter_by(username='newwarden').first()
        assert created is not None
        assert Campaign.query.filter_by(owner_id=created.id).count() == 0


def test_cas4_map_article_holds_the_maps_and_every_events_table(user):
    """#508: everything to run the manor at the table is in one article, which links back from the others."""
    app, client = user
    assert add(client, 'cas-4').status_code == 302
    with app.app_context():
        entries = {entry.title: entry for entry in ContentEntry.query.filter_by(campaign_id=7)}
        reference, mansion, npcs = (entries[title] for title in (
            'Lockwood Manor Map & Dungeon Events', 'The Mansion', 'NPCs & Creatures'))
        ids = {title: entry.id for title, entry in entries.items()}
        body = reference.body
        assert body.index('iso-map.webp') < body.index('simple-map-white.webp') < body.index('### Dungeon Exploration Cycle')
        assert body.index('### Dungeon Exploration Cycle') < body.index('| d6 | Event |') < body.index('| d4  | Encounters') < body.index('| d4  | Environment')
        # Moved, not copied: the mansion and the bestiary point to it.
        for entry in (mansion, npcs):
            assert '[[Lockwood Manor Map & Dungeon Events]]' in entry.body and '| d4  | Encounters' not in entry.body
        assert 'Dungeon Events Table' not in mansion.body and 'iso-map.webp' not in npcs.body
    page = client.get(f"/campaigns/7/wiki/{ids['The Mansion']}/").get_data(as_text=True)
    assert f'/campaigns/7/wiki/{ids["Lockwood Manor Map & Dungeon Events"]}/">Lockwood Manor Map &amp; Dungeon Events</a>' in page
    # Articles load the table roller and the scrolling "On this page".
    assert 'id="table-roll-labels"' in page and 'src/js/table_rolls.js' in page and 'src/js/wiki_toc.js' in page

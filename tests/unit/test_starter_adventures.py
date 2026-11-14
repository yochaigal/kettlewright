import re
from unittest.mock import patch

import pytest

from app.lib import starter_adventures
from app.lib.campaign_import import preview_archive
from app.lib.starter_adventures import BUNDLES, SOURCE, STARTERS, add_starter_adventure, bundle_archive
from app.models import db, Campaign, ContentEntry, User

DIRS = sorted(path for path in BUNDLES.glob('cas-*') if (path / 'campaign.md').is_file())
COUNT = len(STARTERS)
FIRST, SECOND = DIRS[:2]


def title_of(path):
    return STARTERS[path.name]['title']


@pytest.fixture
def user(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add(User(id=1, username='warden', email='warden@example.com'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    return app, client


def campaigns_page(client):
    return client.get('/campaigns/').get_data(as_text=True)


def names():
    return {c.name for c in Campaign.query.filter_by(owner_id=1)}


def test_cards_match_bundles_and_front_matter_titles():
    assert {path.name for path in DIRS} == set(STARTERS)
    assert len({info['title'] for info in STARTERS.values()}) == COUNT
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


def test_campaigns_page_offers_every_adventure_without_adding_any(user):
    app, client = user
    page = campaigns_page(client)
    for path in DIRS:
        assert title_of(path) in page
        assert f'href="{SOURCE.format(path.name)}"' in page
    assert page.count('>Add<') == COUNT
    assert page.count('class="starter-icon"') == COUNT and page.count('target="_blank" rel="noopener"') == COUNT
    assert 'Read on Cairn' not in page
    assert '<h3 id="starter-heading">Free Starter Adventures</h3>' in page and 'materialTree({collapsed:true})' in page
    assert 'Remove' not in page
    with app.app_context():
        assert Campaign.query.count() == 0


def test_add_creates_only_that_campaign_and_card_shows_added(user):
    app, client = user
    response = client.post(f'/campaigns/starter/{SECOND.name}')
    assert response.status_code == 302 and response.location.endswith('/campaigns/')
    with app.app_context():
        assert names() == {title_of(SECOND)}
        campaign = Campaign.query.filter_by(owner_id=1).one()
        assert ContentEntry.query.filter_by(campaign_id=campaign.id).count() > 1
        campaign_id = campaign.id
    page = campaigns_page(client)
    assert f'{title_of(SECOND)} was added to your campaigns.' in page
    assert 'class="toast"' in page and '<p role="status">' not in page
    assert page.count('>Add<') == COUNT - 1
    assert f'href="/campaigns/{campaign_id}/"' in page and '>Remove<' in page
    assert '>Delete</button>' in page


def test_heading_stays_until_every_adventure_is_added(user):
    app, client = user
    for path in DIRS[:-1]:
        client.post(f'/campaigns/starter/{path.name}')
    assert 'starter-heading' in campaigns_page(client)
    client.post(f'/campaigns/starter/{DIRS[-1].name}')
    assert 'starter-heading' not in campaigns_page(client)


def test_adding_twice_does_not_duplicate(user):
    app, client = user
    client.post(f'/campaigns/starter/{FIRST.name}')
    with app.app_context():
        count = ContentEntry.query.count()
    client.post(f'/campaigns/starter/{FIRST.name}')
    with app.app_context():
        assert Campaign.query.count() == 1 and ContentEntry.query.count() == count


def test_same_named_campaign_counts_as_added_and_is_not_duplicated(user):
    app, client = user
    with app.app_context():
        db.session.add(Campaign(owner_id=1, name=title_of(FIRST)))
        db.session.commit()
    assert '>Remove<' in campaigns_page(client)
    client.post(f'/campaigns/starter/{FIRST.name}')
    with app.app_context():
        assert Campaign.query.count() == 1


def test_renamed_or_deleted_copy_restores_the_button(user):
    app, client = user
    client.post(f'/campaigns/starter/{FIRST.name}')
    with app.app_context():
        Campaign.query.one().name = 'My own name'
        db.session.commit()
    assert campaigns_page(client).count('>Add<') == COUNT
    client.post(f'/campaigns/starter/{SECOND.name}')
    with app.app_context():
        db.session.delete(Campaign.query.filter_by(name=title_of(SECOND)).one())
        db.session.commit()
    assert campaigns_page(client).count('>Add<') == COUNT


def test_remove_asks_for_confirmation_then_deletes_and_restores_add(user):
    app, client = user
    client.post(f'/campaigns/starter/{FIRST.name}')
    page = campaigns_page(client)
    action = re.search(r'action="(/campaigns/\d+/delete)"', page).group(1)
    version = re.search(r'name="version" value="(\d+)"', page).group(1)
    asked = client.post(action, data={'version': version})
    assert asked.status_code == 200 and 'Delete campaign?' in asked.get_data(as_text=True)
    with app.app_context():
        assert Campaign.query.count() == 1
    assert client.post(action, data={'version': version, 'confirm': 'delete'}).status_code == 302
    with app.app_context():
        assert Campaign.query.count() == 0 and ContentEntry.query.count() == 0
    page = campaigns_page(client)
    assert page.count('>Add<') == COUNT
    assert f'{title_of(FIRST)} was removed from your campaigns.' in page and 'class="toast"' in page


def test_unknown_slug_is_404_and_logged_out_is_redirected(user):
    app, client = user
    assert client.post('/campaigns/starter/cas-99').status_code == 404
    assert client.post('/campaigns/starter/../../etc').status_code == 404
    assert app.test_client().post(f'/campaigns/starter/{FIRST.name}').status_code == 302


def test_csrf_token_is_required(user):
    app, client = user
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(f'/campaigns/starter/{FIRST.name}').status_code == 400
    page = campaigns_page(client)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page).group(1)
    assert client.post(f'/campaigns/starter/{FIRST.name}', data={'csrf_token': token}).status_code == 302


def test_failed_import_is_rolled_back_and_reported(user):
    app, client = user
    real = starter_adventures.import_preview

    def fail(payload, owner_id):
        real(payload, owner_id)
        raise RuntimeError('boom')

    with patch.object(starter_adventures, 'import_preview', fail):
        response = client.post(f'/campaigns/starter/{FIRST.name}')
    assert response.status_code == 302
    with app.app_context():
        assert Campaign.query.count() == 0 and ContentEntry.query.count() == 0
        assert db.session.get(User, 1) is not None
    page = campaigns_page(client)
    assert f'Could not add {title_of(FIRST)}' in page
    assert 'role="alert"' in page and 'class="toast"' not in page


def test_add_starter_adventure_rejects_unknown_slug(user):
    app, _ = user
    with app.app_context(), pytest.raises(KeyError):
        add_starter_adventure(1, 'cas-99')


def test_signup_adds_no_campaigns(app):
    with app.test_client() as client, app.app_context(), patch('app.blueprints.auth.send_email'):
        client.post('/signup', data={'email': 'new@example.com', 'user_name': 'newwarden',
                                     'password': 'Sup3r-secret-pass', 'password2': 'Sup3r-secret-pass'})
        created = User.query.filter_by(username='newwarden').first()
        assert created is not None
        assert Campaign.query.filter_by(owner_id=created.id).count() == 0

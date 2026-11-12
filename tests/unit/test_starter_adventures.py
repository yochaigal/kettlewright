from unittest.mock import patch

import pytest

from app.lib import starter_adventures
from app.lib.campaign_import import preview_archive
from app.lib.starter_adventures import bundle_archive, bundle_dirs, bundle_title, seed_starter_adventures
from app.models import db, Campaign, ContentEntry, User

COUNT = len(bundle_dirs())


@pytest.fixture
def user(app):
    with app.app_context():
        user = User(username='warden', email='warden@example.com')
        db.session.add(user)
        db.session.commit()
        yield user.id


def test_bundles_are_present_and_titles_unique():
    titles = [bundle_title(path) for path in bundle_dirs()]
    assert COUNT >= 4 and len(set(titles)) == COUNT


@pytest.mark.parametrize('path', bundle_dirs(), ids=lambda path: path.name)
def test_bundle_previews_clean_with_unique_titles(app, path):
    with app.app_context():
        payload = preview_archive(bundle_archive(path), None)
    assert payload['errors'] == [] and payload['warnings'] == []
    titles = [row['title'] for row in payload['rows']]
    assert len(titles) == len(set(titles)) and len(titles) > 1


def test_seed_creates_all_campaigns_with_articles_and_is_idempotent(app, user):
    with app.app_context():
        assert seed_starter_adventures(user) == COUNT
        db.session.commit()
        campaigns = Campaign.query.filter_by(owner_id=user).all()
        assert sorted(c.name for c in campaigns) == sorted(bundle_title(p) for p in bundle_dirs())
        for campaign in campaigns:
            assert ContentEntry.query.filter_by(campaign_id=campaign.id).count() > 1
        count = ContentEntry.query.count()
        assert seed_starter_adventures(user) == 0
        db.session.commit()
        assert ContentEntry.query.count() == count


def test_dry_run_counts_without_creating(app, user):
    with app.app_context():
        assert seed_starter_adventures(user, dry_run=True) == COUNT
        assert Campaign.query.count() == 0


def test_seed_skips_campaign_user_already_has(app, user):
    with app.app_context():
        db.session.add(Campaign(owner_id=user, name=bundle_title(bundle_dirs()[0])))
        db.session.commit()
        assert seed_starter_adventures(user) == COUNT - 1


def test_failing_bundle_is_rolled_back_and_does_not_raise(app, user):
    real = starter_adventures.import_preview
    calls = iter(range(1, 100))

    def fail_second(payload, owner_id):
        real(payload, owner_id)
        if next(calls) == 2:
            raise RuntimeError('boom')

    with app.app_context(), patch.object(starter_adventures, 'import_preview', fail_second):
        assert seed_starter_adventures(user) == COUNT - 1
        db.session.commit()
        names = {c.name for c in Campaign.query.filter_by(owner_id=user)}
        assert len(names) == COUNT - 1
        assert db.session.get(User, user) is not None
        orphaned = ContentEntry.query.filter(~ContentEntry.campaign_id.in_(
            db.session.query(Campaign.id))).count()
        assert orphaned == 0


def test_signup_seeds_starter_adventures(app):
    with app.test_client() as client, app.app_context(), patch('app.blueprints.auth.send_email'):
        response = client.post('/signup', data={'email': 'new@example.com', 'user_name': 'newwarden',
                                                 'password': 'Sup3r-secret-pass', 'password2': 'Sup3r-secret-pass'})
        user = User.query.filter_by(username='newwarden').first()
        assert user is not None, response.status_code
        assert Campaign.query.filter_by(owner_id=user.id).count() == COUNT

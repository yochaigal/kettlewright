"""Terms of Service and Privacy Policy (#455), and the account deletion the policy describes."""
import json
from pathlib import Path

from app.models import Campaign, Character, Companion, ContentEntry, DiscordAccount, Party, User, db


def test_terms_and_privacy_are_public_and_linked(app_with_babel):
    app = app_with_babel
    client = app.test_client()
    for path, title in (('/terms', 'Terms of Service'), ('/privacy', 'Privacy Policy')):
        page = client.get(path)
        assert page.status_code == 200
        html = page.get_data(as_text=True)
        assert title in html and 'Last updated:' in html
        assert 'github.com/yochaigal/kettlewright/issues' in html
        assert 'This page is available in English only.' not in html
    assert 'href="/privacy"' in client.get('/terms').get_data(as_text=True)
    assert 'href="/terms"' in client.get('/privacy').get_data(as_text=True)
    for path in ('/signup', '/about', '/account/discord'):
        html = client.get(path).get_data(as_text=True)
        assert 'href="/terms"' in html and 'href="/privacy"' in html, path


def test_legal_pages_say_they_are_in_english(app):
    # The site's own language selector (?lang=), not the test fixture's fixed English.
    from flask_babel import Babel
    from app import get_locale
    Babel(app, locale_selector=get_locale)
    html = app.test_client().get('/privacy?lang=de').get_data(as_text=True)
    assert 'Diese Seite ist nur auf Englisch verfügbar.' in html
    assert 'Datenschutzerklärung' in html


def test_privacy_policy_matches_what_the_app_keeps(app_with_babel):
    app = app_with_babel
    """The policy names these periods; keep them in step with the code."""
    from app.lib.mfa import LIFETIME
    from app.lib.presence import TTL
    html = app.test_client().get('/privacy').get_data(as_text=True)
    assert LIFETIME == 600 and 'up to\n        10 minutes' in html
    assert TTL <= 90 and 'about a minute' in html
    assert 'for 24 hours' in html and '180 days' in html


def test_deleting_an_account_removes_its_uploaded_images(app_with_babel, tmp_path):
    app = app_with_babel
    portraits, images = tmp_path / 'portraits', tmp_path / 'material-images'
    app.config.update(PORTRAIT_UPLOAD_FOLDER=str(portraits), MATERIAL_IMAGE_UPLOAD_FOLDER=str(images))
    portraits.mkdir()
    (images / '1').mkdir(parents=True)
    names = {key: f'{key * 64}.webp' for key in 'abcd'}
    for name in names.values():
        (portraits / name).write_bytes(b'x')
    own, shown_elsewhere = 'c' * 32 + '.webp', 'd' * 32 + '.webp'
    for name in (own, shown_elsewhere):
        (images / '1' / name).write_bytes(b'x')
    with app.app_context():
        user = User(id=1, username='leaving', email='leaving@example.invalid')
        user.password = 'correct horse'
        db.session.add_all([user, User(id=2, username='staying', email='staying@example.invalid')])
        db.session.add_all([
            Character(id=1, owner=1, name='Mine', background='x', custom_image=True, image_url=f'/portraits/{names["a"]}'),
            # Another user's character uses the same uploaded portrait: it must stay.
            Character(id=2, owner=2, name='Theirs', background='x', custom_image=True, image_url=f'/portraits/{names["b"]}'),
            Character(id=3, owner=1, name='Mine too', background='x', custom_image=True, image_url=f'/portraits/{names["b"]}'),
            Party(id=1, owner=1, name='Mine', members='[]'),
            DiscordAccount(user_id=1, discord_id='111', display_name='Leaving'),
        ])
        db.session.flush()
        db.session.add_all([
            Companion(id=1, kind='hireling', party_id=1, name='Hireling', custom_image=True, image_url=f'/portraits/{names["c"]}'),
            Companion(id=2, kind='pet', hireling_id=1, name='Pet', custom_image=True, image_url=f'/portraits/{names["d"]}'),
            Campaign(id=1, owner_id=1, name='Mine'),
            ContentEntry(owner_id=2, title='Theirs', category='location', body=f'<img src="/material-images/1/{shown_elsewhere}">'),
        ])
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'], session['_fresh'] = '1', True
    assert client.post('/delete_account', data={'password': 'correct horse'}).status_code == 302
    with app.app_context():
        assert db.session.get(User, 1) is None and db.session.get(DiscordAccount, 1) is None
        assert Character.query.filter_by(owner=1).count() == 0 and db.session.get(Party, 1) is None
        assert db.session.get(Campaign, 1) is None
    assert sorted(path.name for path in portraits.iterdir()) == [names['b']]
    assert sorted(path.name for path in (images / '1').iterdir()) == [shown_elsewhere]


def test_wrong_password_deletes_nothing(app_with_babel, tmp_path):
    app = app_with_babel
    app.config['PORTRAIT_UPLOAD_FOLDER'] = str(tmp_path)
    (tmp_path / ('e' * 64 + '.webp')).write_bytes(b'x')
    with app.app_context():
        user = User(id=1, username='staying', email='staying@example.invalid')
        user.password = 'correct horse'
        db.session.add(user)
        db.session.add(Character(id=1, owner=1, name='Mine', background='x', custom_image=True, image_url='/portraits/' + 'e' * 64 + '.webp'))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'], session['_fresh'] = '1', True
    client.post('/delete_account', data={'password': 'wrong'})
    with app.app_context():
        assert db.session.get(User, 1) is not None
    assert (tmp_path / ('e' * 64 + '.webp')).exists()

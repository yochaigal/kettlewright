"""Starred parties (#476): bookmarks for anyone in a party, listed first on the Campaigns page."""
from app.models import db, PartyStar, Party
from tests.helpers import login
from tests.unit.test_campaigns import setup  # noqa: F401 (fixture)


def stars(app, user_id):
    with app.app_context():
        return [star.party_id for star in PartyStar.query.filter_by(user_id=user_id)]


def test_star_and_unstar_a_party(setup):
    app, client = setup
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'Starred' not in page
    response = client.post('/party/1/star', data={'starred': '1', 'next': '/users/user1/parties/party1/'})
    assert response.status_code == 302 and response.location.endswith('/users/user1/parties/party1/')
    assert stars(app, 1) == [1]
    client.post('/party/1/star', data={'starred': '1'})  # Twice is still one star.
    assert stars(app, 1) == [1]
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'Starred' in page and page.index('Starred') < page.index('class="campaign-gallery"')
    assert 'action="/party/1/star"' in page
    assert client.post('/party/1/star', data={'starred': '0'}).status_code == 302
    assert stars(app, 1) == []


def test_members_star_but_strangers_cannot(setup):
    app, client = setup
    login(client, 2)  # Plays in party 1.
    assert client.post('/party/1/star', data={'starred': '1'}).status_code == 302
    assert stars(app, 2) == [1]
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'Party 1' in page[page.index('Starred'):]
    assert client.post('/party/3/star', data={'starred': '1'}).status_code == 403
    assert stars(app, 2) == [1]


def test_redirect_stays_on_this_site(setup):
    app, client = setup
    for target in ('https://evil.example/', '//evil.example/', '/\\evil.example'):
        response = client.post('/party/1/star', data={'starred': '1', 'next': target})
        assert response.location.endswith('/campaigns/'), target


def test_a_party_left_or_deleted_drops_out(setup):
    app, client = setup
    login(client, 2)
    client.post('/party/1/star', data={'starred': '1'})
    with app.app_context():
        party = db.session.get(Party, 1)
        party.members = '[]'
        from app.models import Character
        db.session.get(Character, 1).party_id = None
        db.session.commit()
    assert 'Starred' not in client.get('/campaigns/').get_data(as_text=True)
    with app.app_context():
        db.session.delete(db.session.get(Party, 1))
        db.session.commit()
        assert PartyStar.query.count() == 0


def test_party_page_shows_the_star(setup):
    app, client = setup
    with app.app_context():
        from app.models import Character
        character = db.session.get(Character, 1)
        character.url_name, character.owner_username = 'player-a', 'user2'
        db.session.commit()
    page = client.get('/users/user1/parties/party1/', follow_redirects=True).get_data(as_text=True)
    assert 'action="/party/1/star"' in page and 'aria-pressed="false"' in page
    client.post('/party/1/star', data={'starred': '1'})
    page = client.get('/users/user1/parties/party1/', follow_redirects=True).get_data(as_text=True)
    assert 'aria-pressed="true"' in page

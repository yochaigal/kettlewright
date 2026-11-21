"""Stars (#476): bookmarks of parties, modules, articles, maps and backgrounds, first on the Campaigns page."""
from app.models import db, Party, Module, Star
from tests.helpers import login
from tests.unit.test_campaigns import setup, create_entry, create_map, map_entry_id, renderable_party_page  # noqa: F401


def stars(app, user_id=1):
    with app.app_context():
        return sorted((star.kind, star.target_id, star.name) for star in Star.query.filter_by(user_id=user_id))


def star(client, kind, target_id, name='', on=True, **extra):
    return client.post('/stars', data={'kind': kind, 'target_id': target_id, 'name': name,
                                       'starred': '1' if on else '0', **extra})


def first_module(app):
    with app.app_context():
        module = Module.query.filter_by(campaign_id=1).order_by(Module.id).first()
        return module.id, module.version


def add_background(app, client):
    from app.lib.campaign_backgrounds import BACKGROUND_TEMPLATE
    module_id, version = first_module(app)
    response = client.post(f'/campaigns/1/modules/{module_id}/background',
                           data={'version': version, 'action': 'save', 'text': BACKGROUND_TEMPLATE})
    assert response.status_code == 302, response.text
    with app.app_context():
        return module_id, next(iter(db.session.get(Module, module_id).backgrounds))


def test_star_and_unstar_everything_on_the_campaigns_island(setup):
    app, client = setup
    assert 'starred-island' not in client.get('/campaigns/').text
    entry_id = create_entry(client, title='Lighthouse')
    map_id, _ = create_map(client, title='Coast map', nodes=0)
    map_entry = map_entry_id(app, map_id)
    module_id, background = add_background(app, client)
    response = star(client, 'party', 1, next='/users/user1/parties/party1/')
    assert response.status_code == 302 and response.location.endswith('/users/user1/parties/party1/')
    for kind, target, name in (('module', module_id, ''), ('article', entry_id, ''), ('map', map_entry, ''),
                               ('background', module_id, background)):
        assert star(client, kind, target, name).status_code == 302
    star(client, 'party', 1)  # Twice is still one star.
    assert len(stars(app)) == 5
    page = client.get('/campaigns/').text
    island = page[page.index('class="starred-island"'):page.index('</section>', page.index('class="starred-island"'))]
    assert page.index('starred-island') < page.index('class="campaign-gallery"')
    for text in ('Party 1', 'Lighthouse', 'Coast map', background, f'/campaigns/1/wiki/{entry_id}/',
                 f'/campaigns/1/modules/{module_id}/wiki/#background-'):
        assert text in island, text
    assert island.count('class="star-button"') == 5 and island.count('aria-pressed="true"') == 5
    assert '<h3' not in island and '<h2' not in island  # No heading: just the cards.
    star(client, 'article', entry_id, on=False)
    assert ('article', entry_id, '') not in stars(app)


def test_the_star_buttons_show_where_things_are_read(setup):
    app, client = setup
    entry_id = create_entry(client)
    module_id, background = add_background(app, client)
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').text
    assert 'name="kind" value="article"' in page and f'name="target_id" value="{entry_id}"' in page
    home = client.get(f'/campaigns/1/modules/{module_id}/wiki/').text
    assert 'name="kind" value="module"' in home
    # The module's backgrounds are in its wiki, each with a star.
    assert 'id="wiki-home-backgrounds"' in home and background in home and 'name="kind" value="background"' in home
    star(client, 'module', module_id)
    assert 'aria-pressed="true"' in client.get(f'/campaigns/1/modules/{module_id}/wiki/').text


def test_only_what_you_can_open(setup):
    app, client = setup
    entry_id = create_entry(client)
    module_id, _ = first_module(app)
    assert star(client, 'party', 3).status_code == 404  # Someone else's party.
    assert star(client, 'background', module_id, 'No such background').status_code == 404
    assert star(client, 'nonsense', 1).status_code == 400
    login(client, 2)  # A player in party 1.
    assert star(client, 'party', 1).status_code == 302
    assert star(client, 'article', entry_id).status_code == 404  # The Warden's article.
    assert star(client, 'module', module_id).status_code == 404
    assert stars(app, 2) == [('party', 1, '')]


def test_redirect_stays_on_this_site(setup):
    app, client = setup
    for target in ('https://evil.example/', '//evil.example/', '/\\evil.example'):
        assert star(client, 'party', 1, next=target).location.endswith('/campaigns/'), target


def test_deleted_or_unreachable_drop_out(setup):
    app, client = setup
    entry_id = create_entry(client, title='Doomed')
    star(client, 'article', entry_id)
    login(client, 2)
    star(client, 'party', 1)
    with app.app_context():
        from app.models import Character, ContentEntry
        db.session.get(Character, 1).party_id = None
        db.session.get(Party, 1).members = '[]'
        db.session.delete(db.session.get(ContentEntry, entry_id))
        db.session.commit()
    assert 'starred-island' not in client.get('/campaigns/').text
    assert stars(app, 2) == []  # Removed when listed.
    login(client, 1)
    assert 'Doomed' not in client.get('/campaigns/').text and stars(app, 1) == []


def test_party_page_star(setup):
    app, client = setup
    renderable_party_page(app)
    page = client.get('/users/user1/parties/party1/').text
    assert 'name="kind" value="party"' in page and 'aria-pressed="false"' in page
    star(client, 'party', 1)
    assert 'aria-pressed="true"' in client.get('/users/user1/parties/party1/').text

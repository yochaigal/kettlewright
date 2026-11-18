"""Reading a campaign as a wiki (#421) and the campaign page header (#420)."""
import json
import re

import pytest

from app.models import Campaign, ContentEntry, ContentLink, db
from tests.unit.test_campaigns import create_entry, create_map, login, map_entry_id, reveal, setup  # noqa: F401


def wiki(client, entry_id=None, campaign_id=1):
    return client.get(f'/campaigns/{campaign_id}/wiki/' + (f'{entry_id}/' if entry_id else ''))


def build(app, client):
    guild = create_entry(client, category='faction', title='Ash Guild',
                         body='Bellmakers.\n\n## History\n\nOld.\n\n## Members\n\nLed by [[Mira]].')
    mira = create_entry(client, category='npc', title='Mira', body='The guildmaster.', parent_id=guild)
    town = create_entry(client, category='settlement', title='Thornwick', is_heart='on', body='A market town.')
    relic = create_entry(client, category='relic', title='Bell of Ash', body='It rings at dusk.')
    with app.app_context():
        db.session.add(ContentLink(source_id=relic, target_id=guild))  # A related article.
        db.session.commit()
    return guild, mira, town, relic


def test_home_groups_articles_and_highlights_hearts(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    page = wiki(client).get_data(as_text=True)
    assert '<h1>Secret campaign</h1>' in page
    assert '4 articles' in page
    for group in ('Factions', 'POIs', 'Items'):
        assert f'<h2>{group} <small>1</small></h2>' in page
    assert '<h2>People' not in page  # Mira sits inside the guild, so only the top level is grouped.
    assert page.count(f'href="/campaigns/1/wiki/{town}/"') == 3  # Heart section, its group, the sidebar.
    assert 'A market town.' in page  # Card excerpt.
    assert 'href="/campaigns/1/"' in page  # Edit goes back to the editing view.


def test_home_opens_with_the_campaign_front_page(setup):
    app, client = setup
    guild = build(app, client)[0]
    with app.app_context():
        # Imported adventures carry an overview article named after the campaign.
        db.session.add(ContentEntry(id=900, owner_id=1, campaign_id=1, category='overview',
                                    title='Secret campaign', body='Welcome. Start with the [[Ash Guild]].'))
        db.session.commit()
    page = wiki(client).get_data(as_text=True)
    intro = page[page.index('wiki-intro'):]
    assert 'Welcome.' in intro
    assert re.search(rf'<a [^>]*href="/campaigns/1/wiki/{guild}/"[^>]*>Ash Guild</a>', intro)
    assert 'href="/campaigns/1/wiki/900/"' in intro
    assert '<h2>Notes' not in page  # The front page is not listed again as a card.


def test_article_page_links_breadcrumbs_and_backlinks(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    page = wiki(client, guild).get_data(as_text=True)
    assert '<h1>Ash Guild</h1>' in page
    # The [[Mira]] link opens Mira's wiki page, not her editor.
    assert re.search(rf'<a [^>]*href="/campaigns/1/wiki/{mira}/"[^>]*>Mira</a>', page)
    assert f'href="/materials/{mira}/edit"' not in page
    # Mira is a sub-article; the Bell links here.
    assert 'In this article' in page
    assert 'Linked from' in page and f'href="/campaigns/1/wiki/{relic}/"' in page
    # Two headings make a table of contents pointing at their anchors.
    assert 'On this page' in page and 'href="#kw-h-history"' in page and 'id="kw-h-history"' in page
    assert f'href="/materials/{guild}/edit"' in page  # Edit button.
    assert 'aria-current="page">Ash Guild</a>' in page

    mira_page = wiki(client, mira).get_data(as_text=True)
    crumbs = mira_page[mira_page.index('class="wiki-crumbs"'):mira_page.index('class="wiki-header"')]
    assert 'Secret campaign' in crumbs and f'href="/campaigns/1/wiki/{guild}/"' in crumbs
    assert 'Linked from' in mira_page  # The guild links to Mira.

    relic_page = wiki(client, relic).get_data(as_text=True)
    assert 'Links to' in relic_page and f'href="/campaigns/1/wiki/{guild}/"' in relic_page


def test_empty_article_offers_to_edit(setup):
    app, client = setup
    entry = create_entry(client, title='Blank', body='')
    page = wiki(client, entry).get_data(as_text=True)
    assert 'This article has no text yet.' in page
    assert 'On this page' not in page and 'Linked from' not in page


def test_map_article_shows_its_map_read_only(setup):
    app, client = setup
    map_id, _graph = create_map(client)
    page = wiki(client, map_entry_id(app, map_id)).get_data(as_text=True)
    assert 'x-data="pointcrawl"' in page and 'data-editing="false"' in page
    assert 'data-save-url' not in page
    assert 'In this article' in page and 'SECRET ROOM 0' in page  # The map's points are its sub-articles.


def test_wiki_is_private_to_the_owner(setup):
    app, client = setup
    guild = build(app, client)[0]
    login(client, 2)
    assert wiki(client).status_code == 403
    assert wiki(client, guild).status_code == 403


def test_article_must_belong_to_the_campaign(setup):
    app, client = setup
    with app.app_context():
        db.session.add(Campaign(id=2, owner_id=1, name='Other campaign'))
        db.session.commit()
    guild = build(app, client)[0]
    assert wiki(client, guild, campaign_id=2).status_code == 404
    assert wiki(client, 999).status_code == 404
    assert wiki(client, campaign_id=999).status_code == 404


def test_campaign_page_links_to_the_wiki_and_drops_the_tools_button(setup):
    app, client = setup
    page = client.get('/campaigns/1/').get_data(as_text=True)
    assert 'href="/campaigns/1/wiki/"' in page
    header = page[page.index('class="campaign-page-header"'):page.index('campaign-shared-with')]
    assert '/tools/' not in header  # #420: Tools is already in the top navigation.


def test_editor_links_to_the_article_page(setup):
    app, client = setup
    entry = create_entry(client)
    page = client.get(f'/materials/{entry}/edit').get_data(as_text=True)
    assert f'href="/campaigns/1/wiki/{entry}/"' in page


# ----- Campaigns gallery: read by default, covers from article images -----

PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAwS2OUAAAAABJRU5ErkJggg=='


def card(page, campaign_id=1):
    start = page.index(f'href="/campaigns/{campaign_id}/wiki/"')
    return page[page.rfind('<li class="campaign-card"', 0, start):page.index('</li>', start)]


def test_campaign_cards_open_to_read_and_offer_edit(setup):
    app, client = setup
    build(app, client)
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'class="campaign-gallery"' in page and '<details class="campaign-tree-root' not in page
    first = card(page)
    assert 'class="campaign-card-title" href="/campaigns/1/wiki/"' in first  # Reading is the default.
    assert 'href="/campaigns/1/"' in first and '>Edit' in first.replace('</i> ', '>')
    assert '4 articles' in first and 'Not revealed to any party yet' in first  # Worked out from reveals.
    assert 'data-search="secret campaign ' in first and 'ash guild' in first  # Search finds articles too.
    assert 'campaign-card-placeholder' in first  # No image anywhere yet.
    assert client.get('/campaigns/1/cover').status_code == 404


def set_body(app, entry_id, body):
    """Write a body as older rows hold it, skipping the hooks that store uploads on save."""
    with app.app_context():
        db.session.execute(db.update(ContentEntry).where(ContentEntry.id == entry_id).values(body=body))
        db.session.commit()


def test_cover_prefers_the_front_page(setup):
    app, client = setup
    create_entry(client, title='Map room', body='![first](https://example.org/room.png)')
    with app.app_context():
        # Saving stores the inline upload as a material image file.
        db.session.add(ContentEntry(id=900, owner_id=1, campaign_id=1, category='overview',
                                    title='Secret campaign', body=f'Intro.\n\n![cover]({PNG})'))
        db.session.commit()
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'src="/campaigns/1/cover"' in card(page)
    response = client.get('/campaigns/1/cover')
    assert response.status_code == 302 and '/material-images/1/' in response.location
    assert client.get(response.location).status_code == 200
    home = wiki(client).get_data(as_text=True)
    assert 'class="wiki-cover" src="/campaigns/1/cover"' in home


def test_older_inline_images_are_served_as_files(setup):
    app, client = setup
    entry = create_entry(client, title='Old article', body='x')
    set_body(app, entry, f'![cover]({PNG})')
    response = client.get('/campaigns/1/cover')
    assert response.status_code == 200 and response.mimetype == 'image/png'
    assert response.data.startswith(b'\x89PNG')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_cover_links_to_remote_images(setup):
    app, client = setup
    create_entry(client, title='Pictures', body='<p>Text</p><img src="https://example.org/a.png" alt="">')
    response = client.get('/campaigns/1/cover')
    assert response.status_code == 302 and response.location == 'https://example.org/a.png'


@pytest.mark.parametrize('body', ['![x](javascript:alert(1))', '![x](data:text/html;base64,PHNjcmlwdD4=)',
                                  '<img src="//example.org/a.png">', 'No images.'])
def test_unsafe_or_missing_images_give_no_cover(setup, body):
    app, client = setup
    entry = create_entry(client, title='Pictures', body='x')
    set_body(app, entry, body)
    assert client.get('/campaigns/1/cover').status_code == 404
    assert 'campaign-card-placeholder' in client.get('/campaigns/').get_data(as_text=True)


def test_cover_is_private_to_the_owner(setup):
    app, client = setup
    create_entry(client, title='Pictures', body='![x](https://example.org/a.png)')
    login(client, 2)
    assert client.get('/campaigns/1/cover').status_code == 403


# ----- "Create new" dialog: random generation options -----

def test_create_dialog_offers_random_generation_with_defaults(setup):
    app, client = setup
    page = client.get('/campaigns/').get_data(as_text=True)
    dialog = page[page.index('<dialog class="create-dialog"'):page.index('</dialog>')]
    assert 'x-data="newCampaign"' in dialog and 'Generate it randomly' in dialog
    assert '<select name="map_kind" x-model="kind">' in dialog
    assert 'name="poi_count"' in dialog and '<option value="">Random count</option>' in dialog
    assert 'name="generate_children" value="1" x-model="children"' in dialog
    assert 'name="forest_chance" min="0" max="100" value="50"' in dialog
    assert 'name="dungeon_chance" min="0" max="100" value="25"' in dialog


def test_dialog_creates_an_empty_campaign_and_opens_it(setup):
    app, client = setup
    response = client.post('/campaigns/create', data={'kind': 'campaign', 'name': 'Quiet world', 'start': 'empty'})
    with app.app_context():
        campaign = Campaign.query.filter_by(name='Quiet world').one()
        assert not campaign.entries
    assert response.location.endswith(f'/campaigns/{campaign.id}/')


def test_dialog_saves_a_generated_dungeon_with_the_campaign(setup):
    app, client = setup
    draft = {'nodes': [{'id': 'new-1', 'title': 'Gate', 'category': 'room', 'number': 1, 'x': 0, 'y': 0}], 'edges': []}
    response = client.post('/campaigns/create', data={'kind': 'campaign', 'name': 'Deep world', 'start': 'random',
        'map_kind': 'dungeon', 'title': 'The Sunken Vault', 'body': 'Damp stone.', 'draft': json.dumps(draft)})
    with app.app_context():
        campaign = Campaign.query.filter_by(name='Deep world').one()
        dungeon = ContentEntry.query.filter_by(campaign_id=campaign.id, title='The Sunken Vault').one()
        assert dungeon.pointcrawl.kind == 'dungeon'
    assert response.location.endswith(f'/campaigns/{campaign.id}/')


def test_dialog_falls_back_to_the_generator_with_its_options(setup):
    app, client = setup
    response = client.post('/campaigns/create', data={'kind': 'campaign', 'name': 'Wild world', 'start': 'random',
        'map_kind': 'forest', 'poi_count': '8', 'generate_children': '1', 'dungeon_chance': '40'})
    location = response.location
    assert '/materials/generate?' in location and 'kind=forest' in location
    assert 'children=1' in location and 'forest_pois=40' in location and 'pois=8' in location


def test_wiki_undoes_global_aside_and_article_styles():
    css = open('app/static/src/css/campaigns.css').read()
    rule = css[css.index('aside:where(.campaign-wiki *)'):]
    rule = rule[:rule.index('}')]
    for declaration in ('float:none', 'width:auto', 'max-width:none', 'margin:0', 'border-left:0'):
        assert declaration in rule


# ----- Unfiled articles read the same way -----

def unfiled(client, **values):
    result = client.post('/materials/new', data={'category': 'note', 'title': 'Loose', 'body': 'x', **values})
    assert result.status_code == 302
    return int(re.search(r'/materials/(\d+)/edit', result.location).group(1))


def test_unfiled_articles_have_a_wiki(setup):
    app, client = setup
    rumor = unfiled(client, title='Rumor', body='Whispers.')
    tavern = unfiled(client, title='Tavern notes', body='Ask about the [[Rumor]].\n\n## Prices\n\nCheap.\n\n## Staff\n\nGrim.')
    in_campaign = create_entry(client, title='Campaign only')
    home = client.get('/materials/wiki/').get_data(as_text=True)
    assert '<h1>Unfiled articles</h1>' in home and '2 articles' in home
    assert f'href="/materials/wiki/{tavern}/"' in home and 'Campaign only' not in home
    assert 'href="/materials/"' in home  # Edit opens the library.
    page = client.get(f'/materials/wiki/{tavern}/').get_data(as_text=True)
    assert re.search(rf'<a [^>]*href="/materials/wiki/{rumor}/"[^>]*>Rumor</a>', page)
    assert 'On this page' in page and f'href="/materials/{tavern}/edit"' in page
    assert 'Linked from' in client.get(f'/materials/wiki/{rumor}/').get_data(as_text=True)
    assert client.get(f'/materials/wiki/{in_campaign}/').status_code == 404
    login(client, 2)
    assert client.get(f'/materials/wiki/{tavern}/').status_code == 403
    assert 'Rumor' not in client.get('/materials/wiki/').get_data(as_text=True)


def test_gallery_and_editors_link_unfiled_reading(setup):
    app, client = setup
    note = unfiled(client)
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'class="campaign-card-title" href="/materials/wiki/"' in page and 'href="/materials/"' in page
    assert 'href="/materials/wiki/"' in client.get('/materials/').get_data(as_text=True)
    assert f'href="/materials/wiki/{note}/"' in client.get(f'/materials/{note}/edit').get_data(as_text=True)


# ----- Reveal from read mode -----

def test_owner_reveals_from_the_article_page(setup):
    app, client = setup
    entry = create_entry(client)
    page = wiki(client, entry).get_data(as_text=True)
    assert f'id="reveal-dialog-{entry}"' in page and f'action="/materials/{entry}/reveal"' in page and 'Reveal to party' in page
    assert 'Revealed · ' not in page
    assert reveal(client, entry).status_code == 302
    assert 'Revealed · 1' in wiki(client, entry).get_data(as_text=True)


# ----- Players read revealed articles as wiki pages -----

def test_players_read_only_published_versions(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    assert reveal(client, guild, title='The Guild', body='Bell people.\n\n## Rumors\n\nMany.\n\n## Dues\n\nHigh.').status_code == 302
    assert reveal(client, relic, title='A bell', body='It rings. See the [[Ash Guild]].').status_code == 302
    login(client, 2)
    page = client.get(f'/party/1/materials/{guild}').get_data(as_text=True)
    assert 'class="wiki-layout"' in page and 'id="party-content-results"' in page
    assert '<h1>The Guild</h1>' in page and 'Bell people.' in page and 'On this page' in page
    # Only published titles and bodies: never the private original or unrevealed articles.
    for secret in ('Bellmakers', 'Ash Guild</a>', 'Mira', 'Thornwick', 'It rings at dusk'):
        assert secret not in page
    assert f'/party/1/materials/{mira}' not in page and f'/party/1/materials/{town}' not in page
    # The bell's published [[link]] and its related link both point here.
    assert 'Linked from' in page and f'href="/party/1/materials/{relic}"' in page
    assert f'/materials/{guild}/edit' not in page and '/reveal' not in page  # No Warden tools for players.
    assert '← Back to party' in page and 'href="/users/user1/parties/party1/#campaign-details"' in page


def test_party_wiki_home_groups_only_revealed_articles(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    empty = client.get('/party/1/wiki/').get_data(as_text=True)
    assert 'Nothing has been revealed yet.' in empty and '0 articles' in empty
    assert reveal(client, guild, title='The Guild', body='Bell people.').status_code == 302
    assert reveal(client, relic, title='A bell', body='It rings.').status_code == 302
    login(client, 2)
    page = client.get('/party/1/wiki/').get_data(as_text=True)
    assert 'class="wiki-layout"' in page and 'id="party-content-results"' in page  # Refreshes live like article pages.
    assert '2 articles' in page
    for group in ('Factions', 'Items'):
        assert f'<h2>{group} <small>1</small></h2>' in page
    assert f'href="/party/1/materials/{guild}"' in page and 'Bell people.' in page
    # No private originals, unrevealed articles, campaign cover or Warden tools.
    for secret in ('Bellmakers', 'Ash Guild', 'Mira', 'Thornwick', 'It rings at dusk', 'Secret campaign',
                   'wiki-cover', '/edit', 'New article'):
        assert secret not in page
    assert 'aria-current="page"' in page  # The sidebar's home link is this page.
    assert 'href="/users/user1/parties/party1/#campaign-details"' in page  # Back to party.


def test_party_wiki_home_links_and_access(setup):
    app, client = setup
    entry = create_entry(client)
    assert reveal(client, entry).status_code == 302
    page = client.get(f'/party/1/materials/{entry}').get_data(as_text=True)
    assert 'class="wiki-campaign-name" href="/party/1/wiki/"' in page  # Sidebar home is the party wiki.
    assert '← Back to party' in page and 'href="/users/user1/parties/party1/#campaign-details"' in page
    login(client, 3)
    assert client.get('/party/1/wiki/').status_code == 403


def test_party_owner_edits_the_party_version_from_the_article(setup):
    app, client = setup
    entry = create_entry(client)
    assert reveal(client, entry).status_code == 302
    page = client.get(f'/party/1/materials/{entry}').get_data(as_text=True)
    assert f'href="/party/1/materials/{entry}/version"' in page and 'Edit party version' in page
    assert f'/materials/{entry}/edit' not in page and 'Private original' not in page
    assert f'/materials/{entry}/reveal' not in page


def test_party_map_stays_outside_the_refreshed_content(setup):
    app, client = setup
    map_id, _graph = create_map(client)
    entry = map_entry_id(app, map_id)
    assert reveal(client, entry).status_code == 302
    login(client, 2)
    page = client.get(f'/party/1/materials/{entry}').get_data(as_text=True)
    results = page.index('id="party-content-results"')
    content = page[results:page.index('x-data="pointcrawl"')]
    assert content.count('<div') <= content.count('</div>')  # The map panel is not inside the refreshed container.

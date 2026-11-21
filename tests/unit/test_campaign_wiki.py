"""Reading a campaign as a wiki (#421) and the campaign page header (#420)."""
import json
import re
from pathlib import Path

import pytest

from app.models import Campaign, ContentEntry, ContentLink, db
from tests.unit.test_campaigns import create_entry, create_map, login, map_entry_id, reveal, setup  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]


def wiki(client, entry_id=None, campaign_id=1):
    return client.get(f'/campaigns/{campaign_id}/wiki/' + (f'{entry_id}/' if entry_id else ''))


def build(app, client):
    guild = create_entry(client, category='faction', title='Ash Guild',
                         body='Bellmakers.\n\n## History\n\nOld.\n\n## Members\n\nLed by [[Mira]].')
    mira = create_entry(client, category='npc', title='Mira', body='The guildmaster.', parent_id=guild)
    town = create_entry(client, category='settlement', title='Thornwick', is_heart='on', body='A market town.')
    relic = create_entry(client, category='lore', title='Bell of Ash', body='It rings at dusk.')
    with app.app_context():
        db.session.add(ContentLink(source_id=relic, target_id=guild))  # A related article.
        db.session.commit()
    return guild, mira, town, relic


def test_home_groups_articles_and_highlights_hearts(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    page = wiki(client).get_data(as_text=True)
    assert '<h1>Secret campaign</h1>' in page and 'campaign-rename' not in page  # Reading only; the lobby renames it.
    assert '4 articles' in page
    for group in ('Factions', 'POIs', 'Dungeon'):
        assert f'<h2>{group} <small>1</small></h2>' in page
    assert '<h2>People' not in page  # Mira sits inside the guild, so only the top level is grouped.
    # Heart section and its group (picture and title on each card), and the sidebar.
    assert page.count(f'href="/campaigns/1/wiki/{town}/"') == 5
    assert 'A market town.' in page  # Card excerpt.


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
    assert 'Welcome.' not in client.get('/campaigns/1/').get_data(as_text=True)  # Not in the lobby.
    assert re.search(rf'<a [^>]*href="/campaigns/1/wiki/{guild}/"[^>]*>Ash Guild</a>', intro)
    assert 'href="/campaigns/1/wiki/900/"' in intro
    assert '<h2>Notes' not in page  # The front page is not listed again as a card.


def test_article_page_links_breadcrumbs_and_backlinks(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    page = wiki(client, guild).get_data(as_text=True)
    assert '<h1>Ash Guild<' in page
    # The [[Mira]] link opens Mira's wiki page, not her editor.
    text = page[page.index('class="rich-content"'):page.index('In this article')]
    assert re.search(rf'<a [^>]*href="/campaigns/1/wiki/{mira}/"[^>]*>Mira</a>', page)
    assert f'href="/materials/{mira}/edit"' not in text  # Her card below has Edit; the link in the text reads.
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


def test_map_page_shows_its_map_read_only_apart_from_articles(setup):
    app, client = setup
    map_id, _graph = create_map(client)
    page = wiki(client, map_entry_id(app, map_id)).get_data(as_text=True)
    assert 'x-data="pointcrawl"' in page and 'data-editing="false"' in page
    assert 'data-save-url' not in page
    assert 'Reveal map' in page and f'href="/maps/{map_id}/edit"' in page and 'SECRET ROOM 0' in page
    sidebar = page[page.index('id="wiki-sidebar"'):page.index('</aside>')]
    # Maps have their own section in the sidebar, first; the article tree holds the points (articles), not the map.
    maps = sidebar[sidebar.index('class="wiki-maps"'):sidebar.index('class="wiki-articles-title"')]
    assert 'SECRET MAP' in maps
    assert 'SECRET MAP' not in sidebar[sidebar.index('class="wiki-tree"'):]
    home = wiki(client).get_data(as_text=True)
    main = home[home.index('class="wiki-main"'):]
    assert 'id="wiki-home-maps"' in main and main.index('SECRET ROOM 0') < main.index('id="wiki-home-maps"')  # Maps below.


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


def test_campaign_lobby_renames_with_the_pencil_and_has_no_edit_view(setup):
    app, client = setup
    home = client.get('/campaigns/1/').get_data(as_text=True)
    header = home[home.index('class="wiki-header lobby-header"'):home.index('</header>', home.index('class="wiki-header lobby-header"'))]
    assert 'campaign-rename' in header and '>Edit<' not in header and 'Export' not in header and '/tools/' not in header
    assert 'wiki-badge' not in header  # Just the name, centred.
    dialog = home[home.index('id="campaign-settings-dialog"'):home.index('</dialog>', home.index('id="campaign-settings-dialog"'))]
    assert 'action="/campaigns/1/"' in dialog and 'name="name"' in dialog and 'action="/campaigns/1/delete"' in dialog
    assert 'name="image"' in dialog  # A name and, optionally, its picture (#476).
    assert client.post('/campaigns/1/', data={'name': 'Renamed', 'version': 1}).location.endswith('/campaigns/1/')
    assert '<h1>Renamed' in client.get('/campaigns/1/').get_data(as_text=True)
    assert '<h1>Renamed</h1>' in client.get('/campaigns/1/wiki/').get_data(as_text=True)  # No pencil in the wiki.
    assert client.get('/campaigns/1/export').status_code == 404  # Modules are exported, one by one.


def test_editor_links_to_the_article_page(setup):
    app, client = setup
    entry = create_entry(client)
    page = client.get(f'/materials/{entry}/edit').get_data(as_text=True)
    assert f'href="/campaigns/1/wiki/{entry}/"' in page


# ----- Campaigns gallery: read by default, covers from article images -----

PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAwS2OUAAAAABJRU5ErkJggg=='


def card(page, campaign_id=1):
    start = page.index(f'class="campaign-card-title" href="/campaigns/{campaign_id}/"')
    return page[page.rfind('<li class="campaign-card"', 0, start):page.index('</li>', start)]


def test_campaign_cards_open_to_read_and_offer_edit(setup):
    app, client = setup
    build(app, client)
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'class="campaign-gallery"' in page and '<details class="campaign-tree-root' not in page
    first = card(page)
    assert 'class="campaign-card-title" href="/campaigns/1/"' in first  # The card opens the lobby.
    assert '>Edit' not in first.replace('</i> ', '>')  # No Edit view.
    assert '4 articles' in first and 'Party: <a href="/users/user1/parties/party1/">Party 1</a>' in first
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
    assert '<div class="wiki-cover"><img src="/campaigns/1/cover"' in home


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

def test_new_module_dialog_offers_random_generation_with_defaults(setup):
    app, client = setup
    assert 'Generate it randomly' not in client.get('/campaigns/').get_data(as_text=True)  # Campaigns only have a name.
    page = client.get('/campaigns/1/').get_data(as_text=True)
    start = page.index('id="new-module-dialog"')
    dialog = page[start:page.index('</dialog>', start)]
    assert 'x-data="newCampaign"' in dialog and 'Generate it randomly' in dialog and 'action="/campaigns/1/modules"' in dialog
    assert '<select name="kind" x-model="kind">' in dialog
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
    assert response.location.endswith(f'/campaigns/{campaign.id}/')  # Its lobby.


def test_dialog_saves_a_generated_dungeon_as_a_module(setup):
    app, client = setup
    draft = {'nodes': [{'id': 'new-1', 'title': 'Gate', 'category': 'room', 'number': 1, 'x': 0, 'y': 0}], 'edges': []}
    response = client.post('/campaigns/1/modules', data={'name': 'Deep vault', 'start': 'random',
        'kind': 'dungeon', 'title': 'The Sunken Vault', 'body': 'Damp stone.', 'draft': json.dumps(draft)})
    from app.models import Module
    with app.app_context():
        module = Module.query.filter_by(title='Deep vault').one()
        dungeon = ContentEntry.query.filter_by(campaign_id=1, title='The Sunken Vault').one()
        assert dungeon.pointcrawl.kind == 'dungeon' and dungeon.module_id == module.id
        assert all(node.entry.module_id == module.id for node in dungeon.pointcrawl.nodes)
    assert response.location.endswith(f'/campaigns/1/modules/{module.id}/')


def test_dialog_falls_back_to_the_generator_with_its_options(setup):
    app, client = setup
    response = client.post('/campaigns/1/modules', data={'name': 'Wild lands', 'start': 'random',
        'kind': 'forest', 'poi_count': '8', 'generate_children': '1', 'dungeon_chance': '40'})
    location = response.location
    from app.models import Module
    with app.app_context():
        module = Module.query.filter_by(title='Wild lands').one()
    assert '/materials/generate?' in location and 'kind=forest' in location and f'module_id={module.id}' in location
    assert 'children=1' in location and 'forest_pois=40' in location and 'pois=8' in location
    page = client.get(location).get_data(as_text=True)
    assert f'<input type="hidden" name="module_id" value="{module.id}">' in page and 'data-kind="forest"' in page


def test_wiki_undoes_global_aside_and_article_styles():
    css = (ROOT / 'app/static/src/css/campaigns.css').read_text(encoding='utf-8')
    rule = css[css.index('aside:where(.campaign-wiki *)'):]
    rule = rule[:rule.index('}')]
    for declaration in ('float:none', 'width:auto', 'max-width:none', 'margin:0', 'border-left:0'):
        assert declaration in rule


# ----- Unfiled articles read the same way -----

def unfiled(client, **values):
    result = client.post('/materials/new', data={'category': 'note', 'title': 'Loose', 'body': 'x', **values})
    assert result.status_code == 302
    return int(re.search(r'/materials/(\d+)/edit', result.location).group(1))


def wiki_card(page, title):
    """The article card whose title is this text."""
    for match in re.finditer(r'<li class="wiki-card">(.*?)</li>', page, re.S):
        if f'>{title}</a>' in match.group(1):
            return match.group(1)
    raise AssertionError(f'No card for {title}')


def test_article_cards_show_a_picture_or_a_placeholder(setup):
    app, client = setup
    pictured = create_entry(client, category='npc', title='Portrait', body='![face](https://example.org/face.png)')
    create_entry(client, category='note', title='Plain', body='No picture.')
    page = wiki(client).get_data(as_text=True)
    assert f'<img src="/materials/{pictured}/image"' in wiki_card(page, 'Portrait')
    plain = wiki_card(page, 'Plain')
    assert '<img' not in plain and '<span class="wiki-card-placeholder">P</span>' in plain


def test_owner_article_cards_offer_edit_but_not_delete(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    card_html = wiki_card(wiki(client).get_data(as_text=True), 'Bell of Ash')
    assert f'href="/materials/{relic}/edit"' in card_html
    assert 'Delete' not in card_html and '<form' not in card_html  # Delete is at the bottom of the editor.


def test_old_unfiled_links_open_campaigns(setup):
    app, client = setup
    entry = create_entry(client, title='Filed')
    assert client.get('/materials/wiki/').location.endswith('/campaigns/')
    assert client.get(f'/materials/wiki/{entry}/').location.endswith(f'/campaigns/1/wiki/{entry}/')
    assert 'Unfiled' not in client.get('/campaigns/').get_data(as_text=True)


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

def test_players_read_only_revealed_articles(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    assert reveal(client, guild).status_code == 302
    assert reveal(client, relic).status_code == 302
    login(client, 2)
    page = client.get(f'/party/1/materials/{guild}').get_data(as_text=True)
    assert 'class="wiki-layout"' in page and 'id="party-content-results"' in page
    assert '<h1>Ash Guild<' in page and 'Bellmakers.' in page and 'On this page' in page
    # Never unrevealed articles: Mira is named in the text, but not linked; Thornwick is not there at all.
    assert f'/party/1/materials/{mira}' not in page and f'/party/1/materials/{town}' not in page and 'Thornwick' not in page
    # The bell's related link points here.
    assert 'Linked from' in page and f'href="/party/1/materials/{relic}"' in page
    assert f'/materials/{guild}/edit' not in page and '/reveal' not in page  # No Warden tools for players.
    assert '← Back to party' in page and 'href="/users/user1/parties/party1/"' in page


def test_party_wiki_home_groups_only_revealed_articles(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    empty = client.get('/party/1/wiki/').get_data(as_text=True)
    assert 'Nothing has been revealed yet.' in empty and '0 articles' in empty
    assert reveal(client, guild).status_code == 302
    assert reveal(client, relic).status_code == 302
    login(client, 2)
    page = client.get('/party/1/wiki/').get_data(as_text=True)
    assert 'class="wiki-layout"' in page and 'id="party-content-results"' in page  # Refreshes live like article pages.
    assert '2 articles' in page
    for group in ('Factions', 'Dungeon'):
        assert f'<h2>{group} <small>1</small></h2>' in page
    assert f'href="/party/1/materials/{guild}"' in page and 'Bellmakers.' in page
    # No unrevealed articles, campaign cover or Warden tools.
    for secret in ('Thornwick', f'/party/1/materials/{mira}', 'Secret campaign', 'wiki-cover', '/edit', 'New article'):
        assert secret not in page
    assert 'aria-current="page"' in page  # The sidebar's home link is this page.
    assert 'href="/users/user1/parties/party1/"' in page  # Back to party.


def test_party_wiki_gives_the_warden_hide_and_note_edit_and_delete(setup):
    """Party wiki, Warden: Hide on revealed articles, Edit and Delete on party notes; back to the wiki."""
    app, client = setup
    shown = create_entry(client, title='Plain', body='As written')
    assert reveal(client, shown).status_code == 302
    assert client.post('/party/1/notes', data={'title': 'Table note', 'body': 'Said aloud'}).status_code == 302
    home = client.get('/party/1/wiki/').text
    # Cards: Hide on the article; a note's Delete is at the bottom of its editor.
    assert home.count('name="return_to" value="wiki"') == 1
    assert '/version' not in home and 'Party version' not in home
    assert 'data-confirm="Hide this article from the party?' in home
    with app.app_context():
        note_id = ContentEntry.query.filter_by(category='party_note').one().id
    editor = client.get(f'/party/1/notes/{note_id}/edit').text
    footer = editor[editor.index('campaign-footer-actions'):]
    assert f'action="/party/1/notes/{note_id}/delete"' in footer and 'data-confirm="Delete this party note?' in footer
    plain = client.get(f'/party/1/materials/{shown}').text
    assert ' Hide</button>' in plain and '/version' not in plain and 'Edit party version' not in plain
    gone = client.post(f'/materials/{shown}/revoke/1', data={'version': 1, 'return_to': 'wiki'})
    assert gone.location == '/party/1/wiki/'
    assert client.post(f'/party/1/notes/{note_id}/delete', data={'return_to': 'wiki'}).location == '/party/1/wiki/'
    login(client, 2)  # Players get no buttons.
    assert 'name="return_to" value="wiki"' not in client.get('/party/1/wiki/').text


def test_party_wiki_home_links_and_access(setup):
    app, client = setup
    entry = create_entry(client)
    assert reveal(client, entry).status_code == 302
    page = client.get(f'/party/1/materials/{entry}').get_data(as_text=True)
    assert 'class="wiki-campaign-name" href="/party/1/wiki/"' in page  # Sidebar home is the party wiki.
    assert '← Back to party' in page and 'href="/users/user1/parties/party1/"' in page
    login(client, 3)
    assert client.get('/party/1/wiki/').status_code == 403


def test_party_article_page_has_no_party_version_editing(setup):
    app, client = setup
    entry = create_entry(client)
    assert reveal(client, entry).status_code == 302
    page = client.get(f'/party/1/materials/{entry}').get_data(as_text=True)
    assert f'/party/1/materials/{entry}/version' not in page and 'Edit party version' not in page
    assert f'/materials/{entry}/edit' not in page and 'Private original' not in page
    assert f'/materials/{entry}/reveal' not in page


def test_party_opens_maps_on_the_party_map_page(setup):
    """A party never reads a map as a wiki article: the wiki lists it under Maps and opens the party map page."""
    app, client = setup
    map_id, _graph = create_map(client)
    entry = map_entry_id(app, map_id)
    assert reveal(client, entry).status_code == 302
    login(client, 2)
    assert client.get(f'/party/1/materials/{entry}').location == f'/party/1/map/{map_id}/'
    home = client.get('/party/1/wiki/').get_data(as_text=True)
    sidebar = home[home.index('id="wiki-sidebar"'):home.index('</aside>')]
    assert f'href="/party/1/map/{map_id}/"' in sidebar[:sidebar.index('class="wiki-articles-title"')]
    assert f'href="/party/1/map/{map_id}/"' in home[home.index('id="wiki-home-maps"'):]


def test_party_wiki_home_has_a_cover_from_what_the_party_was_shown(setup):
    app, client = setup
    plain = create_entry(client, title='Plain', body='No picture here.')
    pictured = create_entry(client, title='Portrait', body='![face](https://example.org/face.png)')
    create_entry(client, title='Hidden', body='![map](https://example.org/secret.png)')
    assert client.get('/party/1/wiki/').text.count('class="wiki-cover"') == 0  # Nothing shown yet.
    assert reveal(client, plain).status_code == 302
    assert 'class="wiki-cover"' not in client.get('/party/1/wiki/').text  # No picture in what they read.
    assert reveal(client, pictured).status_code == 302
    home = client.get('/party/1/wiki/').text
    assert f'<div class="wiki-cover"><img src="/party/1/materials/{pictured}/image"' in home
    login(client, 2)  # Members see it too.
    assert f'/party/1/materials/{pictured}/image" alt="" data-cover' in client.get('/party/1/wiki/').text

# ----- Campaign lobby and module wiki -----

def test_campaign_opens_on_its_lobby_without_wiki_parts(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    assert 'href="/campaigns/1/"' in client.get('/campaigns/').get_data(as_text=True)  # Cards open the lobby.
    lobby = client.get('/campaigns/1/').get_data(as_text=True)
    for part in ('campaign-parties', 'campaign-modules', 'id="campaign-settings-dialog"', 'id="marketplace-dialog"'):
        assert part in lobby
    assert 'Read everything as wiki' not in lobby  # Modules are read one at a time, from their cards.
    assert 'id="backgrounds-dialog"' not in lobby  # Backgrounds are set per party, on the party page.
    # No wiki: no article tree, groups or front page text.
    for part in ('wiki-sidebar', 'wiki-tree', '<h2>Factions', 'Bellmakers'):
        assert part not in lobby
    wiki_home = client.get('/campaigns/1/wiki/').get_data(as_text=True)
    assert 'wiki-sidebar' in wiki_home and 'campaign-parties' not in wiki_home and 'campaign-settings-dialog' not in wiki_home
    assert '← Secret campaign' in wiki_home and 'href="/campaigns/1/"' in wiki_home  # Back to the lobby.
    login(client, 2)
    assert client.get('/campaigns/1/').status_code == 403


def test_module_cards_open_the_module_as_a_wiki(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    from app.models import Module
    with app.app_context():
        db.session.add(Module(id=5, campaign_id=1, title='Second module'))
        db.session.add(ContentEntry(owner_id=1, campaign_id=1, module_id=5, category='lore', title='Other lore', body='Elsewhere.'))
        db.session.commit()
        first = db.session.get(ContentEntry, guild).module_id
    lobby = client.get('/campaigns/1/').get_data(as_text=True)
    assert f'href="/campaigns/1/modules/{first}/wiki/"' in lobby and f'href="/campaigns/1/modules/{first}/"' in lobby
    page = client.get(f'/campaigns/1/modules/{first}/wiki/').get_data(as_text=True)
    assert 'Ash Guild' in page and 'Other lore' not in page and 'Edit module' in page  # Only this module.
    assert f'href="/campaigns/1/modules/{first}/"' in page and '← Secret campaign' in page
    article = client.get(f'/campaigns/1/modules/{first}/wiki/{guild}/').get_data(as_text=True)
    assert '<h1>Ash Guild<' in article and f'href="/campaigns/1/modules/{first}/wiki/{mira}/"' in article
    assert client.get(f'/campaigns/1/modules/5/wiki/{guild}/').status_code == 404  # Not in that module.
    everything = client.get('/campaigns/1/wiki/').get_data(as_text=True)
    assert 'Ash Guild' in everything and 'Other lore' in everything  # The campaign's wiki, by its address.


def test_reveal_module_reveals_all_its_articles_to_one_party(setup):
    app, client = setup
    guild, mira, town, relic = build(app, client)
    from app.models import Module, PartyPresentation, Party
    with app.app_context():
        module_id = db.session.get(ContentEntry, guild).module_id
        db.session.add(Module(id=5, campaign_id=1, title='Other module'))
        db.session.add(ContentEntry(owner_id=1, campaign_id=1, module_id=5, category='lore', title='Elsewhere', body='x'))
        db.session.commit()
    home = client.get(f'/campaigns/1/modules/{module_id}/wiki/').get_data(as_text=True)
    assert 'id="reveal-module-dialog"' in home and f'action="/campaigns/1/modules/{module_id}/reveal"' in home
    assert '<option value="1">Party 1</option>' in home and 'value="2"' not in home.split('reveal-module-dialog')[1].split('</dialog>')[0]
    assert reveal(client, relic).status_code == 302  # Already revealed: stays revealed.
    response = client.post(f'/campaigns/1/modules/{module_id}/reveal', data={'party_id': 1})
    assert response.location.endswith(f'/campaigns/1/modules/{module_id}/wiki/')
    with app.app_context():
        shown = {row.entry.title for row in PartyPresentation.query.filter_by(party_id=1)}
        assert shown == {'Ash Guild', 'Mira', 'Thornwick', 'Bell of Ash'}  # Not the other module's article.
    assert client.post(f'/campaigns/1/modules/{module_id}/reveal', data={'party_id': 2}).status_code == 403  # Not this campaign's.
    assert client.post(f'/campaigns/1/modules/{module_id}/reveal', data={'party_id': 3}).status_code == 403  # Not my party.
    login(client, 2)
    assert client.post(f'/campaigns/1/modules/{module_id}/reveal', data={'party_id': 1}).status_code == 403

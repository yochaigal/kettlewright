"""The party map is part of the party wiki (#476): its sidebar beside a big map, with Full screen."""
import re

from tests.helpers import login
from tests.unit.test_campaigns import setup, create_map, create_entry, reveal, map_entry_id  # noqa: F401 (fixture)


def test_map_page_has_the_wiki_sidebar(setup):
    app, client = setup
    map_id, _ = create_map(client, title='Coast map')
    second_id, _ = create_map(client, title='Cave map')
    article = create_entry(client, title='Lighthouse')
    for entry_id in (map_entry_id(app, map_id), map_entry_id(app, second_id), article):
        reveal(client, entry_id)
    login(client, 2)  # A member.
    page = client.get(f'/party/1/map/{map_id}/').text
    assert 'id="wiki-sidebar"' in page and 'x-data="partyMap"' in page
    # Both maps are listed, this one marked; the revealed article is listed too.
    current = re.search(r'<a [^>]*aria-current="page"[^>]*>([^<]*)', page)
    assert current and 'Coast map' in current.group(1)
    assert f'/party/1/map/{second_id}/' in page and f'/party/1/materials/{article}' in page
    assert 'Full screen' in page and 'allowfullscreen' in page
    # The wiki home keeps its own mark.
    home = client.get('/party/1/wiki/').text
    assert re.search(r'aria-current="page"[^>]*>[^<]*Party 1', home) or 'aria-current="page"' in home


def test_map_editor_has_full_screen(setup):
    app, client = setup
    map_id, _ = create_map(client)
    page = client.get(f'/maps/{map_id}/edit').text
    assert 'fullscreen()' in page and 'allowfullscreen' in page

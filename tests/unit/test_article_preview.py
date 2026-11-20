from tests.unit.test_campaigns import setup, create_entry, create_map, map_entry_id, login, reveal, drawing
from app.models import db, PointcrawlMap
from html import unescape
import json
import re


def preview_graph(response):
    return json.loads(unescape(re.search(r'data-graph="([^"]+)"', response.get_data(as_text=True))[1]))


def test_preview_uses_the_original_for_owner_and_party(setup):
    app, client = setup
    entry_id = create_entry(client, title='Private title', body='Private body')
    private = client.get(f'/materials/{entry_id}/preview')
    assert private.status_code == 200
    assert 'Private body' in private.get_data(as_text=True)
    assert private.headers['Cache-Control'] == 'private, no-store'
    login(client, 2)
    assert client.get(f'/party/1/materials/{entry_id}/preview').status_code == 404  # Not revealed yet.
    login(client, 1)
    assert reveal(client, entry_id).status_code == 302
    login(client, 2)
    published = client.get(f'/party/1/materials/{entry_id}/preview')
    assert published.status_code == 200
    assert 'Private body' in published.get_data(as_text=True)  # Revealed: the party reads the article.
    assert client.get(f'/materials/{entry_id}/preview').status_code in (403, 404)
    assert client.get(f'/party/1/materials/{entry_id + 1000}/preview').status_code == 404
    login(client, 4)
    assert client.get(f'/party/1/materials/{entry_id}/preview').status_code in (403, 404)


def test_preview_map_projects_current_drawing_and_only_revealed_markers(setup):
    app, client = setup
    map_id, graph = create_map(client)
    entry_id = map_entry_id(app, map_id)
    with app.app_context():
        pointcrawl = db.session.get(PointcrawlMap, map_id)
        pointcrawl.drawing = drawing('First drawing')
        db.session.commit()
    private = preview_graph(client.get(f'/materials/{entry_id}/preview'))
    assert len(private['nodes']) == 2
    assert private['edges']
    assert reveal(client, entry_id).status_code == 302
    assert reveal(client, graph['nodes'][0]['entry_id']).status_code == 302
    with app.app_context():
        db.session.get(PointcrawlMap, map_id).drawing = drawing('Redrawn')
        db.session.commit()
    login(client, 2)
    response = client.get(f'/party/1/materials/{entry_id}/preview')
    public = preview_graph(response)
    assert len(public['nodes']) == 1
    assert public['nodes'][0]['title'] == 'SECRET ROOM 0'  # The revealed point, as it is.
    assert public['edges'] == []
    assert public['drawing']['elements'][0]['text'] == 'Redrawn'  # The map's current drawing.
    text = response.get_data(as_text=True)
    assert 'First drawing' not in text
    assert 'SECRET ROOM 1' not in text and 'SECRET TRAP 1' not in text  # The point that was not revealed.

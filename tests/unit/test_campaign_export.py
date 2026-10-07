import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from app.lib.campaign_import import preview_archive, import_preview
from app.models import db, Campaign, ContentEntry, ContentLink, PointcrawlMap
from test_campaigns import setup, login, create_entry, create_map, drawing
from test_campaign_import import upload, archive, md


def test_export_roundtrip_duplicate_titles_and_private_scope(setup):
    app, client = setup
    root = create_entry(client, title='Same: "title"', category='note')
    child = create_entry(client, title='Same: "title"', category='settlement')
    with app.app_context():
        db.session.get(ContentEntry, child).parent_id = root
        db.session.get(ContentEntry, child).is_heart = True
        db.session.get(ContentEntry, child).path_type = 'hidden'
        db.session.add(ContentEntry(owner_id=1, title='UNFILED SECRET', category='note', body='outside'))
        db.session.add(Campaign(id=2, owner_id=1, name='OTHER CAMPAIGN SECRET'))
        db.session.add(ContentEntry(owner_id=1, campaign_id=2, title='OTHER SECRET', category='note', body='outside'))
        db.session.commit()
    response = client.get('/campaigns/1/export')
    assert response.status_code == 200
    assert response.mimetype == 'application/zip'
    assert 'attachment' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'private, no-store'
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        contents = '\n'.join(exported.read(name).decode() for name in exported.namelist())
        assert 'OTHER SECRET' not in contents and 'UNFILED SECRET' not in contents
        assert 'party_id' not in contents and 'owner_id' not in contents
    preview = preview_archive(response.data)
    assert preview['errors'] == []
    response = upload(client, response.data)
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', response.get_data(as_text=True)).group(1)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 302
    with app.app_context():
        imported = Campaign.query.filter(Campaign.id.notin_([1, 2])).one()
        assert imported.name == 'Secret campaign'
        assert imported.parties == []
        assert len(imported.entries) == 2
        parent = next(entry for entry in imported.entries if entry.parent_id is None)
        child = next(entry for entry in imported.entries if entry.parent_id is not None)
        assert parent.title == child.title == 'Same: "title"'
        assert child.parent_id == parent.id and child.is_heart and child.path_type == 'hidden'
        assert parent.body == child.body == 'SECRET BODY'
        assert all(not entry.presentations for entry in imported.entries)
    assert 'Export campaign' in client.get('/campaigns/1/').get_data(as_text=True)
    login(client, 2)
    assert client.get('/campaigns/1/export').status_code == 403
    login(client, 1)
    app.config['FEATURE_TEST_USER_IDS'] = set()
    assert client.get('/campaigns/1/export').status_code == 404


def test_export_map_sidecar_roundtrip(setup):
    app, client = setup
    map_id, graph = create_map(client, nodes=2)
    graph['drawing'] = drawing()
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    with app.app_context():
        pointcrawl = db.session.get(PointcrawlMap, map_id)
        db.session.add(ContentLink(source_id=pointcrawl.nodes[0].entry_id,
                                   target_id=pointcrawl.nodes[1].entry_id))
        pointcrawl.entry.body = '![Image](https://example.com/world.webp)'
        db.session.commit()
    response = client.get('/campaigns/1/export')
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        manifest = json.loads(exported.read('manifest.json'))
        assert manifest['format'] == 'kettlewright-campaign' and manifest['version'] == 1
        assert len(manifest['links']) == 1
        assert 'assets' not in manifest
        assert not any(name.startswith('assets/') for name in exported.namelist())
        sidecar = json.loads(exported.read(manifest['maps'][0]))
        assert sidecar['drawing']['elements'][0]['text'] == 'SECRET DRAWING'
        assert len(sidecar['nodes']) == 2 and len(sidecar['edges']) == len(graph['edges'])
        assert {node['id'] for node in sidecar['nodes']} >= {
            edge['source'] for edge in sidecar['edges']}
        assert any(f'id: {sidecar["article_id"]}\n' in exported.read(filename).decode()
                   for filename in manifest['articles'])
    preview = preview_archive(response.data)
    assert preview['errors'] == []
    with app.app_context():
        original = db.session.get(PointcrawlMap, map_id)
        expected_nodes = sorted((n.number, n.x, n.y, n.entry.title) for n in original.nodes)
        expected_edges = len(original.edges)
        import_preview(preview, 2)
        db.session.commit()
        imported = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == 2).one()
        assert imported.drawing == original.drawing
        assert sorted((n.number, n.x, n.y, n.entry.title) for n in imported.nodes) == expected_nodes
        assert len(imported.edges) == expected_edges
        assert imported.entry.body == '![Image](https://example.com/world.webp)'
        assert ContentLink.query.join(ContentEntry, ContentEntry.id == ContentLink.source_id).filter(ContentEntry.owner_id == 2).count() == 1


@pytest.mark.parametrize('header, message', [
    ('id: duplicate\n', 'duplicate id'),
    ('parent_id: missing\n', 'parent_id'),
    ('id: self\nparent_id: self\n', 'cycle'),
    ('heart: yes\n', 'heart must'),
    ('path_type: nope\n', 'path_type'),
])
def test_portable_metadata_validation(header, message):
    files = {'a.md': md('A').replace('layout: default\n', 'layout: default\n' + header)}
    if message == 'duplicate id':
        files['b.md'] = files['a.md']
    assert any(message in error for error in preview_archive(archive(files))['errors'])


def test_example_archive_is_importable(setup):
    app, _ = setup
    example = Path(__file__).resolve().parents[2] / 'docs/examples/campaign'
    files = {str(path.relative_to(example)): path.read_text() for path in example.rglob('*') if path.is_file()}
    preview = preview_archive(archive(files))
    assert preview['errors'] == []
    assert len(preview['rows']) == 6
    assert next(row for row in preview['rows'] if row['title'] == 'Alderbridge')['is_heart']
    assert 'maps/article-0001.json' not in preview['ignored']
    with app.app_context():
        assert import_preview(preview, 1) == (1, 5)
        db.session.commit()
        imported = Campaign.query.filter(Campaign.id != 1).one()
        assert len(imported.entries) == 6  # Campaign description becomes an Overview.
        npc = next(entry for entry in imported.entries if entry.category == 'npc')
        assert npc.parent.title == 'Alderbridge'
        realm = next(entry for entry in imported.entries if entry.category == 'realm')
        assert len(realm.pointcrawl.nodes) == 2 and len(realm.pointcrawl.edges) == 1
        dungeon = next(entry for entry in imported.entries if entry.category == 'dungeon')
        assert next(node for node in realm.pointcrawl.nodes if node.entry_id == dungeon.id).nested_map_id == dungeon.pointcrawl.id


def test_empty_campaign_export(setup):
    app, client = setup
    response = client.get('/campaigns/1/export')
    preview = preview_archive(response.data)
    assert preview['errors'] == [] and len(preview['rows']) == 1
    with app.app_context():
        assert import_preview(preview, 1) == (1, 0)

import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from app.lib.campaign_import import preview_archive, import_preview
from app.models import db, Campaign, ContentEntry, ContentLink, PointcrawlMap
from test_campaigns import setup, login, create_entry, create_map, drawing, module_url
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
    export_url = module_url(app, 1, 'export')  # Modules are exported, one by one.
    response = client.get(export_url)
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
    # An exported campaign imports again as a module of another campaign.
    assert client.post('/materials/import-archive', data={'preview_id': token, 'target_campaign': 2}).status_code == 302
    with app.app_context():
        from app.models import Module
        imported = Module.query.filter_by(campaign_id=2).one()
        assert imported.title == 'Secret campaign' and Campaign.query.count() == 2
        assert len(imported.entries) == 2
        parent = next(entry for entry in imported.entries if entry.parent_id is None)
        child = next(entry for entry in imported.entries if entry.parent_id is not None)
        assert parent.title == child.title == 'Same: "title"'
        assert child.parent_id == parent.id and child.is_heart and child.path_type == 'hidden'
        assert parent.body == child.body == 'SECRET BODY'
        assert all(not entry.presentations for entry in imported.entries)
    assert f'href="{export_url}"' in client.get('/campaigns/1/').get_data(as_text=True)  # On its module card, in the lobby.
    assert '/export' not in client.get('/campaigns/').get_data(as_text=True)
    login(client, 2)
    assert client.get(export_url).status_code == 403
    login(client, 1)
    app.config['FEATURE_TEST_USER_IDS'] = set()
    assert client.get(export_url).status_code == 200


def test_export_is_markdown_with_one_folder_per_part_and_roundtrips(setup):
    """Format 2: module.md, maps/*.md, articles/*.md, backgrounds/*.md. No JSON, no manifest."""
    app, client = setup
    map_id, graph = create_map(client, nodes=2)
    graph['drawing'] = drawing()
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    with app.app_context():
        pointcrawl = db.session.get(PointcrawlMap, map_id)
        db.session.add(ContentLink(source_id=pointcrawl.nodes[0].entry_id,
                                   target_id=pointcrawl.nodes[1].entry_id))
        db.session.commit()
    response = client.get(module_url(app, 1, 'export'))
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        names = exported.namelist()
        assert all(name.endswith('.md') for name in names) and 'manifest.json' not in names
        assert {name.split('/')[0] for name in names} == {'module.md', 'maps', 'articles'}
        module = exported.read('module.md').decode()
        assert 'type: Module' in module and 'format: kettlewright-module' in module and 'version: 2' in module
        map_file = exported.read('maps/secret-map.md').decode()
        assert 'type: Map' in map_file and 'map_type: dungeon' in map_file and '```kettlewright-map' in map_file
        sidecar = json.loads(map_file.split('```kettlewright-map\n')[1].split('\n```')[0])
        assert sidecar['drawing']['elements'][0]['text'] == 'SECRET DRAWING'
        assert len(sidecar['nodes']) == 2 and len(sidecar['edges']) == len(graph['edges'])
        rooms = [exported.read(name).decode() for name in names if name.startswith('articles/') and 'SECRET ROOM' in exported.read(name).decode()]
        assert len(rooms) == 2 and sum('links:' in room for room in rooms) == 1  # The link travels in front matter.
    preview = preview_archive(response.data)
    assert preview['errors'] == []
    with app.app_context():
        original = db.session.get(PointcrawlMap, map_id)
        expected_nodes = sorted((n.number, n.x, n.y, n.entry.title) for n in original.nodes)
        expected_edges = len(original.edges)
        import_preview(preview, 2)
        db.session.commit()
        imported = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == 2).one()
        assert imported.drawing == original.drawing and imported.kind == 'dungeon'
        assert imported.entry.title == 'SECRET MAP' and imported.entry.body == ''
        assert sorted((n.number, n.x, n.y, n.entry.title) for n in imported.nodes) == expected_nodes
        assert len(imported.edges) == expected_edges
        assert ContentLink.query.join(ContentEntry, ContentEntry.id == ContentLink.source_id).filter(ContentEntry.owner_id == 2).count() == 1


def test_an_article_with_its_own_map_exports_both_and_reattaches(setup):
    from test_campaigns import nested_draft
    app, client = setup
    map_id, graph = create_map(client)
    graph['nodes'][0]['nested_draft'] = nested_draft()
    saved = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).json
    nested_id = saved['nodes'][0]['nested_map_id']
    response = client.get(module_url(app, 1, 'export'))
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        maps = [exported.read(name).decode() for name in exported.namelist() if name.startswith('maps/')]
        assert len(maps) == 2 and sum('\narticle: article-' in text for text in maps) == 1
    preview = preview_archive(response.data)
    assert preview['errors'] == []
    with app.app_context():
        import_preview(preview, 2)
        db.session.commit()
        maps = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == 2).all()
        entrance = next(m for m in maps if m.entry.body)  # The dungeon point: an article with text and a map.
        region = next(m for m in maps if m is not entrance)
        assert entrance.kind == db.session.get(PointcrawlMap, nested_id).kind and len(entrance.nodes) == 2
        assert next(n for n in region.nodes if n.entry_id == entrance.entry_id).nested_map_id == entrance.id


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


def test_example_module_is_importable(setup):
    """The example module (the import page's download): format 2, every part, ids tying them together."""
    app, _ = setup
    example = Path(__file__).resolve().parents[2] / 'app/static/examples/module'
    files = {str(path.relative_to(example)): path.read_text() for path in example.rglob('*') if path.is_file()}
    preview = preview_archive(archive(files))
    assert preview['errors'] == [] and preview['warnings'] == []
    assert sorted(row['title'] for row in preview['rows']) == [
        'Alderbridge', 'Mara the Ferryman', 'The Ashen Marches', 'The Ashen Marches', 'The Old Pilgrim Road', 'The Sunken Abbey']
    assert list(preview['backgrounds']) == ['Tidewatcher']
    assert list(preview['items']) == ['The Stolen Bell', "Pilgrim's Token"]
    with app.app_context():
        import_preview(preview, 1)
        db.session.commit()
        from app.models import Module
        module = Module.query.filter_by(title='The Ashen Marches').one()
        entries = {entry.title: entry for entry in module.entries}
        realm = next(entry for entry in module.entries if entry.pointcrawl and entry.category == 'realm')
        abbey = entries['The Sunken Abbey']
        assert realm.body == '' and abbey.category == 'dungeon' and abbey.pointcrawl.kind == 'dungeon'
        assert len(realm.pointcrawl.nodes) == 2 and len(realm.pointcrawl.edges) == 1
        assert next(n for n in realm.pointcrawl.nodes if n.entry_id == abbey.id).nested_map_id == abbey.pointcrawl.id
        assert entries['Alderbridge'].is_heart and entries['Mara the Ferryman'].parent.title == 'Alderbridge'
        assert entries['The Old Pilgrim Road'].path_type == 'conditional'
        assert [link.target_id for link in abbey.links] == [entries['Mara the Ferryman'].id]
        assert list(module.backgrounds) == ['Tidewatcher']
        assert module.items['The Stolen Bell']['tags'] == ['bulky', 'charges']


def test_empty_module_export(setup):
    app, client = setup
    from app.models import Module
    with app.app_context():
        db.session.add(Module(id=9, campaign_id=1, title='Empty'))
        db.session.commit()
    response = client.get('/campaigns/1/modules/9/export')
    preview = preview_archive(response.data)
    assert preview['errors'] == [] and len(preview['rows']) == 1
    with app.app_context():
        assert import_preview(preview, 1) == (1, 0)


def test_an_image_map_exports_with_its_picture_and_imports_as_an_image_map(setup):
    from test_campaigns import create_image_map
    app, client = setup
    map_id, _ = create_image_map(client)
    response = client.get(module_url(app, 1, 'export'))
    with zipfile.ZipFile(io.BytesIO(response.data)) as exported:
        map_file = exported.read('maps/coast-of-vald.md').decode()
        assert 'map_type: image' in map_file and 'data:image/webp;base64,' in map_file  # The picture travels in the map.
    preview = preview_archive(response.data)
    assert preview['errors'] == []
    with app.app_context():
        original = db.session.get(PointcrawlMap, map_id)
        import_preview(preview, 2)
        db.session.commit()
        imported = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == 2).one()
        assert imported.kind == 'image' and imported.entry.category == 'topography'
        assert imported.drawing == original.drawing

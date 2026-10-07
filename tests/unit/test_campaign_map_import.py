import base64
from copy import deepcopy
import io
import json
import re

from PIL import Image
import pytest

from app.lib.campaign_import import preview_archive, import_preview, ImportError, MAX_MAP_FILE
from app.models import db, Campaign, CampaignImport, ContentEntry, PointcrawlMap, ContentLink
from test_campaigns import setup, login, drawing
from test_campaign_import import archive, md, upload


def bundle():
    article = md('World', 'Realm', 'Campaign').replace('layout: default\n',
        'layout: default\nid: world\nmap: maps/world.json\n')
    room = md('Village', 'Settlement', 'World').replace('layout: default\n', 'layout: default\nid: village\n')
    path = md('Road', 'Path', 'World').replace('layout: default\n', 'layout: default\nid: road\n')
    graph = {'article_id': 'world', 'kind': 'realm', 'drawing': drawing(),
        'nodes': [{'id': 'one', 'article_id': 'village', 'number': 1, 'x': 10, 'y': 20}], 'edges': []}
    return {'campaign.md': md('Campaign', 'Campaign'), 'world.md': article,
        'village.md': room, 'road.md': path, 'maps/world.json': json.dumps(graph)}


def test_excalidraw_scene_preview_confirmation_and_images(setup):
    app, client = setup
    files = bundle()
    files['world.md'] = files['world.md'].replace('maps/world.json', 'maps/world.excalidraw')
    del files['maps/world.json']
    png = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(png, format='PNG')
    scene = drawing('Hand-drawn world')
    scene['elements'][0].update(link='obsidian://open?vault=test', customData={'secret': 'vault'})
    scene['elements'].append({'id': 'picture', 'type': 'image', 'x': 1, 'y': 2,
        'width': 20, 'height': 20, 'fileId': 'picture'})
    scene['files']['picture'] = {'mimeType': 'image/png',
        'dataURL': 'data:image/png;base64,' + base64.b64encode(png.getvalue()).decode()}
    scene.update(type='excalidraw', version=2, appState={'viewBackgroundColor': '#123456'})
    files['maps/world.excalidraw'] = json.dumps(scene)
    # Common ZIP tools add a containing folder. References remain relative to
    # the bundle root, not to the article's own directory.
    files = {'vault-export/' + name: text for name, text in files.items()}
    response = upload(client, archive(files))
    html = response.get_data(as_text=True)
    assert response.status_code == 200 and 'drawing elements' in html
    assert 'do not automatically become article points' in html
    with app.app_context():
        assert PointcrawlMap.query.count() == 0
        assert Campaign.query.count() == 1
    token = re.search(r'name="preview_id" value="([a-f0-9]+)"', html).group(1)
    login(client, 2)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 404
    login(client, 1)
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 302
    with app.app_context():
        pointcrawl = PointcrawlMap.query.one()
        assert pointcrawl.kind == 'realm' and pointcrawl.nodes == [] and pointcrawl.edges == []
        assert len(pointcrawl.drawing['elements']) == 2
        assert 'customData' not in pointcrawl.drawing['elements'][0]
        assert pointcrawl.drawing['elements'][0]['link'] is None
        assert pointcrawl.drawing['files']['picture']['dataURL'].startswith('data:image/png;base64,')
        assert pointcrawl.entry.presentations == []
        map_id, entry_id = pointcrawl.id, pointcrawl.entry_id
    assert client.get(f'/materials/{entry_id}/edit').status_code == 200
    saved = client.get(f'/maps/{map_id}/data')
    assert saved.status_code == 200 and len(saved.json['drawing']['elements']) == 2
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(saved.json)}).status_code == 200
    assert client.get('/party/1/materials/data').json == {'entries': []}
    assert client.post('/materials/import-archive', data={'preview_id': token}).status_code == 409


@pytest.mark.parametrize('case, expected', [
    ('missing', 'Missing map file'), ('kind', 'map kind'), ('invalid_json', 'invalid JSON'),
    ('nan', 'invalid JSON'), ('bad_drawing', 'Unsupported drawing element'),
    ('unknown_article', 'Unknown article ID'), ('duplicate_point', 'unique nonempty'),
    ('duplicate_number', 'positive unique'), ('duplicate_article', 'unique point article'),
    ('coordinate', 'coordinate'), ('bad_geometry', 'geography shape'),
    ('bad_edge', 'distinct points'), ('self_nested', 'another imported map'),
    ('cross_campaign', 'same campaign'), ('unsafe', 'Unsafe map reference'),
    ('obsidian_md', 'export Obsidian'), ('wrong_article_type', 'does not support a map'),
    ('too_many_points', '200 points'), ('too_many_elements', '2000 elements'),
    ('missing_image', 'Missing drawing image'), ('frame', 'Unsupported drawing element'),
])
def test_invalid_maps_block_whole_preview(setup, case, expected):
    app, client = setup
    files = bundle()
    graph = json.loads(files['maps/world.json'])
    node = graph['nodes'][0]
    if case == 'missing': del files['maps/world.json']
    elif case == 'kind': graph['kind'] = 'dungeon'
    elif case == 'invalid_json': files['maps/world.json'] = '{broken'
    elif case == 'nan': node['x'] = float('nan')
    elif case == 'bad_drawing': graph['drawing']['elements'][0]['type'] = 'iframe'
    elif case == 'unknown_article': node['article_id'] = 'old-database-id'
    elif case == 'duplicate_point': graph['nodes'].append(deepcopy(node))
    elif case == 'duplicate_number': graph['nodes'].append({**node, 'id': 'two'})
    elif case == 'duplicate_article': graph['nodes'].append({**node, 'id': 'two', 'number': 2})
    elif case == 'coordinate': node['x'] = 100001
    elif case == 'bad_geometry': node['geometry'] = {'type': 'ellipse'}
    elif case == 'bad_edge': graph['edges'] = [{'article_id': 'road', 'source': 'one', 'target': 'one'}]
    elif case == 'self_nested': node['nested_map'] = 'world'
    elif case == 'cross_campaign':
        files['other.md'] = md('Other campaign', 'Campaign')
        files['village.md'] = files['village.md'].replace('parent: World', 'parent: Other campaign')
    elif case == 'unsafe': files['world.md'] = files['world.md'].replace('maps/world.json', '../outside.json')
    elif case == 'obsidian_md':
        files['world.md'] = files['world.md'].replace('maps/world.json', 'maps/world.excalidraw.md')
        files['maps/world.excalidraw.md'] = '```compressed-json\nnot a normal scene\n```'
    elif case == 'wrong_article_type': files['world.md'] = files['world.md'].replace('type: Realm', 'type: Note')
    elif case == 'too_many_points': graph['nodes'] = [deepcopy(node) for _ in range(201)]
    elif case == 'too_many_elements': graph['drawing']['elements'] = [drawing()['elements'][0]] * 2001
    elif case == 'missing_image': graph['drawing']['elements'][0].update(type='image', fileId='missing')
    elif case == 'frame': graph['drawing']['elements'][0]['type'] = 'frame'
    if case not in ('missing', 'invalid_json'):
        files['maps/world.json'] = json.dumps(graph)
    response = upload(client, archive(files))
    html = response.get_data(as_text=True)
    assert expected in html and 'name="preview_id"' not in html
    with app.app_context():
        assert CampaignImport.query.count() == ContentEntry.query.count() == PointcrawlMap.query.count() == 0


def test_map_files_can_exceed_markdown_limit(setup):
    files = bundle()
    graph = json.loads(files['maps/world.json'])
    graph['drawing']['elements'] = [{**drawing()['elements'][0], 'id': f'text-{i}',
        'text': 'x' * 40000} for i in range(15)]
    files['maps/world.json'] = json.dumps(graph)
    assert len(files['maps/world.json']) > 512 * 1024
    preview = preview_archive(archive(files))
    assert preview['errors'] == []
    assert len(next(row for row in preview['rows'] if row['id'] == 'world')['map']['drawing']['elements']) == 15


def test_manifest_version_and_links_are_validated(setup):
    files = bundle()
    for manifest, expected in [
        ({'format': 'kettlewright-campaign', 'version': 2}, 'Unsupported'),
        ({'format': 'kettlewright-campaign', 'version': 1, 'links': [{'source': 'world', 'target': 'missing'}]}, 'Unknown article'),
        ({'format': 'kettlewright-campaign', 'version': 1, 'links': [{'source': 'world', 'target': 'world'}]}, 'distinct and unique'),
    ]:
        files['manifest.json'] = json.dumps(manifest)
        assert any(expected in error for error in preview_archive(archive(files))['errors'])


def test_geometry_nested_maps_and_manifest_only_old_export(setup):
    app, _ = setup
    files = bundle()
    files['world.md'] = files['world.md'].replace('map: maps/world.json\n', '')
    files['terrain.md'] = md('Marsh', 'Terrain', 'World').replace('layout: default\n', 'layout: default\nid: terrain\n')
    files['dungeon.md'] = md('Crypt', 'Dungeon', 'World').replace('layout: default\n', 'layout: default\nid: dungeon\n')
    graph = json.loads(files['maps/world.json'])
    geometry = {'type': 'rectangle', 'x': 50, 'y': 70, 'width': 100, 'height': 200, 'angle': 0}
    graph['nodes'].extend([
        {'id': 'two', 'article_id': 'terrain', 'number': 2, 'x': 50, 'y': 70, 'geometry': geometry},
        {'id': 'three', 'article_id': 'dungeon', 'number': 3, 'x': 100, 'y': 200, 'nested_map': 'dungeon'},
    ])
    graph['edges'] = [{'article_id': 'road', 'source': 'one', 'target': 'three'}]
    files['maps/world.json'] = json.dumps(graph)
    files['maps/dungeon.json'] = json.dumps({'article_id': 'dungeon', 'kind': 'dungeon',
        'drawing': drawing('Nested crypt'), 'nodes': [], 'edges': []})
    files['manifest.json'] = json.dumps({'format': 'kettlewright-campaign', 'version': 1,
        'maps': ['maps/world.json', 'maps/dungeon.json'], 'links': [{'source': 'village', 'target': 'dungeon'}]})
    files = {'campaign-bundle/' + name: text for name, text in files.items()}
    preview = preview_archive(archive(files, 'tar'))
    assert preview['errors'] == []
    with app.app_context():
        import_preview(preview, 1)
        db.session.commit()
        world = PointcrawlMap.query.filter_by(kind='realm').one()
        dungeon = PointcrawlMap.query.filter_by(kind='dungeon').one()
        assert next(node for node in world.nodes if node.number == 3).nested_map_id == dungeon.id
        restored = next(node for node in world.nodes if node.number == 2).geometry
        assert all(restored[key] == value for key, value in geometry.items())
        assert world.edges[0].entry.title == 'Road'
        assert ContentLink.query.one().target_id == dungeon.entry_id


def test_oversized_map_file_rejected():
    with pytest.raises(ImportError, match='16 MB'):
        preview_archive(archive({'map.json': 'x' * (MAX_MAP_FILE + 1)}))


def test_hand_drawn_example_imports(setup):
    from pathlib import Path
    app, _ = setup
    folder = Path(__file__).resolve().parents[2] / 'docs/examples/hand-drawn-campaign'
    files = {str(path.relative_to(folder)): path.read_text() for path in folder.rglob('*') if path.is_file()}
    preview = preview_archive(archive(files))
    assert preview['errors'] == []
    with app.app_context():
        import_preview(preview, 1)
        db.session.commit()
        pointcrawl = PointcrawlMap.query.one()
        assert len(pointcrawl.drawing['elements']) == 4
        assert not pointcrawl.nodes and not pointcrawl.edges

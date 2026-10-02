"""Typed draft persistence, authorization and lifecycle integration."""
import json
import pytest
from app.models import db, ContentEntry, Campaign, PointcrawlMap
from tests.unit.test_campaigns import setup, create_entry, create_map, login, reveal, graph_from_article


def draft():
    return [{'category':'people','title':'People','children':[
        {'category':'culture','title':'Culture','body':'Private culture'},
        {'category':'resources','title':'Resources'}, {'category':'npc','title':'Agent'}]},
        {'category':'settlement','title':'Heart village','is_heart':True},
        {'category':'paths','title':'Paths','children':[{'category':'path','title':'Trail','path_type':'hidden'}]}]


def test_tree_roundtrip_scope_publication_and_move(setup):
    app, client = setup
    root_id = create_entry(client,category='realm',children=json.dumps(draft()))
    with app.app_context():
        root = db.session.get(ContentEntry,root_id)
        assert root.version == 1
        assert {row.category for row in root.children} == {'people','settlement','paths'}
        rows = ContentEntry.query.all()
        assert len(rows) == 8
        assert all(row.owner_id == 1 and row.campaign_id == 1 for row in rows)
        assert next(row for row in rows if row.category == 'settlement').is_heart
        db.session.add(Campaign(id=2,owner_id=1,name='Destination'))
        db.session.commit()
    assert reveal(client,root_id).status_code == 302
    login(client,2)
    assert 'Private culture' not in client.get('/party/1/materials/data').get_data(as_text=True)
    login(client,1)
    assert client.post(f'/materials/{root_id}/edit',data={'version':1,'category':'realm','title':'Moved','campaign_id':2}).status_code == 302
    with app.app_context():
        assert {row.campaign_id for row in ContentEntry.query.all()} == {2}
    assert client.post(f'/materials/{root_id}/delete',data={'version':2}).status_code == 302
    with app.app_context():
        assert ContentEntry.query.count() == 0


@pytest.mark.parametrize('children',[
    [{'category':'location','title':'Old type'}],
    [{'category':'npc','title':'Wrong Heart','is_heart':True}],
    [{'category':'path','title':'Wrong path','path_type':'secret'}],
    [{'category':'people','title':'Parent','children':{}}],
    [{'category':'npc','title':'x'}]*1001,
])
def test_invalid_tree_rolls_back_everything(setup,children):
    app,client=setup
    response=client.post('/materials/new',data={'category':'realm','title':'Root','campaign_id':1,'children':json.dumps(children)})
    assert response.status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 0


def test_parent_owner_workspace_and_cycles(setup):
    app,client=setup
    root=create_entry(client,category='realm')
    child=create_entry(client,category='people',parent_id=root)
    assert client.post(f'/materials/{root}/edit',data={'version':1,'category':'realm','title':'Cycle','campaign_id':1,'parent_id':child}).status_code == 400
    assert client.post('/materials/new',data={'category':'npc','title':'Wrong workspace','parent_id':root}).status_code == 400
    login(client,4)
    assert client.post('/materials/new',data={'category':'npc','title':'Wrong owner','parent_id':root}).status_code == 403


def test_typed_map_roundtrip_and_standalone_path_publication(setup):
    app,client=setup
    map_id,graph=create_map(client)
    node=graph['nodes'][0]
    node.update(category='settlement',is_heart=True,content_changed=True)
    graph=client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).json
    assert graph['nodes'][0]['category'] == 'settlement'
    assert graph['nodes'][0]['is_heart'] is True
    node=graph['nodes'][0]
    node.update(category='npc',content_changed=True)
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code == 400
    path=create_entry(client,category='path',path_type='hidden')
    assert reveal(client,path,path_type_1='standard').status_code == 302
    login(client,2)
    assert client.get(f'/party/1/materials/{path}').status_code == 200


def test_map_draft_children_remain_private_and_form_has_types(setup):
    app,client=setup
    response=client.post('/maps/new',data={'kind':'realm','party_id':1,'title':'Map',
        'draft':json.dumps({'nodes':[],'edges':[],'children':draft()})})
    assert response.status_code == 302
    with app.app_context():
        root=PointcrawlMap.query.filter_by(kind='realm').one().entry
        assert root.category == 'realm'
        assert len(root.children) == 3
        assert all(not row.presentations for row in ContentEntry.query.filter(ContentEntry.id != root.id))
    html=client.get('/materials/new').get_data(as_text=True)
    assert 'Top Category' in html and 'Sub Category' in html and 'name="parent_id"' in html
    assert html.index('name="campaign_id"') < html.index('name="top_category"') < html.index('name="category"') < html.index('name="parent_id"')
    from app.lib.content_types import CATEGORIES, CATEGORY_GROUPS
    grouped = [key for keys in CATEGORY_GROUPS.values() for key in keys]
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == set(CATEGORIES) - {'map', 'overview'}
    assert 'value="location"' not in html
    html=client.get('/campaigns/').get_data(as_text=True)
    navigation=html.split('class="campaign-actions campaign-page-actions"')[1].split('</div>')[0]
    assert 'Unfiled articles' not in navigation
    assert 'Import archive' in navigation and 'New article' in navigation


def test_parent_form_advances_version_once_and_map_groups_roundtrip(setup):
    app,client=setup
    root=create_entry(client,category='realm')
    for version in [1,2]:
        response=client.post(f'/materials/{root}/edit',data={'version':version,'category':'realm',
            'title':f'Edit {version}','campaign_id':1,'parent_id':''})
        assert response.status_code == 302
        with app.app_context():
            assert db.session.get(ContentEntry,root).version == version+1
    payload={'nodes':[{'id':'new-1','title':'Village','category':'settlement','is_heart':True,
                       'number':1,'x':10,'y':10}], 'edges':[],
             'children':[{'category':'pois','title':'POIs'},{'category':'paths','title':'Paths'}]}
    response=client.post('/maps/new',data={'campaign_id':1,'kind':'realm','title':'Typed map','draft':json.dumps(payload)})
    assert response.status_code == 302
    map_id=graph_from_article(client,response.location)['id']
    graph=client.get(f'/maps/{map_id}/data').json
    with app.app_context():
        node=db.session.get(ContentEntry,graph['nodes'][0]['entry_id'])
        assert node.parent.category == 'pois'
        assert node.parent.parent.pointcrawl.id == map_id
    graph['nodes']=[]
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code == 200
    with app.app_context():
        assert ContentEntry.query.filter_by(title='Village').one().parent_id is None


def test_spatial_article_owns_canvas_and_reuses_existing_descendants(setup):
    app, client = setup
    root_id = create_entry(client, category='realm', children=json.dumps([
        {'category': 'pois', 'title': 'POIs', 'children': [
            {'category': 'dungeon', 'title': 'Keep', 'children': [
                {'category': 'room', 'title': 'Hall'}]}]}]))
    with app.app_context():
        root = db.session.get(ContentEntry, root_id)
        keep = root.children[0].children[0]
        assert ContentEntry.query.count() == 4
        assert root.pointcrawl.nodes[0].entry_id == keep.id
        assert root.pointcrawl.nodes[0].nested_map_id == keep.pointcrawl.id
        assert keep.pointcrawl.entry_id == keep.id
        assert keep.pointcrawl.nodes[0].entry_id == keep.children[0].id
        map_id = root.pointcrawl.id
    response = client.post(f'/materials/{root_id}/map', data={'version': 1})
    assert response.location.endswith(f'/materials/{root_id}/edit')
    with app.app_context():
        assert ContentEntry.query.count() == 4
        assert len(db.session.get(ContentEntry, root_id).pointcrawl.nodes) == 1
    login(client, 2)
    assert client.post(f'/materials/{root_id}/map', data={'version': 1}).status_code == 403


def test_picker_omits_legacy_types_and_root_labels_do_not_repeat(setup):
    import re
    from html import unescape
    _, client = setup
    html = client.get('/materials/new').get_data(as_text=True)
    groups = json.loads(unescape(re.search(r'data-category-groups="([^"]+)"', html)[1]))
    assert all(choice['value'] not in ('overview', 'map') for group in groups for choice in group['choices'])
    for name in ('Realm', 'People', 'Topography'):
        group = next(group for group in groups if group['value'] == name)
        assert group['choices'][0]['label'] == 'None'
    assert client.post('/materials/new', data={'title':'Old overview','category':'overview'}).status_code == 400


@pytest.mark.parametrize('kind',['realm','dungeon','forest','freeform'])
def test_generated_articles_open_with_embedded_drawing_and_legacy_links_redirect(setup,kind):
    app,client=setup
    response=client.post('/materials/generate',data={'title':'Generated article','kind':kind,'campaign_id':1})
    assert response.status_code==302
    assert response.location.startswith('/materials/') and response.location.endswith('/edit')
    graph=graph_from_article(client,response.location)
    page=client.get(response.location).get_data(as_text=True)
    assert 'form="article-form" name="graph"' in page
    assert 'Edit map' not in page and 'Save map' not in page and 'Open map' not in page
    assert client.get(f'/maps/{graph["id"]}/edit').location==response.location
    with app.app_context():
        entry_id=db.session.get(PointcrawlMap,graph['id']).entry_id
    assert reveal(client,entry_id,title='Known place').status_code==302
    public_url=f'/party/1/materials/{entry_id}'
    assert graph_from_article(client,public_url)['title']=='Known place'
    assert client.get(f'/party/1/maps/{graph["id"]}/').location==public_url
    assert 'form="article-form" name="graph"' not in client.get(public_url).get_data(as_text=True)
    ordinary=create_entry(client,category='note')
    assert 'data-graph=' not in client.get(f'/materials/{ordinary}/edit').get_data(as_text=True)


def test_article_text_and_drawing_save_atomically(setup):
    app,client=setup
    map_id,graph=create_map(client)
    with app.app_context():
        entry=db.session.get(PointcrawlMap,map_id).entry
        entry_id,version=entry.id,entry.version
    graph['nodes'][0]['x']=789
    data={'version':version,'title':'Updated article','body':'Updated text','campaign_id':1,
          'category':'dungeon','graph':json.dumps(graph)}
    response=client.post(f'/materials/{entry_id}/edit',data=data)
    assert response.status_code==302
    saved=graph_from_article(client,response.location)
    assert saved['title']=='Updated article' and saved['body']=='Updated text'
    assert saved['nodes'][0]['x']==789
    with app.app_context():
        data['version']=db.session.get(ContentEntry,entry_id).version
    data['title']='Must roll back'
    # Current article version with stale drawing version: neither part is saved.
    assert client.post(f'/materials/{entry_id}/edit',data=data).status_code==409
    assert graph_from_article(client,response.location)==saved


def test_existing_spatial_article_gets_canvas_without_new_article(setup):
    app, client = setup
    with app.app_context():
        entry = ContentEntry(owner_id=1, campaign_id=1, category='settlement', title='Existing town', body='Town')
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id
    assert 'Add drawing' in client.get(f'/materials/{entry_id}/edit').get_data(as_text=True)
    assert client.post(f'/materials/{entry_id}/map', data={'version': 9}).status_code == 409
    assert client.post(f'/materials/{entry_id}/map', data={'version': 1}).status_code == 302
    with app.app_context():
        assert ContentEntry.query.count() == 1
        assert PointcrawlMap.query.one().entry_id == entry_id


def test_generation_on_reused_point_requires_current_article_version(setup):
    from tests.unit.test_campaigns import nested_draft
    app, client = setup
    entry_id = create_entry(client, category='custom', title='Original', body='Keep me')
    map_id, graph = create_map(client, nodes=1)
    graph['nodes'].append({'id':'new-reused', 'entry_id': entry_id, 'number':2,
        'x':100, 'y':100, 'nested_draft':nested_draft(), 'entry_version':99})
    assert client.post(f'/maps/{map_id}/data', data={'graph':json.dumps(graph)}).status_code == 409
    with app.app_context():
        entry = db.session.get(ContentEntry, entry_id)
        assert entry.body == 'Keep me' and not entry.pointcrawl
    graph['nodes'][-1]['entry_version'] = 1
    saved = client.post(f'/maps/{map_id}/data', data={'graph':json.dumps(graph)})
    assert saved.status_code == 200
    with app.app_context():
        entry = db.session.get(ContentEntry, entry_id)
        assert entry.pointcrawl.entry_id == entry_id
        assert entry.version == 2
        assert entry.body.startswith('Keep me')


def test_nested_generation_retains_rich_description_and_rejects_overwrite(setup):
    from tests.unit.test_campaigns import nested_draft
    from app.lib.rich_content import RICH_PREFIX, render_content
    app, client = setup
    map_id, graph = create_map(client, nodes=1)
    graph['nodes'][0].update(body=RICH_PREFIX + '<p><strong>Keep me</strong></p>',
        content_changed=True, nested_draft=nested_draft())
    response = client.post(f'/maps/{map_id}/data', data={'graph':json.dumps(graph)})
    assert response.status_code == 200
    saved = response.json
    with app.app_context():
        entry = db.session.get(ContentEntry, saved['nodes'][0]['entry_id'])
        assert '<strong>Keep me</strong>' in render_content(entry.body)
        assert 'GENERATED PRIVATE INTERIOR' in render_content(entry.body)
        entry_count = ContentEntry.query.count()
    saved['nodes'][0].update(nested_map_id=None, nested_draft=nested_draft())
    assert client.post(f'/maps/{map_id}/data', data={'graph':json.dumps(saved)}).status_code == 409
    with app.app_context():
        assert ContentEntry.query.count() == entry_count


def test_saving_legacy_typed_entrance_preserves_its_linked_map(setup):
    app, client = setup
    parent_id, graph = create_map(client, nodes=1)
    nested_id, _ = create_map(client, nodes=1)
    with app.app_context():
        parent = db.session.get(PointcrawlMap, parent_id)
        parent.nodes[0].entry.category = 'dungeon'
        parent.nodes[0].nested_map = db.session.get(PointcrawlMap, nested_id)
        db.session.commit()
    graph = client.get(f'/maps/{parent_id}/data').json
    response = client.post(f'/maps/{parent_id}/data', data={'graph':json.dumps(graph)})
    assert response.status_code == 200
    assert response.json['nodes'][0]['nested_map_id'] == nested_id
    with app.app_context():
        assert PointcrawlMap.query.count() == 2


def realm_geography_draft():
    return [
        {'category':'topography','title':'Topography','children':[
            {'category':'terrain','title':'Terrain: Hills','children':[
                {'category':'water','title':'River','body':'Private water course'},
                {'category':'forest','title':'Forest','children':[
                    {'category':'ruins','title':'Hidden ruin'}]}]}]},
        {'category':'pois','title':'POIs','children':[
            {'category':'settlement','title':'Village','is_heart':True},
            {'category':'waypoint','title':'Watchtower'}]},
        {'category':'paths','title':'Paths','children':[
            {'category':'path','title':'Ridge path','path_type':'hidden'}]},
    ]


def test_realm_map_contains_geography_and_reuses_paths_without_tree_duplicates(setup):
    from app.lib.campaigns import material_hierarchy
    app, client = setup
    root_id = create_entry(client, category='realm', children=json.dumps(realm_geography_draft()))
    with app.app_context():
        root = db.session.get(ContentEntry, root_id)
        canvas = root.pointcrawl
        assert canvas.entry_id == root_id
        assert {node.entry.category for node in canvas.nodes} == {'terrain','water','forest','settlement','waypoint'}
        assert len(canvas.edges) == 1 and canvas.edges[0].entry.title == 'Ridge path'
        assert canvas.edges[0].entry.path_type == 'hidden'
        assert ContentEntry.query.count() == 11
        terrain = next(node for node in canvas.nodes if node.entry.category == 'terrain')
        water = next(node for node in canvas.nodes if node.entry.category == 'water')
        assert abs(water.x-terrain.x) < 320 and abs(water.y-terrain.y) < 350
        tree = material_hierarchy(ContentEntry.query.all())
        flattened = []
        def walk(branch):
            flattened.append(branch['entry'].id)
            for child in branch['children']:
                walk(child)
        for branch in tree:
            walk(branch)
        assert len(flattened) == len(set(flattened)) == 11
    html = client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    assert '<h2>Drawing</h2>' in html
    assert 'title="Drawing editor"' in html
    assert 'Prepare realm geography' not in html


def test_realm_geography_upgrade_is_private_idempotent_and_preserves_geometry(setup):
    app, client = setup
    root_id = create_entry(client, category='realm')
    with app.app_context():
        map_id = db.session.get(ContentEntry, root_id).pointcrawl.id
    payload = {'version':1,'article_version':1,'children':json.dumps(realm_geography_draft())}
    response = client.post(f'/maps/{map_id}/geography', data=payload)
    assert response.status_code == 200, response.get_data(as_text=True)
    graph = response.json
    assert len(graph['nodes']) == 5 and len(graph['edges']) == 1
    graph['nodes'][0]['x'] = -800
    saved = client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).json
    with app.app_context():
        count = ContentEntry.query.count()
    repeat = client.post(f'/maps/{map_id}/geography',data={
        'version':saved['version'],'article_version':1,'children':'[]'})
    assert repeat.status_code == 200
    assert repeat.json['nodes'] == saved['nodes']
    assert repeat.json['version'] == saved['version']
    with app.app_context():
        assert ContentEntry.query.count() == count
        assert all(not row.presentations for row in ContentEntry.query.all())
    assert client.post(f'/maps/{map_id}/geography',data=payload).status_code == 409
    payload['version'] = saved['version']
    assert client.post(f'/maps/{map_id}/geography',data=payload).status_code == 409
    login(client,2)
    assert client.post(f'/maps/{map_id}/geography',data=payload).status_code == 403


def test_realm_projection_reveals_only_published_geography(setup):
    app, client = setup
    root_id = create_entry(client, category='realm',children=json.dumps(realm_geography_draft()))
    with app.app_context():
        root = db.session.get(ContentEntry,root_id)
        map_id = root.pointcrawl.id
        water_id = next(node.entry_id for node in root.pointcrawl.nodes if node.entry.category=='water')
    assert reveal(client,root_id).status_code == 302
    public = client.get(f'/party/1/maps/{map_id}/data').json
    assert public['nodes'] == []
    assert 'realm_sections' not in public
    assert reveal(client,water_id,title='Known river',body='Public banks').status_code == 302
    public = client.get(f'/party/1/maps/{map_id}/data').json
    assert len(public['nodes']) == 1 and public['nodes'][0]['category'] == 'water'
    assert public['nodes'][0]['title'] == 'Known river'
    assert 'Private water course' not in json.dumps(public)
    assert 'is_heart' not in public['nodes'][0]


def test_geography_shapes_persist_and_follow_article_visibility(setup):
    app, client = setup
    root_id = create_entry(client, category='realm', children=json.dumps(realm_geography_draft()))
    graph = graph_from_article(client, f'/materials/{root_id}/edit')
    terrain = next(node for node in graph['nodes'] if node['category'] == 'terrain')
    water = next(node for node in graph['nodes'] if node['category'] == 'water')
    terrain['geometry'] = {'type':'line','x':10,'y':20,'width':900,'height':600,'angle':0,
                           'points':[[0,0],[900,0],[450,600],[0,0]],'strokeWidth':2}
    water['geometry'] = {'type':'freedraw','x':100,'y':100,'width':300,'height':100,'angle':0,
                         'points':[[0,0],[100,100],[300,0]],'strokeWidth':4}
    response = client.post(f'/maps/{graph["id"]}/data', data={'graph':json.dumps(graph)})
    assert response.status_code == 200
    reloaded = graph_from_article(client, f'/materials/{root_id}/edit')
    for original in (terrain, water):
        assert next(n for n in reloaded['nodes'] if n['id'] == original['id'])['geometry'] == original['geometry']
    assert reveal(client, root_id).status_code == 302
    assert client.get(f'/party/1/maps/{graph["id"]}/data').json['nodes'] == []
    assert reveal(client, water['entry_id']).status_code == 302
    public = client.get(f'/party/1/maps/{graph["id"]}/data').json
    assert len(public['nodes']) == 1
    assert public['nodes'][0]['geometry'] == water['geometry']
    # Invalid shapes fail atomically, preserving the saved coordinates.
    reloaded['nodes'][0]['x'] = 9876
    next(n for n in reloaded['nodes'] if n['id'] == water['id'])['geometry']['points'] = [[0,0],[float('inf'),0]]
    assert client.post(f'/maps/{graph["id"]}/data', data={'graph':json.dumps(reloaded)}).status_code == 400
    assert graph_from_article(client, f'/materials/{root_id}/edit')['nodes'][0]['x'] != 9876


@pytest.mark.parametrize('category', ['realm','forest','dungeon','terrain','water'])
def test_content_detection_includes_children_and_free_drawing(setup, category):
    app, client = setup
    root_id = create_entry(client, category=category)
    graph = graph_from_article(client, f'/materials/{root_id}/edit')
    assert graph['has_contents'] is False
    if category == 'realm':
        assert 'Prepare realm geography' in client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    create_entry(client, category='note', parent_id=root_id)
    graph = graph_from_article(client, f'/materials/{root_id}/edit')
    assert graph['has_contents'] is True
    assert 'Prepare realm geography' not in client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    blank_id = create_entry(client, category=category)
    graph = graph_from_article(client, f'/materials/{blank_id}/edit')
    graph['drawing'] = {'elements':[{'id':'river','type':'freedraw','x':0,'y':0,'width':100,'height':100,
                                   'angle':0,'points':[[0,0],[50,100],[100,50]]}], 'files':{}}
    assert client.post(f'/maps/{graph["id"]}/data',data={'graph':json.dumps(graph)}).status_code == 200
    assert graph_from_article(client, f'/materials/{blank_id}/edit')['has_contents'] is True
    assert 'Prepare realm geography' not in client.get(f'/materials/{blank_id}/edit').get_data(as_text=True)


def test_multiple_terrain_landmarks_survive_save_and_respect_publication(setup):
    app, client = setup
    children = [{'category':'topography','title':'Topography','children':[
        {'category':'terrain','title':f'Terrain {i}','children':[
            {'category':'landmark','title':f'Private landmark {i}'}]} for i in range(6)]}]
    root_id = create_entry(client,category='realm',children=json.dumps(children))
    with app.app_context():
        canvas = db.session.get(ContentEntry,root_id).pointcrawl
        map_id = canvas.id
    graph = client.get(f'/maps/{map_id}/data').json
    terrains = [node for node in graph['nodes'] if node['category']=='terrain']
    landmarks = [node for node in graph['nodes'] if node['category']=='landmark']
    assert len(terrains) == len(landmarks) == 6
    assert len({(node['x'],node['y']) for node in terrains}) == 6
    for landmark in landmarks:
        terrain = next(node for node in terrains if node['id']==landmark['terrain_id'])
        assert (landmark['x'],landmark['y']) == (terrain['x'],terrain['y'])
    landmark = landmarks[0]
    landmark['x'] += 120
    saved = client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)})
    assert saved.status_code == 200
    restored = client.get(f'/maps/{map_id}/data').json
    assert next(node for node in restored['nodes'] if node['id']==landmark['id'])['x'] == landmark['x']
    assert reveal(client,root_id).status_code == 302
    assert reveal(client,landmark['entry_id'],title='Known tower').status_code == 302
    public = client.get(f'/party/1/maps/{map_id}/data').json
    assert len(public['nodes']) == 1
    assert 'terrain_id' not in public['nodes'][0]
    assert 'Private landmark' not in json.dumps(public)
    terrain = next(node for node in terrains if node['id']==landmark['terrain_id'])
    assert reveal(client,terrain['entry_id'],title='Known hills').status_code == 302
    public = client.get(f'/party/1/maps/{map_id}/data').json
    assert next(node for node in public['nodes'] if node['category']=='landmark')['terrain_id'] == terrain['id']


def test_legacy_direct_publish_does_not_publish_new_geography_sections(setup):
    app, client = setup
    response = client.post('/maps/new',data={'kind':'realm','party_id':1,'title':'Region',
        'draft':json.dumps({'nodes':[],'edges':[],'children':realm_geography_draft()})})
    assert response.status_code == 302
    graph = graph_from_article(client,response.location)
    assert graph['nodes'] == []
    with app.app_context():
        root = PointcrawlMap.query.filter_by(kind='realm').one()
        assert len(root.nodes) == 5
        assert all(not node.entry.presentations for node in root.nodes)

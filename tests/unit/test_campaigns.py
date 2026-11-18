import json
from html import unescape
import re

import pytest
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import Session

from app.models import (db, User, Party, Character, Campaign, CampaignParty,
                        ContentEntry, ContentLink, PartyPresentation, PointcrawlMap, MapNode, MapEdge)
from app.lib.campaigns import render_content


def drawing(text='SECRET DRAWING'):
    return {'elements': [{'id': 'annotation', 'type': 'text', 'x': 10, 'y': 20,
        'width': 100, 'height': 30, 'angle': 0, 'text': text}], 'files': {}}


@pytest.mark.parametrize('kind', ['dungeon', 'freeform'])
def test_drawing_publication_is_explicit_independent_and_revocable(setup, kind):
    app, client = setup
    map_id, graph = create_map(client, kind=kind, nodes=0 if kind == 'freeform' else 2)
    assert graph['kind'] == kind
    entry_id = map_entry_id(app, map_id)
    graph['drawing'] = drawing()
    response = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    assert response.status_code == 200
    graph = response.json
    assert reveal(client, entry_id).status_code == 302
    assert client.get(f'/party/1/maps/{map_id}/data').json['drawing']['elements'] == []
    assert reveal(client, entry_id, version=1, publish_drawing='1', map_version=graph['version']).status_code == 302
    graph['drawing'] = drawing('CHANGED PRIVATE DRAWING')
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    assert reveal(client, entry_id, version=2, publish_drawing='1', map_version=graph['version']).status_code == 409
    login(client, 2)
    published = client.get(f'/party/1/maps/{map_id}/data')
    assert published.json['kind'] == kind
    assert 'SECRET DRAWING' in published.get_data(as_text=True)
    assert 'CHANGED PRIVATE DRAWING' not in published.get_data(as_text=True)
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 403
    login(client, 1)
    assert client.post(f'/materials/{entry_id}/revoke/1', data={'version': 2}).status_code == 302
    assert client.get(f'/party/1/maps/{map_id}/data').status_code == 404


@pytest.mark.parametrize('mutation', ['embed', 'invalid_image', 'managed', 'nan'])
def test_invalid_drawing_does_not_replace_saved_graph(setup, mutation):
    app, client = setup
    map_id, graph = create_map(client)
    original = json.loads(json.dumps(graph))
    graph['drawing'] = drawing()
    element = graph['drawing']['elements'][0]
    if mutation == 'embed': element['type'] = 'iframe'
    elif mutation == 'invalid_image': element.update(type='image', fileId='missing')
    elif mutation == 'managed': element['id'] = 'kw-label-private'
    elif mutation == 'nan': element['x'] = float('nan')
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 400
    assert client.get(f'/maps/{map_id}/data').json == original


@pytest.mark.parametrize('kind', ['dungeon', 'freeform'])
def test_new_map_keeps_drawing_and_drops_unused_files(setup, kind):
    app, client = setup
    draft = {'nodes': [], 'edges': [], 'drawing': drawing('PUBLIC DRAWING')}
    draft['drawing']['files']['unused'] = {'dataURL': 'SECRET UNUSED FILE'}
    response = client.post('/maps/new', data={'title': 'Shared map',
        'kind': kind, 'draft': json.dumps(draft)})
    assert response.status_code == 302
    graph = graph_from_article(client,response.location)
    assert graph['kind'] == kind
    assert graph['drawing']['elements'][0]['text'] == 'PUBLIC DRAWING'
    assert graph['drawing']['files'] == {}


def test_drawing_image_roundtrip_and_content_validation(setup):
    import base64
    import io
    from PIL import Image
    app, client = setup
    map_id, graph = create_map(client)
    image = io.BytesIO()
    Image.new('RGB', (2, 2), color='red').save(image, format='PNG')
    graph['drawing'] = {'elements': [{'id': 'token', 'type': 'image', 'x': 0, 'y': 0,
        'width': 40, 'height': 40, 'fileId': 'token-image'}], 'files': {
        'token-image': {'mimeType': 'image/png', 'dataURL': 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode()}}}
    response = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    assert response.status_code == 200
    assert response.json['drawing']['files']['token-image']['dataURL'].startswith('data:image/png;base64,')
    graph = response.json
    graph['drawing']['files']['token-image']['dataURL'] = 'data:image/png;base64,' + base64.b64encode(b'not an image').decode()
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 400


@pytest.fixture
def setup(app_with_babel, tmp_path):
    app = app_with_babel
    app.config.update(LOCAL_FEATURE_ACCESS=False, FEATURE_TEST_USER_IDS=set(), FEATURE_TEST_PARTY_IDS=set())
    app.config['MATERIAL_IMAGE_UPLOAD_FOLDER'] = str(tmp_path / 'material-images')
    with app.app_context():
        db.session.add_all([User(id=i, username=f'user{i}') for i in range(1, 5)])
        db.session.add_all([Party(id=i, owner=1 if i < 3 else 4, name=f'Party {i}',
            owner_username='user1' if i < 3 else 'user4', party_url=f'party{i}', members=json.dumps([i]),
            items='[]', containers='[{"id":0,"name":"Main","slots":10}]') for i in range(1, 4)])
        db.session.add_all([Character(id=1, owner=2, party_id=1, name='Player A', background='Test'),
                            Character(id=2, owner=3, party_id=2, name='Player B', background='Test')])
        db.session.add(Campaign(id=1, owner_id=1, name='Secret campaign'))
        db.session.add_all([CampaignParty(campaign_id=1, party_id=i) for i in (1, 2)])
        db.session.commit()
    client = app.test_client()
    login(client, 1)
    return app, client


def login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def create_entry(client, **values):
    result = client.post('/materials/new', data={'category':'npc', 'title':'SECRET NAME',
        'body':'SECRET BODY', 'campaign_id':1, **values})
    assert result.status_code == 302, result.get_data(as_text=True)
    return int(re.search(r'/materials/(\d+)/edit', result.location).group(1))


def reveal(client, entry_id, party_id=1, version=0, title='Known name', body='Known facts', mode='custom', **extra):
    """Reveal a version written for the party (mode=custom) unless another mode is given."""
    return client.post(f'/materials/{entry_id}/reveal', data={'party_ids':str(party_id),
        f'version_{party_id}':version, 'mode':mode, 'title':title, 'body':body, **extra})


def graph_from_article(client, url):
    page = client.get(url, follow_redirects=True).get_data(as_text=True)
    return json.loads(unescape(re.search(r'data-graph="([^"]+)"', page)[1]))


def create_map(client, campaign_id=1, title='SECRET MAP', nodes=2, kind='dungeon'):
    draft={'nodes':[{'id':f'new-node-{i}', 'number':i+1,'x':i*100,'y':100,
        'title':f'SECRET ROOM {i}', 'body':f'SECRET TRAP {i}'} for i in range(nodes)],
        'edges':[{'id':'new-edge-0','source':'new-node-0','target':'new-node-1',
                  'title':'SECRET PASSAGE','body':'SECRET KEY','path_type':'hidden'}] if nodes>1 else []}
    response=client.post('/maps/new',data={'campaign_id':campaign_id,'title':title,
        'kind':kind,'draft':json.dumps(draft)})
    assert response.status_code==302, response.get_data(as_text=True)
    map_id=graph_from_article(client,response.location)['id']
    return map_id,client.get(f'/maps/{map_id}/data').json


def map_entry_id(app, map_id):
    with app.app_context():
        return db.session.get(PointcrawlMap,map_id).entry_id


def test_private_default_and_owner_routes(setup):
    app,client=setup
    entry_id=create_entry(client)
    assert client.get('/campaigns/1/').status_code==200
    assert client.get('/materials/').status_code==200
    assert client.get(f'/materials/{entry_id}/edit').status_code==200
    assert client.get(f'/materials/{entry_id}/reveal').status_code==200
    login(client,2)
    assert client.get('/party/1/materials/data').json=={'entries':[]}
    for path in ['/campaigns/1/', f'/materials/{entry_id}/edit',f'/materials/{entry_id}/reveal']:
        assert client.get(path).status_code==403
    assert client.get(f'/party/1/materials/{entry_id}').status_code==404
    assert client.get('/party/2/materials/data').status_code==403
    assert client.post(f'/materials/{entry_id}/delete',data={'version':1}).status_code==403
    login(client,4)
    assert client.get('/party/1/materials/').status_code==403


def test_independent_versions_original_changes_and_safe_links(setup):
    app,client=setup
    entry_id=create_entry(client)
    target_id=create_entry(client,title='SECRET TARGET')
    assert reveal(client,entry_id,title='Alias A').status_code==302
    assert reveal(client,entry_id,party_id=2,title='Alias B').status_code==302
    assert client.post(f'/materials/{entry_id}/edit',data={'version':1,'title':'NEW SECRET',
        'body':'NEW SECRET BODY','category':'npc','campaign_id':1,'links':target_id}).status_code==302
    for user,party,title in [(2,1,'Alias A'),(3,2,'Alias B')]:
        login(client,user)
        response=client.get(f'/party/{party}/materials/data')
        assert 'SECRET' not in response.get_data(as_text=True)
        assert response.json['entries'][0]['title']==title
        assert response.json['entries'][0]['links']==[]
    login(client,1)
    assert reveal(client,target_id,title='Known target').status_code==302
    login(client,2)
    entries=client.get('/party/1/materials/data').json['entries']
    assert entries[0]['links']==[{'id':target_id,'title':'Known target'}]


def test_new_articles_and_maps_are_private_even_with_a_party_id(setup):
    """"Create and show" is gone: articles are created privately, then revealed."""
    app, client = setup
    article = client.post('/materials/new', data={'party_id': 1, 'category': 'lore', 'title': 'Rumour', 'body': 'Heard'})
    assert article.status_code == 302 and '/party/' not in article.location
    draft = {'nodes': [{'id': 'new-a', 'number': 1, 'x': 100, 'y': 100, 'title': 'Place', 'body': 'Facts'}], 'edges': []}
    drawn = client.post('/maps/new', data={'party_id': 1, 'title': 'Drawn', 'kind': 'realm', 'draft': json.dumps(draft)})
    assert drawn.status_code == 302 and '/party/' not in drawn.location
    with app.app_context():
        assert ContentEntry.query.filter_by(title='Rumour').one().body == 'Heard'
        assert PartyPresentation.query.count() == 0
    assert 'Create and show' not in client.get('/materials/new?party_id=1').text


def test_republish_revoke_conflicts_and_membership(setup):
    app,client=setup
    entry_id=create_entry(client)
    assert reveal(client,entry_id).status_code==302
    assert reveal(client,entry_id,version=0,title='Stale').status_code==409
    assert reveal(client,entry_id,version=1,title='Updated').status_code==302
    assert client.post(f'/materials/{entry_id}/revoke/1',data={'version':1}).status_code==409
    assert client.post(f'/materials/{entry_id}/revoke/1',data={'version':2}).status_code==302
    login(client,2)
    assert client.get('/party/1/materials/data').json['entries']==[]
    login(client,1)
    assert reveal(client,entry_id,version=0).status_code==302  # Hide deleted the version: revealing starts anew.
    with app.app_context():
        db.session.get(Character,1).party_id=None
        # A stale subowners list must not grant access.
        db.session.get(Party,1).subowners='[2]'
        db.session.commit()
    login(client,2)
    assert client.get('/party/1/materials/data').status_code==403
    assert client.get(f'/party/1/materials/{entry_id}').status_code==403


def test_reveal_goes_to_one_party_at_a_time(setup):
    app,client=setup
    entry_id=create_entry(client)
    assert reveal(client,entry_id,party_id=2,version=5).status_code==409
    with app.app_context():
        assert PartyPresentation.query.count()==0
    assert client.post(f'/materials/{entry_id}/reveal',data={'party_ids':['1','2'],'mode':'custom',
        'version_1':0,'version_2':0,'title':'A','body':'A facts'}).status_code==302
    with app.app_context():  # Only the first party submitted: the popup chooses one.
        assert [(p.party_id, p.title) for p in PartyPresentation.query] == [(1,'A')]
    assert reveal(client,entry_id,party_id=3).status_code==403


def test_reveal_popup_original_or_party_version_and_hide(setup):
    """Reveal to party: one party, then the original or a party version. Hide deletes the version."""
    app, client = setup
    entry_id = create_entry(client)  # SECRET NAME / SECRET BODY
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').text
    assert f'id="reveal-dialog-{entry_id}"' in page and 'name="party_ids"' in page and 'class="wiki-reveal-menu"' not in page
    assert 'Original' in page and 'Party version' in page and 'Title only' not in page
    assert f'id="reveal-dialog-{entry_id}"' in client.get(f'/materials/{entry_id}/edit').text  # Same popup in Edit.

    def shown(party_id):
        with app.app_context():
            row = PartyPresentation.query.filter_by(entry_id=entry_id, party_id=party_id).first()
            return row and (row.title, row.body, row.version)

    # Original: the private title and text as they are now; back to the article afterwards.
    original = client.post(f'/materials/{entry_id}/reveal', data={'party_ids': '1', 'version_1': 0, 'mode': 'everything',
                                                                 'return_to': 'article', 'title': 'ignored'})
    assert original.location == f'/campaigns/1/wiki/{entry_id}/'
    assert shown(1) == ('SECRET NAME', 'SECRET BODY', 1)
    data = client.get(f'/campaigns/1/wiki/{entry_id}/').text
    assert '&#34;status&#34;: &#34;same&#34;' in data and '&#34;status&#34;: &#34;none&#34;' in data  # Party 1, party 2.

    # A "party version" left identical to the original counts as the original, and the message says so.
    same = client.post(f'/materials/{entry_id}/reveal', data={'party_ids': '1', 'version_1': 1, 'mode': 'custom',
                                                             'title': 'SECRET NAME', 'body': 'SECRET BODY'}, follow_redirects=True)
    assert 'counts as the original' in same.text and shown(1) == ('SECRET NAME', 'SECRET BODY', 1)  # Nothing changed.
    # Party version: written for them; opens on it next time.
    assert reveal(client, entry_id, version=1, title='The guildmaster', body='Polite').status_code == 302
    assert shown(1) == ('The guildmaster', 'Polite', 2)
    assert '&#34;status&#34;: &#34;custom&#34;' in client.get(f'/campaigns/1/wiki/{entry_id}/').text
    assert reveal(client, entry_id, version=2, title=' ').status_code == 400  # A party version needs a title.
    assert reveal(client, entry_id, version=2, mode='title').status_code == 400  # No other modes.

    # Hide deletes the party version; the party tree can hide too, and returns to the party.
    assert client.post(f'/materials/{entry_id}/revoke/1', data={'version': 2}).location == f'/campaigns/1/wiki/{entry_id}/'
    assert shown(1) is None
    assert reveal(client, entry_id, party_id=2, version=0, mode='everything').status_code == 302
    hidden = client.post(f'/materials/{entry_id}/revoke/2', data={'version': 1, 'return_to': 'party'})
    assert hidden.location == '/users/user1/parties/party2/#campaign-details' and shown(2) is None

    # The page form (from the party tree) preselects the party and returns there.
    page = client.get(f'/materials/{entry_id}/reveal?party_id=1&return_to=party').text
    assert 'data-selected="1"' in page and 'name="return_to" value="party"' in page
    assert client.post(f'/materials/{entry_id}/reveal', data={'party_ids': '1', 'version_1': 0, 'mode': 'everything',
                                                              'return_to': 'party'}).location == '/users/user1/parties/party1/#campaign-details'
    assert client.post(f'/materials/{entry_id}/reveal', data={'party_ids': '2', 'version_2': 0, 'mode': 'everything',
                                                              'return_to': 'https://evil.example'}).location == f'/campaigns/1/wiki/{entry_id}/'


def test_party_tree_labels_edits_and_hides_party_versions(setup):
    """Party's Wiki tab: each revealed article says Original or Party version, with Edit and Hide."""
    app, client = setup
    entry_id = create_entry(client)  # SECRET NAME / SECRET BODY
    assert reveal(client, entry_id, mode='everything').status_code == 302
    html = client.get('/party/1/materials/').text
    assert 'class="party-card"' in html and 'party-card-cover' not in html  # Small card; no picture in this text.
    assert f'href="/party/1/materials/{entry_id}/version"' not in html  # No Edit on the original: that is in Campaigns.
    assert f'/party/1/materials/{entry_id}/version' not in client.get(f'/party/1/materials/{entry_id}').text
    assert f'action="/materials/{entry_id}/revoke/1"' in html and ' Hide</button>' in html
    assert 'data-confirm="Hide this article from the party?' in html and 'confirm(' not in html  # Modal, not confirm().
    assert 'Change what they see' not in html and 'Private original' not in html and f'/materials/{entry_id}/edit' not in html

    page = client.get(f'/party/1/materials/{entry_id}/version').text
    assert 'What Party 1 sees' in page and 'They see the original.' in page and 'Use the original instead' not in page
    assert client.post(f'/party/1/materials/{entry_id}/version', data={'version': 9, 'title': 'X'}).status_code == 409
    saved = client.post(f'/party/1/materials/{entry_id}/version', data={'version': 1, 'title': 'The guildmaster', 'body': 'Polite'})
    assert saved.location == '/users/user1/parties/party1/#campaign-details'
    with app.app_context():
        row = PartyPresentation.query.filter_by(entry_id=entry_id, party_id=1).one()
        assert (row.title, row.body) == ('The guildmaster', 'Polite')
        assert db.session.get(ContentEntry, entry_id).title == 'SECRET NAME'  # The original is unchanged.
    html = client.get('/party/1/materials/').text
    assert f'href="/party/1/materials/{entry_id}/version"' in html  # A party version: Edit appears.

    # Back to the original from the same page.
    page = client.get(f'/party/1/materials/{entry_id}/version').text
    assert 'They see a party version.' in page and 'Use the original instead' in page
    assert client.post(f'/materials/{entry_id}/reveal', data={'party_ids': '1', 'version_1': 2, 'mode': 'everything',
                                                              'return_to': 'party'}).status_code == 302
    assert f'/party/1/materials/{entry_id}/version' not in client.get('/party/1/materials/').text  # Original again.

    assert client.get(f'/party/2/materials/{entry_id}/version').status_code == 404  # Not revealed to party 2.
    assert client.get(f'/party/3/materials/{entry_id}/version').status_code == 403  # Someone else's party.


def test_party_cards_take_their_picture_from_the_party_text(setup):
    app, client = setup
    png = 'data:image/png;base64,' + 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
    entry_id = create_entry(client, body=f'Secret ![map]({png})')
    assert reveal(client, entry_id, body='Told without a picture').status_code == 302
    html = client.get('/party/1/materials/').text
    assert 'party-card-cover' not in html  # The original's picture never leaks into the card.
    assert client.get(f'/party/1/materials/{entry_id}/image').status_code == 404
    assert reveal(client, entry_id, version=1, body=f'Seen: ![sketch]({png})').status_code == 302
    html = client.get('/party/1/materials/').text
    assert f'src="/party/1/materials/{entry_id}/image"' in html
    image = client.get(f'/party/1/materials/{entry_id}/image')
    assert image.status_code in (200, 302)  # Stored uploads redirect to their (access-checked) file.
    assert client.get(f'/party/2/materials/{entry_id}/image').status_code == 404  # Not shown to party 2.


def test_map_reveal_shows_points_and_paths_progress(setup):
    app, client = setup
    map_id, _ = create_map(client)  # Two rooms joined by one path.
    root = map_entry_id(app, map_id)
    with app.app_context():
        room = db.session.get(PointcrawlMap, map_id).nodes[0].entry.id
    assert reveal(client, room).status_code == 302
    page = client.get(f'/campaigns/1/wiki/{root}/').text
    assert 'Points of interest revealed: {points} of 2' in page and 'Paths: {paths} of 1' in page
    assert '&#34;paths&#34;: 0, &#34;points&#34;: 1' in page and '&#34;paths&#34;: 0, &#34;points&#34;: 0' in page  # Party 1, party 2.
    assert 'Also show the map drawing' in page


def test_map_projection_filters_geometry_and_nested_maps(setup):
    app,client=setup
    map_id,graph=create_map(client)
    nested_id,_=create_map(client,title='SECRET NESTED',nodes=0)
    graph['nodes'][0]['nested_map_id']=nested_id
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code==200
    root_id=map_entry_id(app,map_id)
    nested_root=map_entry_id(app,nested_id)
    reveal(client,root_id,title='Known region')
    reveal(client,graph['nodes'][0]['entry_id'],title='Known entrance')
    # Revealing a path alone must not expose its hidden destination.
    reveal(client,graph['edges'][0]['entry_id'],title='Known path')
    login(client,2)
    response=client.get(f'/party/1/maps/{map_id}/data')
    assert response.status_code==200
    assert len(response.json['nodes'])==1
    assert response.json['nodes'][0]['nested_map_id'] is None
    assert response.json['edges']==[]
    assert 'SECRET' not in response.get_data(as_text=True)
    assert 'version' not in response.json
    assert client.get(f'/party/1/materials/{graph["edges"][0]["entry_id"]}').status_code==404
    assert client.get(f'/party/1/maps/{nested_id}/data').status_code==404
    assert client.get(f'/maps/{map_id}/data').status_code==403
    assert 'SECRET' not in client.get(f'/party/1/maps/{map_id}/').get_data(as_text=True)
    login(client,1)
    reveal(client,graph['nodes'][1]['entry_id'],title='Known destination')
    reveal(client,nested_root,title='Known dungeon')
    login(client,2)
    known=client.get(f'/party/1/maps/{map_id}/data').json
    assert len(known['edges'])==1
    assert known['edges'][0]['path_type']=='standard' # Private hidden type is not inherited.
    assert known['nodes'][0]['nested_map_id']==nested_id
    login(client,3)
    assert client.get(f'/party/2/maps/{map_id}/data').status_code==404


def test_geometry_roundtrip_conflicts_and_new_points_private(setup):
    app,client=setup
    map_id,graph=create_map(client)
    reveal(client,map_entry_id(app,map_id),title='Map')
    reveal(client,graph['nodes'][0]['entry_id'],title='Location')
    graph['nodes'][0]['x']=999
    graph['nodes'].append({'id':'new-added','number':3,'x':400,'y':400,'title':'SECRET NEW','body':'SECRET NEW BODY'})
    response=client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)})
    assert response.status_code==200
    assert response.json['version']>graph['version']
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code==409
    login(client,2)
    public=client.get(f'/party/1/maps/{map_id}/data').json
    assert len(public['nodes'])==1
    assert public['nodes'][0]['x']==999


@pytest.mark.parametrize('mutation', ['foreign_node','foreign_edge','foreign_map','bad_coordinate','duplicate_number','bad_endpoint'])
def test_invalid_graph_is_atomic(setup, mutation):
    app,client=setup
    map_id,graph=create_map(client)
    other_id,other=create_map(client)
    original=json.loads(json.dumps(graph))
    if mutation=='foreign_node': graph['nodes'][0]['id']=other['nodes'][0]['id']
    if mutation=='foreign_edge': graph['edges'][0]['id']=other['edges'][0]['id']
    if mutation=='foreign_map': graph['nodes'][0]['nested_map_id']=map_id
    if mutation=='bad_coordinate': graph['nodes'][0]['x']=float('nan')
    if mutation=='duplicate_number': graph['nodes'][0]['number']=graph['nodes'][1]['number']
    if mutation=='bad_endpoint': graph['edges'][0]['target']=999999
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code==400
    assert client.get(f'/maps/{map_id}/data').json==original


def test_remove_map_elements_removes_presentations(setup):
    app,client=setup
    map_id,graph=create_map(client)
    edge_entry=graph['edges'][0]['entry_id']
    reveal(client,edge_entry)
    graph['nodes']=graph['nodes'][:1]
    graph['edges']=[]
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code==200
    with app.app_context():
        assert MapEdge.query.count()==0
        assert MapNode.query.count()==1
        assert db.session.get(ContentEntry,edge_entry) is None
        assert PartyPresentation.query.filter_by(entry_id=edge_entry).count()==0


def test_party_deletion_keeps_campaign_originals(setup):
    app,client=setup
    entry_id=create_entry(client)
    reveal(client,entry_id)
    assert client.post('/party/delete/1').status_code==200
    with app.app_context():
        assert db.session.get(ContentEntry,entry_id) is not None
        assert db.session.get(Campaign,1) is not None
        assert PartyPresentation.query.count()==0
        assert db.session.get(CampaignParty,(1,1)) is None


def test_hide_everything_and_deleting_campaign_removes_materials(setup):
    app,client=setup
    entry_id=create_entry(client)
    reveal(client,entry_id)
    reveal(client,entry_id,party_id=2)
    assert client.post('/campaigns/1/hide/1').location=='/campaigns/1/wiki/'
    with app.app_context():  # Party 1's versions are deleted; party 2 keeps its own.
        assert [p.party_id for p in PartyPresentation.query.filter_by(entry_id=entry_id)]==[2]
    assert client.post('/campaigns/1/hide/3').status_code==403  # Not my party.
    login(client,2)
    assert client.get('/party/1/materials/data').json['entries']==[]
    login(client,1)
    assert client.post('/campaigns/1/delete',data={'version':1,'confirm':'delete'}).status_code==302
    with app.app_context():
        assert db.session.get(ContentEntry,entry_id) is None
        assert PartyPresentation.query.filter_by(entry_id=entry_id).count() == 0


def test_xss_and_protocols():
    value=str(render_content('<script>alert(1)</script>\njavascript:alert(1) https://example.com/path'))
    assert '<script>' not in value
    assert '<p>' in value
    assert 'href="javascript:' not in value
    assert 'href="https://example.com/path"' in value


def test_csrf_is_required_and_generated_form_works(setup):
    app,client=setup
    app.config['WTF_CSRF_ENABLED']=True
    assert client.post('/campaigns/',data={'name':'No token'}).status_code==400
    page=client.get('/campaigns/').get_data(as_text=True)
    token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page).group(1)
    assert client.post('/campaigns/',data={'name':'With token','csrf_token':token}).status_code==302


def test_socket_notifications_have_no_content(setup, monkeypatch):
    app,client=setup
    from app import socketio
    calls=[]
    monkeypatch.setattr(socketio,'emit',lambda event,payload,**kw: calls.append((event,payload,kw)))
    entry_id=create_entry(client)
    assert not calls
    reveal(client,entry_id)
    assert {kw['room'] for event,payload,kw in calls}=={'user_1','user_2'}
    assert all(event=='campaign_content_changed' and payload=={'party_id':1} for event,payload,kw in calls)


def test_parallel_session_updates_are_rejected(setup):
    app,client=setup
    entry_id=create_entry(client)
    with app.app_context():
        with Session(db.engine) as first, Session(db.engine) as second:
            a=first.get(ContentEntry,entry_id)
            b=second.get(ContentEntry,entry_id)
            a.title='First';first.commit()
            b.title='Second'
            with pytest.raises(StaleDataError): second.commit()


def test_templates_and_tools_handoff(setup):
    app,client=setup
    for path in ['/campaigns/','/campaigns/1/','/materials/','/materials/new',
                 '/materials/import','/materials/generate','/tools/']:
        response=client.get(path)
        assert response.status_code==200, (path,response.get_data(as_text=True))
    map_id,_=create_map(client)
    assert client.get(f'/maps/{map_id}/edit').location == f'/materials/{map_entry_id(app,map_id)}/edit'
    assert set(client.get('/maps/tables').json)=={'Dungeon','Forest','Realm','NPCGenerator','Names'}


def test_delete_location_cleans_paths_and_conflicts_with_old_map_editor(setup):
    app,client=setup
    map_id,graph=create_map(client)
    edge_id=graph['edges'][0]['entry_id']
    reveal(client,edge_id)
    response=client.post(f'/materials/{graph["nodes"][0]["entry_id"]}/delete',data={'version':1})
    assert response.status_code==302
    assert client.post(f'/maps/{map_id}/data',data={'graph':json.dumps(graph)}).status_code==409
    with app.app_context():
        assert db.session.get(ContentEntry,edge_id) is None
        assert PartyPresentation.query.filter_by(entry_id=edge_id).count()==0


def test_adopt_standalone_map_retains_published_knowledge(setup):
    app,client=setup
    map_id,graph=create_map(client,campaign_id='')
    root_id=map_entry_id(app,map_id)
    reveal(client,root_id,title='Known map')
    reveal(client,graph['nodes'][0]['entry_id'],title='Known place')
    assert client.post(f'/materials/{root_id}/edit',data={'version':1,'title':'Private map',
        'body':'Private theme','campaign_id':1}).status_code==302
    with app.app_context():
        assert all(entry.campaign_id==1 for entry in ContentEntry.query.all())
    login(client,2)
    response=client.get(f'/party/1/maps/{map_id}/data')
    assert response.json['title']=='Known map'
    assert response.json['nodes'][0]['title']=='Known place'


def nested_draft(kind='dungeon'):
    return {'kind': kind, 'body': 'GENERATED PRIVATE INTERIOR', 'nodes': [
        {'id': 'new-room-1', 'number': 1, 'x': 100, 'y': 100, 'title': 'Entrance'},
        {'id': 'new-room-2', 'number': 2, 'x': 200, 'y': 100, 'title': 'Treasure'}],
        'edges': [{'id': 'new-path-1', 'source': 'new-room-1', 'target': 'new-room-2',
                   'title': 'Secret door', 'path_type': 'hidden'}]}


@pytest.mark.parametrize('kind', ['dungeon', 'forest'])
@pytest.mark.parametrize('campaign_id', [1, ''])
def test_map_pois_are_children_not_workspace_locations(setup, kind, campaign_id):
    app, client = setup
    standalone = create_entry(client, campaign_id=campaign_id, category='location', title='Standalone')
    response = client.post('/maps/new', data={'campaign_id': campaign_id, 'title': 'Root map',
        'kind': kind, 'draft': json.dumps(nested_draft(kind))})
    map_id = graph_from_article(client,response.location)['id']
    graph = client.get(f'/maps/{map_id}/data').json
    root_id = map_entry_id(app, map_id)
    workspace = f'/campaigns/{campaign_id}/' if campaign_id else '/materials/'
    html = client.get(workspace).get_data(as_text=True)
    assert set(map(int, re.findall(r'data-root-entry-id="(\d+)"', html))) == {standalone, root_id}
    assert set(map(int, re.findall(r'data-child-entry-id="(\d+)"', html))) == {n['entry_id'] for n in graph['nodes'] + graph['edges']}
    for node in graph['nodes']:
        page = client.get(f'/materials/{node["entry_id"]}/edit').get_data(as_text=True)
        parents = re.search(r'<nav class="material-parents".*?</nav>', page, re.S)[0]
        assert f'href="/materials/{root_id}/edit"' in parents
        assert 'Root map' in parents
    # A detached original still exists and becomes standalone, as before.
    removed_id = graph['nodes'].pop()['entry_id']
    graph['edges'] = []
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    html = client.get(workspace).get_data(as_text=True)
    assert f'data-root-entry-id="{removed_id}"' in html


@pytest.mark.parametrize('kind', ['dungeon', 'forest'])
def test_nested_maps_follow_entrance_in_material_hierarchy(setup, kind):
    from app.lib.campaigns import material_hierarchy
    app, client = setup
    map_id, graph = create_map(client)
    graph['nodes'][0]['nested_draft'] = nested_draft(kind)
    saved = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).json
    child_map_id = saved['nodes'][0]['nested_map_id']
    child_id = map_entry_id(app, child_map_id)
    root_id = map_entry_id(app, map_id)
    with app.app_context():
        tree = material_hierarchy(ContentEntry.query.filter_by(owner_id=1, campaign_id=1).all())
        assert [item['entry'].id for item in tree] == [root_id]
        entrance = tree[0]['children'][0]
        assert entrance['entry'].id == saved['nodes'][0]['entry_id']
        assert entrance['number'] == 1
        assert entrance['entry'].id == child_id
        assert [item['entry'].title for item in entrance['children']] == ['Entrance', 'Treasure', 'Secret door']
    html = client.get('/campaigns/1/').get_data(as_text=True)
    assert re.findall(r'data-root-entry-id="(\d+)"', html) == [str(root_id)]
    child_page = client.get(f'/materials/{child_id}/edit').get_data(as_text=True)
    parents = re.search(r'<nav class="material-parents".*?</nav>', child_page, re.S)[0]
    assert f'/materials/{root_id}/edit' in parents


def test_legacy_hierarchy_cycles_remain_accessible_and_scoped(setup):
    from app.lib.campaigns import material_hierarchy
    app, client = setup
    first, first_graph = create_map(client, nodes=1)
    second, second_graph = create_map(client, nodes=1)
    with app.app_context():
        a, b = db.session.get(PointcrawlMap, first), db.session.get(PointcrawlMap, second)
        a.nodes[0].nested_map = b
        b.nodes[0].nested_map = a
        # Old/externally written geometry can contain cycles. Do not lose all roots.
        db.session.commit()
        entries = ContentEntry.query.filter_by(owner_id=1, campaign_id=1).all()
        tree = material_hierarchy(entries)
        def flattened(items):
            return [entry_id for item in items for entry_id in [item['entry'].id, *flattened(item['children'])]]
        ids = flattened(tree)
        assert set(ids) == {entry.id for entry in entries}
        assert len(ids) <= len(entries) + 1
        # A scope missing a linked map must never pull its private original in.
        scoped = material_hierarchy([a.entry, a.nodes[0].entry])
        assert set(flattened(scoped)) == {a.entry_id, a.nodes[0].entry_id}
    assert client.get('/campaigns/1/').status_code == 200


@pytest.mark.parametrize('kind', ['dungeon', 'forest'])
def test_generated_nested_map_is_atomic_private_and_not_duplicated(setup, kind):
    app, client = setup
    map_id, graph = create_map(client)
    root_id = map_entry_id(app, map_id)
    graph['nodes'][0]['nested_draft'] = nested_draft(kind)
    response = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    assert response.status_code == 200, response.get_data(as_text=True)
    saved = response.json
    nested_id = saved['nodes'][0]['nested_map_id']
    child = client.get(f'/maps/{nested_id}/data').json
    assert child['kind'] == kind
    assert child['title'] == graph['nodes'][0]['title']
    assert len(child['nodes']) == 2
    assert child['edges'][0]['path_type'] == 'hidden'
    assert child['body'] == graph['nodes'][0]['body'] + '\n\nGENERATED PRIVATE INTERIOR'
    assert map_entry_id(app, nested_id) == saved['nodes'][0]['entry_id']
    child_entry_id = map_entry_id(app, nested_id)
    with app.app_context():
        assert db.session.get(ContentEntry, child_entry_id).campaign_id == 1
        assert PointcrawlMap.query.count() == 2
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(saved)}).status_code == 200
    with app.app_context():
        assert PointcrawlMap.query.count() == 2
    html = client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    assert re.search(fr'value="{child_entry_id}"\s+checked\s+disabled', html)
    assert reveal(client, root_id, title='Region').status_code == 302
    assert reveal(client, saved['nodes'][0]['entry_id'], title='Known dungeon').status_code == 302
    public = client.get('/party/1/materials/data').json['entries']
    root = next(item for item in public if item['id'] == root_id)
    assert root['links'] == [{'id': saved['nodes'][0]['entry_id'], 'title': 'Known dungeon'}]
    assert client.get(f'/party/1/maps/{nested_id}/data').json['nodes'] == []
    assert reveal(client, child_entry_id, version=1, title='Known interior').status_code == 302
    public = client.get('/party/1/materials/data').json['entries']
    root = next(item for item in public if item['id'] == root_id)
    assert {'id': child_entry_id, 'title': 'Known interior'} in root['links']
    assert client.get(f'/party/1/maps/{nested_id}/data').json['nodes'] == []


def test_automatic_map_relations_include_existing_locations_and_follow_removal(setup):
    app, client = setup
    map_id, graph = create_map(client)
    root_id = map_entry_id(app, map_id)
    location_id = graph['nodes'][0]['entry_id']
    html = client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    assert re.search(fr'value="{location_id}"\s+checked\s+disabled', html)
    graph['nodes'] = graph['nodes'][1:]
    graph['edges'] = []
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    html = client.get(f'/materials/{root_id}/edit').get_data(as_text=True)
    assert not re.search(fr'value="{location_id}"\s+checked', html)
    assert client.get(f'/materials/{location_id}/edit').status_code == 200


@pytest.mark.parametrize('mutation', ['bad_kind', 'bad_child', 'recursive', 'existing_link'])
def test_invalid_nested_draft_rolls_back_all_new_materials(setup, mutation):
    app, client = setup
    map_id, graph = create_map(client)
    original = json.loads(json.dumps(graph))
    draft = nested_draft()
    graph['nodes'][0]['nested_draft'] = draft
    if mutation == 'bad_kind': draft['kind'] = 'realm'
    elif mutation == 'bad_child': draft['edges'][0]['target'] = 'missing'
    elif mutation == 'recursive': draft['nodes'][0]['nested_draft'] = nested_draft()
    else: graph['nodes'][0]['nested_map_id'] = map_id
    with app.app_context():
        before = ContentEntry.query.count()
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 400
    assert client.get(f'/maps/{map_id}/data').json == original
    with app.app_context():
        assert PointcrawlMap.query.count() == 1
        assert ContentEntry.query.count() == before


def test_region_and_nested_maps_use_submitted_campaign_over_url_default(setup):
    app, client = setup
    draft = {'nodes': [{'id': 'new-forest', 'number': 1, 'x': 0, 'y': 0,
                       'title': 'Forest', 'nested_draft': nested_draft('forest')}], 'edges': []}
    response = client.post('/maps/new?campaign_id=1', data={'campaign_id': '',
        'title': 'Unfiled region', 'kind': 'realm', 'draft': json.dumps(draft)})
    assert response.status_code == 302
    with app.app_context():
        assert PointcrawlMap.query.count() == 2
        assert all(entry.campaign_id is None for entry in ContentEntry.query.all())


def test_delete_campaign_removes_nested_maps_but_keeps_external_materials_and_parties(setup, monkeypatch):
    app, client = setup
    map_id, graph = create_map(client)
    graph['drawing'] = drawing()
    graph['nodes'][0]['nested_draft'] = nested_draft()
    response = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    assert response.status_code == 200
    nested_id = response.json['nodes'][0]['nested_map_id']
    root_id = map_entry_id(app, map_id)
    child_id = map_entry_id(app, nested_id)
    standalone_id = create_entry(client, campaign_id='', title='Keep unfiled')
    with app.app_context():
        db.session.add(Campaign(id=2, owner_id=1, name='Keep campaign'))
        db.session.commit()
    other_id, other_graph = create_map(client, campaign_id=2, title='Keep map')
    other_entry_id = map_entry_id(app, other_id)
    with app.app_context():
        doomed_ids = [entry.id for entry in ContentEntry.query.filter_by(campaign_id=1)]
        for entry_id in doomed_ids:
            entry = db.session.get(ContentEntry, entry_id)
            entry.presentations.append(PartyPresentation(party_id=1, title='Known', body='Known body'))
        db.session.add_all([ContentLink(source_id=standalone_id, target_id=root_id),
                            ContentLink(source_id=root_id, target_id=other_entry_id),
                            ContentLink(source_id=standalone_id, target_id=other_entry_id)])
        db.session.commit()
    from app import socketio
    notifications = []
    monkeypatch.setattr(socketio, 'emit', lambda event, payload, **kw: notifications.append((event, payload, kw)))
    preview = client.post('/campaigns/1/delete', data={'version': 1})
    assert preview.status_code == 200
    assert 'Delete campaign?' in preview.get_data(as_text=True)
    assert 'Cancel' in preview.get_data(as_text=True)
    assert client.get(f'/maps/{map_id}/data').status_code == 200
    assert client.post('/campaigns/1/delete', data={'version': 1, 'confirm': 'delete'}).status_code == 302
    with app.app_context():
        assert db.session.get(Campaign, 1) is None
        assert db.session.get(Campaign, 2) is not None
        assert ContentEntry.query.filter(ContentEntry.id.in_(doomed_ids)).count() == 0
        assert PartyPresentation.query.filter(PartyPresentation.entry_id.in_(doomed_ids)).count() == 0
        assert CampaignParty.query.filter_by(campaign_id=1).count() == 0
        assert PointcrawlMap.query.count() == 1
        assert MapNode.query.count() == len(other_graph['nodes'])
        assert MapEdge.query.count() == len(other_graph['edges'])
        assert db.session.get(ContentEntry, standalone_id) is not None
        assert db.session.get(ContentEntry, other_entry_id) is not None
        assert [(link.source_id, link.target_id) for link in ContentLink.query.all()] == [(standalone_id, other_entry_id)]
        assert Party.query.count() == 3
        assert Character.query.count() == 2
    assert {payload['party_id'] for event, payload, kw in notifications} == {1, 2}
    assert all(event == 'campaign_content_changed' for event, payload, kw in notifications)
    assert client.get(f'/maps/{map_id}/data').status_code == 404
    assert client.get(f'/maps/{nested_id}/data').status_code == 404
    assert client.get(f'/materials/{child_id}/edit').status_code == 404
    login(client, 2)
    assert client.get('/party/1/materials/data').json['entries'] == []


def test_delete_campaign_checks_owner_and_version_before_removing_contents(setup):
    app, client = setup
    map_id, graph = create_map(client)
    login(client, 2)
    assert client.post('/campaigns/1/delete', data={'version': 1}).status_code == 403
    login(client, 1)
    assert client.post('/campaigns/1/delete', data={'version': 0, 'confirm': 'delete'}).status_code == 409
    assert client.get(f'/maps/{map_id}/data').json == graph
    assert client.get('/campaigns/1/').status_code == 200


def test_rich_descriptions_preserve_formatting_and_independent_publication(setup):
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    rich = RICH_PREFIX + '<h2>Clues</h2><p><strong>Secret</strong> <em>history</em></p><ul><li>Door</li></ul>'
    entry_id = create_entry(client, body=rich)
    with app.app_context():
        assert db.session.get(ContentEntry, entry_id).body == rich
    public = RICH_PREFIX + '<p><strong>Known clue</strong></p>'
    assert reveal(client, entry_id, body=public).status_code == 302
    assert client.post(f'/materials/{entry_id}/edit', data={'version': 1, 'title': 'Private',
        'body': RICH_PREFIX + '<p>Changed secret</p>', 'category': 'npc', 'campaign_id': 1}).status_code == 302
    login(client, 2)
    page = client.get(f'/party/1/materials/{entry_id}').get_data(as_text=True)
    assert '<strong>Known clue</strong>' in page
    assert 'Changed secret' not in page
    assert '<!--kw-rich-text' not in page


def test_rich_images_are_stored_and_published_with_the_description(setup):
    import base64
    import io
    from PIL import Image
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    buffer = io.BytesIO()
    Image.new('RGB', (4, 4), 'red').save(buffer, format='PNG')
    src = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
    body = RICH_PREFIX + f'<p>Map legend</p><p><img src="{src}" alt="Red token"></p>'
    entry_id = create_entry(client, body=body)
    assert client.get('/party/1/materials/data').json['entries'] == []
    with app.app_context():
        stored = db.session.get(ContentEntry, entry_id).body
    assert reveal(client, entry_id, body=stored).status_code == 302
    page = client.get(f'/party/1/materials/{entry_id}').get_data(as_text=True)
    optimized = re.search(r'src="([^"]+)"', stored).group(1)
    assert optimized.startswith('/material-images/1/')
    assert 'data:image/' not in stored
    assert client.get(optimized).mimetype == 'image/webp'
    assert f'src="{optimized}"' in page
    assert 'alt="Red token"' in page
    invalid = RICH_PREFIX + '<p><img src="data:image/png;base64,bm90YW5pbWFnZQ=="></p>'
    assert client.post(f'/materials/{entry_id}/edit', data={'version': 1, 'title': 'Bad',
        'body': invalid, 'category': 'npc', 'campaign_id': 1}).status_code == 400
    with app.app_context():
        assert db.session.get(ContentEntry, entry_id).body == stored


def test_rich_html_sanitization_and_literal_legacy_text(setup):
    from app.lib.rich_content import RICH_PREFIX, content_excerpt
    app, client = setup
    malicious = RICH_PREFIX + '<p style="position:fixed" onclick="evil()"><strong>Safe</strong><script>evil()</script><a href="javascript:evil()">bad</a></p>'
    entry_id = create_entry(client, body=malicious)
    with app.app_context():
        body = db.session.get(ContentEntry, entry_id).body
        assert '<strong>Safe</strong>' in body
        assert 'onclick' not in body and 'style=' not in body and '<script' not in body
        assert 'javascript:' not in body
    assert '<strong>literal</strong><br>' in str(render_content('<strong>literal</strong>\nnext'))
    assert content_excerpt(RICH_PREFIX + '<p>First</p><p><strong>Second</strong></p>', 8) == 'First Se'
    unsafe_image = RICH_PREFIX + '<img src="javascript:alert(1)">'
    assert client.post('/materials/new', data={'title': 'Bad image', 'category': 'note', 'body': unsafe_image}).status_code == 400


def test_rich_map_notes_locations_and_paths_roundtrip(setup):
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    rich = RICH_PREFIX + '<p><em>Formatted description</em></p>'
    draft = nested_draft()
    draft['nodes'][0]['body'] = rich
    draft['edges'][0]['body'] = rich
    response = client.post('/maps/new', data={'campaign_id': 1, 'kind': 'dungeon',
        'title': 'Rich map', 'body': rich, 'draft': json.dumps(draft)})
    assert response.status_code == 302
    map_id = graph_from_article(client,response.location)['id']
    graph = client.get(f'/maps/{map_id}/data').json
    assert graph['body'] == rich
    assert graph['nodes'][0]['body'] == rich
    assert graph['edges'][0]['body'] == rich


@pytest.mark.parametrize('rich', [False, True])
def test_description_text_limit_is_independent_of_image_budget(setup, rich):
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    body = 'x' * 50001
    if rich:
        body = RICH_PREFIX + '<p>' + body + '</p>'
    assert client.post('/materials/new', data={'title': 'Too long', 'category': 'note', 'body': body}).status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 0


def test_remote_description_images_roundtrip_without_embedding(setup):
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    body = RICH_PREFIX + '<p><img src="https://example.com/image?id=1&amp;size=large" alt="Map"></p>'
    entry_id = create_entry(client, body=body)
    with app.app_context():
        assert db.session.get(ContentEntry, entry_id).body == body
    assert reveal(client, entry_id, body=body).status_code == 302
    page = client.get(f'/party/1/materials/{entry_id}').get_data(as_text=True)
    assert 'src="https://example.com/image?id=1&amp;size=large"' in page


@pytest.mark.parametrize('url', ['javascript:alert(1)', '//example.com/a.png', 'file:///tmp/a.png',
    'data:image/svg+xml;base64,PHN2Zz4=', 'https://user:pass@example.com/a.png', 'https://',
    'https://example.com/white space.png'])
def test_description_rejects_unsafe_image_urls(setup, url):
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    response = client.post('/materials/new', data={'title': 'Bad URL', 'category': 'note',
        'body': RICH_PREFIX + f'<img src="{url}">'})
    assert response.status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 0


def test_uploaded_description_images_are_resized_stripped_and_stable(setup):
    import base64
    import io
    from PIL import Image
    from app.lib.rich_content import RICH_PREFIX, optimize_image
    app, client = setup
    original = Image.new('RGB', (2400, 1200), 'orange')
    exif = Image.Exif()
    exif[274] = 6  # Rotate to portrait before resizing.
    exif[270] = 'Private camera metadata'
    buffer = io.BytesIO()
    original.save(buffer, format='JPEG', exif=exif)
    body = RICH_PREFIX + '<img src="data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode() + '">'
    entry_id = create_entry(client, body=body)
    with app.app_context():
        stored = db.session.get(ContentEntry, entry_id).body
    image_url = re.search(r'src="([^"]+)"', stored).group(1)
    data = client.get(image_url).data
    encoded = 'data:image/webp;base64,' + base64.b64encode(data).decode()
    assert optimize_image(encoded) == encoded  # No repeated lossy encoding.
    assert len(data) < len(buffer.getvalue())
    assert len(data) <= 500 * 1024
    with Image.open(io.BytesIO(data)) as result:
        assert result.format == 'WEBP'
        assert result.size == (800, 1600)
        assert not result.getexif()
        assert not result.info.get('xmp')


def test_description_image_transparency_and_animation_policy(setup):
    import base64
    import io
    from PIL import Image
    from app.lib.rich_content import optimize_image
    app, _ = setup
    for format in ('PNG', 'GIF'):
        buffer = io.BytesIO()
        image = Image.new('RGBA', (20, 20), (255, 0, 0, 0))
        image.putpixel((10, 10), (255, 0, 0, 255))
        kwargs = {'save_all': True, 'append_images': [Image.new('RGBA', (20, 20), 'blue')]} if format == 'GIF' else {}
        image.save(buffer, format=format, **kwargs)
        with app.app_context():
            url = optimize_image(f'data:image/{format.lower()};base64,' + base64.b64encode(buffer.getvalue()).decode())
        with Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))) as result:
            assert not getattr(result, 'is_animated', False)
            assert result.convert('RGBA').getpixel((0, 0))[3] == 0
            assert result.convert('RGBA').getpixel((10, 10))[3] == 255


def test_description_high_detail_image_stays_within_storage_budget(setup):
    import base64
    import io
    from PIL import Image
    from app.lib.rich_content import optimize_image
    app, _ = setup
    buffer = io.BytesIO()
    Image.effect_noise((1600, 1600), 100).convert('RGB').save(buffer, format='JPEG', quality=75)
    assert 500 * 1024 < buffer.tell() <= 2 * 1024 * 1024
    with app.app_context():
        url = optimize_image('data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode())
    assert len(base64.b64decode(url.split(',', 1)[1])) <= 500 * 1024


def description_image(client):
    import base64
    import io
    from PIL import Image
    from app.lib.rich_content import RICH_PREFIX
    buffer = io.BytesIO()
    Image.new('RGB', (20, 20), 'red').save(buffer, format='PNG')
    return RICH_PREFIX + '<img src="data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode() + '">'


def test_material_files_keep_publication_access_and_references(setup):
    from pathlib import Path
    app, client = setup
    entry_id = create_entry(client, body=description_image(client))
    with app.app_context():
        stored = db.session.get(ContentEntry, entry_id).body
    url = re.search(r'src="([^"]+)"', stored).group(1)
    assert client.get(url).status_code == 200
    assert client.get(url).headers['Cache-Control'] == 'private, no-store'
    assert len(list(Path(app.config['MATERIAL_IMAGE_UPLOAD_FOLDER']).rglob('*.webp'))) == 1
    login(client, 2)
    assert client.get(url).status_code == 404
    assert client.post('/materials/new', data={'category': 'note', 'title': 'Stolen', 'body': stored}).status_code == 400
    login(client, 1)
    assert reveal(client, entry_id, body=stored).status_code == 302
    login(client, 2)
    assert client.get(url).status_code == 200
    login(client, 3)  # A different party cannot see the image.
    assert client.get(url).status_code == 404
    login(client, 1)
    assert client.post(f'/materials/{entry_id}/edit', data={'version': 1, 'title': 'Changed',
        'body': '', 'category': 'npc', 'campaign_id': 1}).status_code == 302
    login(client, 2)
    assert client.get(url).status_code == 200  # Published copy retains its file.
    login(client, 1)
    assert client.post(f'/materials/{entry_id}/revoke/1', data={'version': 1}).status_code == 302
    login(client, 2)
    assert client.get(url).status_code == 404
    login(client, 1)
    assert client.get(url).status_code == 200  # Warden can still edit the revoked draft.
    assert client.post('/campaigns/1/delete', data={'version': 1, 'confirm': 'delete'}).status_code == 302
    assert client.get(url).status_code == 404
    assert not list(Path(app.config['MATERIAL_IMAGE_UPLOAD_FOLDER']).rglob('*.webp'))


def test_material_image_files_are_removed_when_flushed_request_rolls_back(setup):
    from pathlib import Path
    app, client = setup
    # New map flushes its root before validating the rest of the graph.
    response = client.post('/maps/new', data={'campaign_id': 1, 'title': 'Invalid map',
        'kind': 'dungeon', 'body': description_image(client), 'draft': '{invalid json'})
    assert response.status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 0
    assert not list(Path(app.config['MATERIAL_IMAGE_UPLOAD_FOLDER']).rglob('*.webp'))


def test_existing_embedded_descriptions_can_be_migrated_to_files(setup):
    from sqlalchemy import update
    from app.lib.rich_content import RICH_PREFIX
    app, client = setup
    entry_id = create_entry(client)
    legacy = description_image(client)
    with app.app_context():
        # Bypass the ORM hook to simulate data written before filesystem storage.
        db.session.execute(update(ContentEntry).where(ContentEntry.id == entry_id).values(body=legacy))
        db.session.commit()
    result = app.test_cli_runner().invoke(args=['campaigns', 'migrate-images'])
    assert result.exit_code == 0, result.output
    assert 'Migrated 1 descriptions' in result.output
    with app.app_context():
        body = db.session.get(ContentEntry, entry_id).body
    assert body.startswith(RICH_PREFIX)
    assert 'data:image/' not in body
    assert client.get(re.search(r'src="([^"]+)"', body).group(1)).status_code == 200
    repeat = app.test_cli_runner().invoke(args=['campaigns', 'migrate-images'])
    assert repeat.exit_code == 0
    assert 'Migrated 0 descriptions' in repeat.output


def deletion_preview(client, entry_ids, campaign_id=1, versions=None):
    versions = versions or {}
    response = client.post('/materials/bulk-delete', data={
        'campaign_id': campaign_id, 'entry_ids': [str(entry_id) for entry_id in entry_ids],
        **{f'version_{entry_id}': versions.get(entry_id, 1) for entry_id in entry_ids}})
    assert response.status_code == 200, response.get_data(as_text=True)
    html = response.get_data(as_text=True)
    return re.search(r'name="deletion_token" value="([^"]+)"', html)[1], {
        int(value) for value in re.findall(r'data-delete-entry-id="(\d+)"', html)}


@pytest.mark.parametrize('kind', ['dungeon', 'forest'])
def test_delete_map_removes_nested_contents_and_publications(setup, kind):
    app, client = setup
    map_id, graph = create_map(client)
    graph['nodes'][0]['nested_draft'] = nested_draft(kind)
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    root_id = map_entry_id(app, map_id)
    keep_id = create_entry(client, title='Keep unrelated')
    with app.app_context():
        doomed = [entry.id for entry in ContentEntry.query.filter(ContentEntry.id != keep_id)]
        for entry_id in doomed:
            db.session.add(PartyPresentation(entry=db.session.get(ContentEntry, entry_id), party_id=1, title='Known', body=''))
        db.session.commit()
    assert client.post(f'/materials/{root_id}/delete', data={'version': 1}).status_code == 302
    with app.app_context():
        assert [e.id for e in ContentEntry.query.all()] == [keep_id]
        assert PointcrawlMap.query.count() == MapNode.query.count() == MapEdge.query.count() == 0
        assert PartyPresentation.query.count() == 0
        assert Campaign.query.count() == 1
        assert Party.query.count() == 3
        assert Character.query.count() == 2


def test_bulk_delete_preview_then_atomic_scoped_delete(setup, monkeypatch):
    from app import socketio
    from app.models import PartyMap
    app, client = setup
    first = create_entry(client, campaign_id='', title='Trap')
    second = create_entry(client, campaign_id='', title='Lore')
    keep = create_entry(client, title='Campaign material')
    reveal(client, first)
    with app.app_context():
        db.session.add(PartyMap(party_id=1, drawing=drawing()))
        db.session.add(ContentLink(source_id=keep, target_id=first))
        db.session.commit()
    notifications = []
    monkeypatch.setattr(socketio, 'emit', lambda event, payload, **kw: notifications.append(payload))
    token, listed = deletion_preview(client, [first, second], campaign_id='')
    assert listed == {first, second}
    with app.app_context():
        assert ContentEntry.query.count() == 3  # Preview is read-only.
    response = client.post('/materials/bulk-delete', data={'deletion_token': token})
    assert response.status_code == 302 and response.location.endswith('/materials/')
    with app.app_context():
        assert [entry.id for entry in ContentEntry.query.all()] == [keep]
        assert PartyPresentation.query.count() == ContentLink.query.count() == 0
        assert db.session.get(PartyMap, 1).drawing == drawing()
        assert Campaign.query.count() == 1 and Party.query.count() == 3
    assert notifications and {payload['party_id'] for payload in notifications} == {1}


def test_bulk_delete_map_preview_includes_all_descendants_and_paths(setup):
    app, client = setup
    map_id, graph = create_map(client)
    graph['nodes'][0]['nested_draft'] = nested_draft('forest')
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    root_id = map_entry_id(app, map_id)
    token, listed = deletion_preview(client, [root_id, graph['nodes'][0]['entry_id']],
        versions={graph['nodes'][0]['entry_id']: 2})
    with app.app_context():
        assert listed == {entry.id for entry in ContentEntry.query.all()}
    assert client.post('/materials/bulk-delete', data={'deletion_token': token}).status_code == 302
    with app.app_context():
        assert ContentEntry.query.count() == PointcrawlMap.query.count() == 0


@pytest.mark.parametrize('change', ['material', 'geometry', 'descendant', 'tampered', 'owner'])
def test_bulk_delete_rejects_changed_preview_without_partial_deletion(setup, change):
    app, client = setup
    map_id, graph = create_map(client)
    root_id = map_entry_id(app, map_id)
    token, _ = deletion_preview(client, [root_id])
    if change in ('material', 'descendant'):
        with app.app_context():
            entry_id = root_id if change == 'material' else graph['nodes'][0]['entry_id']
            db.session.get(ContentEntry, entry_id).title = 'Changed since preview'
            db.session.commit()
    elif change == 'geometry':
        graph['nodes'].append({'id': 'new-after-preview', 'number': 3, 'x': 10, 'y': 20, 'title': 'New room'})
        assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).status_code == 200
    elif change == 'tampered':
        token = 'changed' + token
    else:
        login(client, 2)
    result = client.post('/materials/bulk-delete', data={'deletion_token': token})
    assert result.status_code == (403 if change == 'owner' else 409)
    with app.app_context():
        assert db.session.get(ContentEntry, root_id) is not None
        assert db.session.get(ContentEntry, graph['nodes'][0]['entry_id']) is not None
        assert PointcrawlMap.query.count() == 1


def test_bulk_delete_validates_selection_scope_versions_and_csrf(setup):
    app, client = setup
    entry_id = create_entry(client)
    unfiled = create_entry(client, campaign_id='')
    data = {'entry_ids': [entry_id, unfiled], f'version_{entry_id}': 1, f'version_{unfiled}': 1}
    assert client.post('/materials/bulk-delete', data=data).status_code == 409
    assert client.post('/materials/bulk-delete', data={'campaign_id': 1}).status_code == 400
    data = {'campaign_id': 1, 'entry_ids': [entry_id], f'version_{entry_id}': 0}
    assert client.post('/materials/bulk-delete', data=data).status_code == 409
    login(client, 2)
    data[f'version_{entry_id}'] = 1
    assert client.post('/materials/bulk-delete', data=data).status_code == 403
    login(client, 1)
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/materials/bulk-delete', data=data).status_code == 400
    with app.app_context():
        assert ContentEntry.query.count() == 2


def test_deleting_article_with_map_removes_entrance_and_invalidates_parent_editor(setup):
    app, client = setup
    parent_id, graph = create_map(client)
    graph['nodes'][0]['nested_draft'] = nested_draft()
    saved = client.post(f'/maps/{parent_id}/data', data={'graph': json.dumps(graph)}).json
    nested_id = saved['nodes'][0]['nested_map_id']
    root_id = map_entry_id(app, nested_id)
    token, _ = deletion_preview(client, [root_id], versions={root_id: saved['nodes'][0]['entry_version']})
    assert client.post('/materials/bulk-delete', data={'deletion_token': token}).status_code == 302
    parent = client.get(f'/maps/{parent_id}/data').json
    assert [node['entry_id'] for node in parent['nodes']] == [saved['nodes'][1]['entry_id']]
    assert parent['edges'] == []
    assert parent['nodes'][0]['nested_map_id'] is None
    assert parent['version'] > saved['version']
    assert client.post(f'/maps/{parent_id}/data', data={'graph': json.dumps(saved)}).status_code == 409
    with app.app_context():
        assert PointcrawlMap.query.count() == 1
        assert ContentEntry.query.count() == 2


def test_bulk_delete_handles_cycles_without_following_arbitrary_links(setup):
    app, client = setup
    first, _ = create_map(client, nodes=1)
    second, _ = create_map(client, nodes=1)
    keep = create_entry(client)
    with app.app_context():
        a, b = db.session.get(PointcrawlMap, first), db.session.get(PointcrawlMap, second)
        a.nodes[0].nested_map = b
        b.nodes[0].nested_map = a
        root_id = a.entry_id
        db.session.add(ContentLink(source_id=root_id, target_id=keep))
        db.session.commit()
    token, listed = deletion_preview(client, [root_id])
    assert len(listed) == 4 and keep not in listed
    assert client.post('/materials/bulk-delete', data={'deletion_token': token}).status_code == 302
    with app.app_context():
        assert [entry.id for entry in ContentEntry.query.all()] == [keep]
        assert PointcrawlMap.query.count() == MapNode.query.count() == 0


def test_bulk_delete_location_cleans_connected_paths_and_updates_surviving_map(setup):
    app, client = setup
    map_id, graph = create_map(client)
    location_id = graph['nodes'][0]['entry_id']
    token, listed = deletion_preview(client, [location_id])
    assert listed == {location_id, graph['edges'][0]['entry_id']}
    assert client.post('/materials/bulk-delete', data={'deletion_token': token}).status_code == 302
    saved = client.get(f'/maps/{map_id}/data').json
    assert len(saved['nodes']) == 1 and saved['edges'] == []
    assert saved['version'] > graph['version']
    with app.app_context():
        assert ContentEntry.query.count() == 2


def test_markdown_article_publication_preserves_source_and_safe_rendering(setup):
    app, client = setup
    body = '## A clue\n\n**Bold** and *italic*, ~~gone~~, `code`.\n\n- One\n- Two\n\n> Whisper\n\n| A | B |\n| - | - |\n| 1 | 2 |'
    entry_id = create_entry(client, body=body)
    with app.app_context():
        assert db.session.get(ContentEntry, entry_id).body == body
    assert reveal(client, entry_id, body=body).status_code == 302
    login(client, 2)
    page = client.get(f'/party/1/materials/{entry_id}').text
    for tag in ('<h2 id="kw-h-a-clue">A clue</h2>', '<strong>Bold</strong>', '<em>italic</em>', '<del>gone</del>', '<code>code</code>', '<ul>', '<blockquote>', '<table>'):
        assert tag in page


def test_markdown_images_use_existing_private_storage_and_access_checks(setup):
    app, client = setup
    body = 'A token\n\n![Token](' + re.search(r'src="([^"]+)"', description_image(client))[1] + ')'
    entry_id = create_entry(client, body=body)
    with app.app_context():
        saved = db.session.get(ContentEntry, entry_id).body
    assert saved.startswith('A token\n\n![Token](/material-images/1/')
    assert 'data:image/' not in saved
    url = re.search(r'\]\(([^)]+)\)', saved)[1]
    assert client.get(url).status_code == 200
    login(client, 2)
    assert client.get(url).status_code == 404


@pytest.mark.parametrize('category', ['bestiary', 'item', 'spellbook', 'culture', 'custom'])
def test_new_article_categories_can_be_created_unfiled(setup, category):
    app, client = setup
    response = client.post('/materials/new', data={'category': category,
        'title': '**Known** article', 'body': 'A *public* description'})
    assert response.status_code == 302
    with app.app_context():
        entry = ContentEntry.query.one()
        assert entry.campaign_id is None and entry.category == category
        assert entry.body == 'A *public* description' and not entry.presentations


def test_map_inline_card_edits_are_private_and_version_checked(setup):
    app, client = setup
    map_id, graph = create_map(client)
    edge = graph['edges'][0]
    assert reveal(client, edge['entry_id'], body='Public path').status_code == 302
    edge.update(content_changed=True, title='Secret tunnel', body='**Locked** gate', path_type='hidden')
    response = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    assert response.status_code == 200
    saved = response.json
    assert saved['edges'][0]['body'] == '**Locked** gate'
    assert saved['edges'][0]['path_type'] == 'hidden'
    with app.app_context():
        assert PartyPresentation.query.filter_by(entry_id=edge['entry_id']).one().body == 'Public path'
    saved['edges'][0].update(content_changed=True, entry_version=edge['entry_version'], body='Stale')
    assert client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(saved)}).status_code == 409
    assert client.get(f'/maps/{map_id}/data').json['edges'][0]['body'] == '**Locked** gate'


def test_party_tree_uses_published_fields_and_promotes_children_of_hidden_parents(setup):
    app, client = setup
    parent = create_entry(client)
    child = create_entry(client)
    hidden = create_entry(client)
    orphan = create_entry(client)
    with app.app_context():
        db.session.get(ContentEntry, child).parent_id = parent
        db.session.get(ContentEntry, orphan).parent_id = hidden
        db.session.commit()
    for entry_id, title in [(parent, 'Published parent'), (child, 'Published child'),
                            (orphan, 'Published orphan')]:
        assert reveal(client, entry_id, title=title).status_code == 302
    login(client, 2)
    html = client.get('/party/1/materials/').get_data(as_text=True)
    assert f'data-tree-key="entry-{parent}"' in html
    assert 'Published parent' in html and 'Published child' in html and 'Published orphan' in html
    assert 'SECRET NAME' not in html and 'SECRET BODY' not in html
    assert f'/party/1/materials/{hidden}' not in html
    assert 'campaign-card' not in html
    assert 'x-data="materialTree"' in html
    assert client.get(f'/party/1/materials/{child}/preview').status_code == 200
    assert client.get(f'/party/1/materials/{hidden}/preview').status_code == 404


def renderable_party_page(app):
    """The party page renders character sheets, which need these columns."""
    with app.app_context():
        for character in Character.query.all():
            character.owner_username = f'user{character.owner}'
            character.url_name = f'player{character.id}'
            character.items = '[]'
            character.containers = '[{"id":0,"name":"Main","slots":10}]'
        db.session.commit()


def test_party_campaign_tab_uses_published_knowledge(setup):
    app, client = setup
    renderable_party_page(app)
    entry_id = create_entry(client)
    assert reveal(client, entry_id).status_code == 302
    url = '/users/user1/parties/party1/'
    page = client.get(url)
    assert page.status_code == 200
    assert 'id="campaign-details-tab"' in page.text
    assert 'Known name' in page.text and 'Known facts' not in page.text  # Cards: title only.
    assert 'SECRET NAME' not in page.text and 'SECRET BODY' not in page.text
    assert 'Add party note' in page.text and 'Open party wiki' in page.text and 'href="/party/1/wiki/"' in page.text
    # The Warden's connected campaign, as a gallery card with how much of it this party has seen.
    assert 'party-linked-campaigns' in page.text and 'href="/campaigns/1/wiki/"' in page.text
    card = page.text.split('party-linked-campaigns')[1].split('</section>')[0]
    assert 'campaign-card-actions' not in card and '/campaigns/1/"' not in card  # Card opens to read; no Read/Edit.
    assert '1 of 1 articles revealed' in page.text
    assert '>Wiki</button>' in page.text
    assert 'View as party' not in page.text and 'preview=1' not in page.text
    assert f'/party/1/materials/{entry_id}/version' in page.text and f'/materials/{entry_id}/edit' not in page.text
    assert 'To reveal an article, open it in Campaigns and choose Reveal to party.' in page.text
    assert 'Quick notes for this party only' in page.text
    assert 'data-content-url="/party/1/materials/"' in page.text

    login(client, 2)
    player = client.get(url)
    assert 'Known name' in player.text and 'Open party wiki' in player.text
    assert 'Add party note' not in player.text and 'party-linked-campaigns' not in player.text
    assert f'/party/1/materials/{entry_id}/version' not in player.text

    login(client, 3)
    outsider = client.get(url)
    assert 'id="campaign-details-tab"' not in outsider.text
    assert 'Known name' not in outsider.text

    login(client, 1)
    app.config['FEATURE_TEST_PARTY_IDS'] = set()
    released = client.get(url)
    assert 'id="campaign-details-tab"' in released.text
    assert 'Known name' in released.text


def test_no_connection_step_audience_comes_from_reveals(setup):
    """Any of my parties can be shown any article; who has seen a campaign is worked out from reveals."""
    app, client = setup
    renderable_party_page(app)
    with app.app_context():
        CampaignParty.query.delete()  # Old connections no longer matter.
        db.session.commit()
    gallery = client.get('/campaigns/').text
    assert 'Not revealed to any party yet' in gallery and '/campaigns/1/parties' not in gallery and 'campaign-card-parties' not in gallery
    party_page = client.get('/users/user1/parties/party1/').text
    assert 'Nothing from your campaigns has been revealed to this party yet.' in party_page

    entry_id = create_entry(client)
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').text  # Every party I run, no group yet.
    assert 'value="1"' in page and 'value="2"' in page and 'Already seeing this campaign' not in page
    assert reveal(client, entry_id).status_code == 302  # No "connect first" rejection.

    assert 'Revealed to Party 1' in client.get('/campaigns/').text
    home = client.get('/campaigns/1/wiki/').text
    assert 'action="/campaigns/1/hide/1"' in home and 'Hide everything' in home and '1 articles' in home
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').text
    assert page.index('Already seeing this campaign') < page.index('Other parties')
    party_page = client.get('/users/user1/parties/party1/').text
    assert 'party-linked-campaigns' in party_page and '1 of 1 articles revealed' in party_page
    assert 'Revealed to' in client.get('/campaigns/1/').text and 'name="party_ids"' not in client.get('/campaigns/1/').text


def test_party_notes_live_only_on_their_party(setup):
    app, client = setup
    renderable_party_page(app)
    url = '/users/user1/parties/party1/'
    assert client.post('/party/1/notes', data={'title': ' '}).status_code == 400
    added = client.post('/party/1/notes', data={'title': 'Told at the table', 'body': 'The ferryman lies'})
    assert added.location == url + '#campaign-details'
    with app.app_context():
        note = ContentEntry.query.filter_by(title='Told at the table').one()
        note_id, version = note.id, note.version
        assert (note.category, note.campaign_id, note.body) == ('party_note', None, 'The ferryman lies')
        assert [(p.party_id, p.title, p.body, p.published) for p in note.presentations] == [
            (1, 'Told at the table', 'The ferryman lies', True)]

    # On the party: listed under Party notes, readable in the party wiki, editable by the Warden.
    page = client.get(url).text
    assert 'Told at the table' in page and 'The ferryman lies' not in page  # Cards show the title only.
    assert f'/party/1/notes/{note_id}/edit' in page and f'/party/1/notes/{note_id}/delete' in page
    wiki = client.get(f'/party/1/materials/{note_id}').text
    assert 'Party note' in wiki and f'href="/party/1/notes/{note_id}/edit"' in wiki and 'Private original' not in wiki
    assert 'Told at the table' in client.get('/party/1/wiki/').text

    # Never in Campaigns: no list, wiki, link picker or editor shows it.
    for path in ('/campaigns/', '/materials/', '/materials/wiki/', '/materials/reference-catalog'):
        assert 'Told at the table' not in client.get(path).text, path
    for path in (f'/materials/{note_id}/edit', f'/materials/wiki/{note_id}/', f'/materials/{note_id}/reveal'):
        assert client.get(path).status_code == 404, path
    assert client.post(f'/materials/{note_id}/move', data={'campaign_id': 1, 'version': version}).status_code == 404

    assert client.get(f'/party/1/notes/{note_id}/edit').status_code == 200
    assert client.post(f'/party/1/notes/{note_id}/edit', data={'title': 'T', 'version': version + 3}).status_code == 409
    assert client.post(f'/party/1/notes/{note_id}/edit',
                       data={'title': 'Ferryman', 'body': 'He lies', 'version': version}).status_code == 302
    with app.app_context():
        note = db.session.get(ContentEntry, note_id)
        assert (note.title, note.body) == (note.presentations[0].title, note.presentations[0].body) == ('Ferryman', 'He lies')
    assert client.get(f'/party/2/notes/{note_id}/edit').status_code == 404  # Only through its own party.
    assert client.post(f'/party/3/notes', data={'title': 'x'}).status_code == 403  # Someone else's party.

    assert client.post(f'/party/1/notes/{note_id}/delete').status_code == 302
    with app.app_context():
        assert db.session.get(ContentEntry, note_id) is None and PartyPresentation.query.count() == 0


def test_deleting_a_party_deletes_its_notes(setup):
    app, client = setup
    client.post('/party/1/notes', data={'title': 'Gone with the party'})
    with app.app_context():
        from app.lib.campaigns import delete_party_notes
        delete_party_notes(1)
        db.session.commit()
        assert ContentEntry.query.filter_by(category='party_note').count() == 0


def test_unfiled_party_note_moves_to_a_campaign(setup):
    app, client = setup
    client.post('/materials/new', data={'category': 'note', 'title': 'Loose note', 'body': 'Ferry at dawn'})
    with app.app_context():
        note = ContentEntry.query.filter_by(title='Loose note').one()
        note_id, version = note.id, note.version
        assert note.campaign_id is None
    page = client.get(f'/materials/wiki/{note_id}/').text
    assert 'Move to campaign' in page and '<option value="1">Secret campaign</option>' in page
    assert client.post(f'/materials/{note_id}/move', data={'campaign_id': 1, 'version': version + 5}).status_code == 409
    moved = client.post(f'/materials/{note_id}/move', data={'campaign_id': 1, 'version': version})
    assert moved.status_code == 302 and moved.location == f'/campaigns/1/wiki/{note_id}/'
    with app.app_context():
        assert db.session.get(ContentEntry, note_id).campaign_id == 1
    assert 'Move to campaign' not in client.get(f'/campaigns/1/wiki/{note_id}/').text  # Only offered for unfiled articles.


def test_create_new_campaign_redirects_to_campaign_creation(setup):
    app, client = setup
    response = client.post('/campaigns/create', data={'kind': 'campaign', 'name': 'Fresh start'})
    assert response.status_code == 302
    with app.app_context():
        created = Campaign.query.filter_by(owner_id=1, name='Fresh start').one()
    assert f'campaign_id={created.id}' in response.location and 'kind=realm' in response.location


def test_create_new_note_opens_article_form_with_name_and_type(setup):
    app, client = setup
    response = client.post('/campaigns/create', data={'kind': 'note', 'name': 'Session zero notes'})
    assert response.status_code == 302 and response.location.endswith('/materials/new?title=Session+zero+notes&category=note')
    page = client.get(response.location).get_data(as_text=True)
    assert 'value="Session zero notes"' in page and 'data-selected-category="note"' in page
    with app.app_context():
        assert Campaign.query.filter_by(name='Session zero notes').count() == 0


def test_create_new_rejects_bad_kind_and_blank_name_and_requires_csrf(setup):
    app, client = setup
    assert client.post('/campaigns/create', data={'kind': 'map', 'name': 'x'}).status_code == 400
    assert client.post('/campaigns/create', data={'kind': 'note', 'name': '   '}).status_code == 400
    assert client.post('/campaigns/create', data={'kind': 'campaign'}).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/campaigns/create', data={'kind': 'campaign', 'name': 'No token'}).status_code == 400
    assert app.test_client().post('/campaigns/create', data={'kind': 'campaign', 'name': 'x'}).status_code == 302


def test_new_article_form_ignores_unsafe_category_hint(setup):
    app, client = setup
    for hint in ('map', 'overview', 'bogus'):
        page = client.get(f'/materials/new?category={hint}&title=Hello').get_data(as_text=True)
        assert 'data-selected-category="custom"' in page and 'value="Hello"' in page


def test_empty_unfiled_section_is_muted_without_chevron(setup):
    app, client = setup
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'href="/materials/"' not in page and 'tree-empty-title' in page
    assert 'Create New' in page and 'create-dialog' in page
    client.post('/materials/new', data={'category': 'note', 'title': 'Loose note', 'body': 'x'})
    page = client.get('/campaigns/').get_data(as_text=True)
    assert 'href="/materials/"' in page and 'tree-empty-title' not in page

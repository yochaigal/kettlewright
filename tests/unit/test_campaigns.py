import json
import re

import pytest
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import Session

from app.models import (db, User, Party, Character, Campaign, CampaignParty,
                        ContentEntry, PartyPresentation, PointcrawlMap, MapNode, MapEdge)
from app.lib.campaigns import render_content


@pytest.fixture
def setup(app_with_babel):
    app = app_with_babel
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


def reveal(client, entry_id, party_id=1, version=0, title='Known name', body='Known facts', **extra):
    return client.post(f'/materials/{entry_id}/reveal', data={'party_ids':str(party_id),
        f'version_{party_id}':version, f'title_{party_id}':title, f'body_{party_id}':body, **extra})


def create_map(client, campaign_id=1, title='SECRET MAP', nodes=2):
    draft={'nodes':[{'id':f'new-node-{i}', 'number':i+1,'x':i*100,'y':100,
        'title':f'SECRET ROOM {i}', 'body':f'SECRET TRAP {i}'} for i in range(nodes)],
        'edges':[{'id':'new-edge-0','source':'new-node-0','target':'new-node-1',
                  'title':'SECRET PASSAGE','body':'SECRET KEY','path_type':'hidden'}] if nodes>1 else []}
    response=client.post('/maps/new',data={'campaign_id':campaign_id,'title':title,
        'kind':'dungeon','draft':json.dumps(draft)})
    assert response.status_code==302, response.get_data(as_text=True)
    map_id=int(re.search(r'/maps/(\d+)/edit',response.location).group(1))
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


def test_direct_publication_without_campaign_and_adoption(setup):
    app,client=setup
    response=client.post('/materials/new',data={'party_id':1,'category':'lore',
        'title':'Rumour','body':'Something heard in play'})
    assert response.status_code==302
    with app.app_context():
        entry=ContentEntry.query.one()
        entry_id=entry.id
        assert entry.title==entry.body==''
        assert entry.campaign_id is None
    assert client.post(f'/materials/{entry_id}/edit',data={'version':1,'category':'lore',
        'title':'The truth','body':'Private context','campaign_id':1}).status_code==302
    login(client,2)
    row=client.get('/party/1/materials/data').json['entries'][0]
    assert row['title']=='Rumour' and row['body']=='Something heard in play'
    assert client.get('/party/1/materials/').status_code==200


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
    assert reveal(client,entry_id,version=3).status_code==302
    with app.app_context():
        db.session.get(Character,1).party_id=None
        # A stale subowners list must not grant access.
        db.session.get(Party,1).subowners='[2]'
        db.session.commit()
    login(client,2)
    assert client.get('/party/1/materials/data').status_code==403
    assert client.get(f'/party/1/materials/{entry_id}').status_code==403


def test_multiple_parties_publish_atomically(setup):
    app,client=setup
    entry_id=create_entry(client)
    response=client.post(f'/materials/{entry_id}/reveal',data={'party_ids':['1','2'],
        'version_1':0,'title_1':'A','body_1':'A facts','version_2':5,'title_2':'B'})
    assert response.status_code==409
    with app.app_context():
        assert PartyPresentation.query.count()==0
    assert client.post(f'/materials/{entry_id}/reveal',data={'party_ids':['1','2'],
        'version_1':0,'title_1':'A','version_2':0,'title_2':'B'}).status_code==302
    assert reveal(client,entry_id,party_id=3).status_code==403


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


def test_disconnect_revokes_and_deleting_campaign_retains_materials(setup):
    app,client=setup
    entry_id=create_entry(client)
    reveal(client,entry_id)
    assert client.post('/campaigns/1/',data={'version':1,'name':'Renamed','party_ids':['2']}).status_code==302
    login(client,2)
    assert client.get('/party/1/materials/data').json['entries']==[]
    login(client,1)
    assert client.post('/campaigns/1/delete',data={'version':2}).status_code==302
    with app.app_context():
        assert db.session.get(ContentEntry,entry_id).campaign_id is None


def test_xss_and_protocols():
    value=str(render_content('<script>alert(1)</script>\njavascript:alert(1) https://example.com/path'))
    assert '<script>' not in value
    assert '<br>' in value
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
                 '/materials/new?party_id=1','/materials/import','/maps/new','/tools/']:
        response=client.get(path)
        assert response.status_code==200, (path,response.get_data(as_text=True))
    map_id,_=create_map(client)
    assert client.get(f'/maps/{map_id}/edit').status_code==200
    assert set(client.get('/maps/tables').json)=={'Dungeon','Forest','Realm'}


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


def test_direct_map_publication_without_campaign_is_atomic(setup):
    app,client=setup
    draft={'nodes':[{'id':'new-a','number':1,'x':100,'y':100,'title':'Known place','body':'Known facts'}], 'edges':[]}
    response=client.post('/maps/new',data={'party_id':1,'title':'Drawn during play',
        'kind':'realm','draft':json.dumps(draft)})
    assert response.status_code==302
    assert '/party/1/maps/' in response.location
    with app.app_context():
        assert Campaign.query.count()==1 # Existing campaign only, no implicit campaign.
        assert all(entry.campaign_id is None for entry in ContentEntry.query.all())
        assert PartyPresentation.query.count()==2
    login(client,2)
    data=client.get(response.location+'data').json
    assert data['title']=='Drawn during play'
    assert data['nodes'][0]['title']=='Known place'
    login(client,3)
    assert client.get('/party/2/maps/1/data').status_code==404

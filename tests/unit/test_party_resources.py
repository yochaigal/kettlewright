import json
import re
from unittest.mock import patch

import pytest
from app.models import db, User, Character, Party

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'


@pytest.fixture
def resources(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all(User(id=i,username=f'user{i}') for i in range(1,5))
        db.session.add(Party(id=1,owner=1,owner_username='user1',name='Party',party_url='party',members='[1,2]',subowners='[2,3]',items='[]',containers=CONTAINERS))
        for i in (1,2):
            db.session.add(Character(id=i,owner=i+1,owner_username=f'user{i+1}',name=f'Hero{i}',url_name=f'hero{i}',background='Test',
                                     party_id=1,items='[]',containers=CONTAINERS,hp=3,hp_max=6))
        db.session.commit()
    clients={}
    for i in range(1,5):
        clients[i]=app.test_client()
        with clients[i].session_transaction() as session:
            session['_user_id']=str(i)
            session['_fresh']=True
    return app,clients


EDIT='/charedit/inplace-inventory/user2/hero1'
ACTION='/party/1/wilderness'


def test_warden_inventory_controls_and_every_mutation(resources):
    app,clients=resources
    assert clients[1].get('/party/1/members').data.count(b'aria-label="Manage inventory: ')==2
    assert b'/charedit/inplace-inventory/user2/hero1' in clients[1].get('/users/user2/characters/hero1/').data
    assert clients[1].get(EDIT+'/0').status_code==200
    for uid in (3,4):
        assert clients[uid].get(EDIT+'/0').status_code==403
        assert clients[uid].post(EDIT+'/0/fatigue').status_code==403
    assert app.test_client().get(EDIT+'/0').status_code==403
    assert clients[1].get(EDIT+'/0/fatigue').status_code==405
    assert clients[1].post(EDIT+'/0/fatigue').status_code==200
    item_form=dict(edit_item_name='Rations',edit_item_tags='uses',edit_item_uses='3',edit_item_charges='',edit_item_max_charges='',edit_item_container='0',edit_item_description='')
    assert clients[1].post(EDIT+'/item-edit/None/save?mode=create',data=item_form).status_code==200
    with app.app_context():
        items=json.loads(db.session.get(Character,1).items)
        assert len(items)==2
        item=next(i for i in items if i['name']=='Rations')
    assert clients[1].post(EDIT+f'/item-edit/{item["id"]}/amount?action=minus&property=uses').status_code==200
    assert clients[1].post(EDIT+f'/0/item-delete/{item["id"]}').status_code==200
    # Character-wide save and identity are still owner-only.
    assert clients[1].post('/charedit/user2/hero1/save').status_code==403


def test_stale_membership_revokes_inventory_access(resources):
    app,clients=resources
    with app.app_context():
        db.session.get(Party,1).members='[2]'
        db.session.commit()
    assert clients[1].post(EDIT+'/0/fatigue').status_code==403
    assert clients[2].post(EDIT+'/0/fatigue').status_code==200


def test_inventory_and_wilderness_csrf(resources):
    app,clients=resources
    app.config['WTF_CSRF_ENABLED']=True
    assert clients[1].post(EDIT+'/0/fatigue').status_code==400
    assert clients[1].post(ACTION,data={'action':'supply','participants':'1','version':'0'}).status_code==400
    html=clients[1].get('/users/user1/parties/party/').text
    token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',html).group(1)
    assert clients[1].post(EDIT+'/0/fatigue',data={'csrf_token':token}).status_code==200


@pytest.mark.parametrize('count,expected', [(1,4),(2,6),(3,8),(4,10),(5,12),(9,12)])
def test_supply_die_progression(resources,count,expected):
    from app.lib.wilderness import supply
    app,_=resources
    with app.app_context(),patch('app.lib.wilderness.secrets.randbelow',return_value=0) as roll:
        party=db.session.get(Party,1)
        assert supply(party,list(range(count)))==(expected,1)
        roll.assert_called_once_with(expected)
        assert json.loads(party.items)[0]['uses']==3


def test_supply_records_result_and_rejects_duplicate_submission(resources):
    app,clients=resources
    data={'action':'supply','participants':['1','2'],'version':'0'}
    with patch('app.lib.wilderness.secrets.randbelow',return_value=2):
        assert clients[1].post(ACTION,data=data).status_code==302
    clients[1].post(ACTION,data=data)
    with app.app_context():
        party=db.session.get(Party,1)
        assert len(json.loads(party.items))==3
        assert party.version==1
    assert b'Gather supplies' in clients[1].get('/users/user1/parties/party/').data


@pytest.mark.parametrize('uid', [2,3,4])
def test_only_warden_can_apply_group_actions(resources,uid):
    _,clients=resources
    assert clients[uid].post(ACTION,data={'action':'supply','participants':'1','version':'0'}).status_code==403


@pytest.mark.parametrize('selected', [[],['99'],['1','1']])
def test_invalid_participants(resources,selected):
    _,clients=resources
    assert clients[1].post(ACTION,data={'action':'supply','participants':selected,'version':'0'}).status_code==400


def test_camp_is_atomic_and_consumes_one_use_per_character(resources):
    app,clients=resources
    with app.app_context():
        for i in (1,2):
            c=db.session.get(Character,i)
            c.items=json.dumps([dict(id=f'f{i}',name='Fatigue',tags=[],location=0)])
        db.session.get(Party,1).items=json.dumps([dict(id='r',name='Rations',uses=1,tags=['uses'],location=0)])
        db.session.commit()
    data={'action':'camp','participants':['1','2'],'version':'0'}
    assert clients[1].post(ACTION,data=data).status_code==302
    with app.app_context():
        assert db.session.get(Party,1).version==0
        assert json.loads(db.session.get(Party,1).items)[0]['uses']==1
        assert len(json.loads(db.session.get(Character,1).items))==1
        p=db.session.get(Party,1)
        items=json.loads(p.items);items[0]['uses']=3;p.items=json.dumps(items)
        db.session.commit()
    clients[1].post(ACTION,data=data)
    with app.app_context():
        assert json.loads(db.session.get(Party,1).items)[0]['uses']==1
        for i in (1,2):
            assert db.session.get(Character,i).items=='[]'
            assert db.session.get(Character,i).hp==3


def test_camp_feeds_selected_mount_and_uses_personal_rations_first(resources):
    from app.models import Companion
    app,clients=resources
    with app.app_context():
        hero=db.session.get(Character,1)
        hero.deprived=True
        hero.items=json.dumps([dict(id='food',name='Rations',tags=['uses'],uses=1,location=0),dict(id='f',name='Fatigue',tags=[],location=0)])
        hero.pets.append(Companion(id=1,kind='pet',name='Horse',items='[]',containers=CONTAINERS))
        db.session.get(Party,1).items=json.dumps([dict(id='shared',name='Rations',tags=['uses'],uses=3,location=0)])
        db.session.commit()
    clients[1].post(ACTION,data={'action':'camp','participants':'1','mounts':'1','version':'0'})
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items)[0]['name']=='Fatigue'
        assert db.session.get(Character,1).deprived is True
        assert json.loads(db.session.get(Party,1).items)[0]['uses']==2


def test_dead_participants_and_foreign_mounts_are_rejected(resources):
    app,clients=resources
    with app.app_context():
        db.session.get(Character,1).dead=True
        db.session.commit()
    assert clients[1].post(ACTION,data={'action':'supply','participants':'1','version':'0'}).status_code==400
    assert clients[1].post(ACTION,data={'action':'camp','participants':'2','mounts':'999','version':'0'}).status_code==400
    with app.app_context(): assert db.session.get(Party,1).version==0


def test_camp_can_explicitly_resolve_deprivation(resources):
    app,clients=resources
    with app.app_context():
        hero=db.session.get(Character,1)
        hero.deprived=True
        hero.items=json.dumps([dict(id='r',name='Rations',tags=['uses'],uses=1,location=0),dict(id='f',name='Fatigue',tags=[],location=0)])
        db.session.commit()
    clients[1].post(ACTION,data={'action':'camp','participants':'1','resolve_deprivation':'on','version':'0'})
    with app.app_context():
        assert db.session.get(Character,1).deprived is False
        assert db.session.get(Character,1).items=='[]'

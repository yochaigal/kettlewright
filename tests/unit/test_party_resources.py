import json
import re

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


def test_inventory_csrf(resources):
    app,clients=resources
    app.config['WTF_CSRF_ENABLED']=True
    assert clients[1].post(EDIT+'/0/fatigue').status_code==400
    html=clients[1].get('/users/user1/parties/party/').text
    token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',html).group(1)
    assert clients[1].post(EDIT+'/0/fatigue',data={'csrf_token':token}).status_code==200

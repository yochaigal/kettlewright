import json

import pytest
from flask import g
from werkzeug.exceptions import BadRequest

from app.lib.ground_items import ground_container, ground_items, preserve_ground
from app.lib.inventory import Inventory
from app.models import Character, Party, User, db


@pytest.fixture
def ground_game(app_with_babel):
    app = app_with_babel
    # create_app retains an application context in this repository's fixtures.
    # Real requests get fresh g; do not let Flask-Login cache one client's user
    # while these tests switch between independent player sessions.
    @app.before_request
    def reset_test_login_cache():
        g.pop('_login_user', None)
    with app.app_context():
        db.session.add_all([User(id=i, username=name) for i, name in enumerate(('alice', 'bob', 'warden', 'outsider'), 1)])
        db.session.add(Party(id=1, owner=3, name='Party', party_url='test', members='[1,2]', items='[]',
                             containers='[{"id":0,"name":"Storage","slots":10}]'))
        db.session.add_all([Character(id=i, owner=i, name=name, url_name=name.lower(), background='Test',
            party_id=1 if i < 3 else None, items='[]',
            containers='[{"id":0,"name":"Main","slots":10}]') for i, name in enumerate(('Alice', 'Bob', 'Warden'), 1)])
        source = db.session.get(Character, 1)
        source.items = json.dumps([
            dict(id='torch', name='Torch', tags=['uses'], uses=2, max_uses=3, location=0, description='Keep this description'),
            dict(id='marker', name='Carrying Chest', tags=[], location=0, carrying=2),
            dict(id='gem', name='Gem', tags=['petty'], location=2),
            dict(id='inner-marker', name='Carrying Pouch', tags=[], location=2, carrying=4),
            dict(id='key', name='Key', tags=['petty'], location=4)])
        source.containers = json.dumps([dict(id=0, name='Main', slots=10),
            dict(id=2, name='Chest', slots=4, carried_by=0, load=1),
            dict(id=4, name='Pouch', slots=2, carried_by=2, load=1)])
        db.session.commit()
    return app


def client_for(app, user_id=1):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True
    return client


def snapshot(app):
    with app.app_context():
        source = db.session.get(Character, 1)
        party = db.session.get(Party, 1)
        target = db.session.get(Character, 2)
        return source.items, source.containers, party.items, party.containers, target.items, target.containers


def drop(client, kind='item', object_id='torch', place='Beside the bridge'):
    return client.post(f'/characters/1/drop/{kind}/{object_id}', data={'place': place, 'inventory_context': 'sheet'},
                       headers={'HX-Request': 'true'})


def test_web_drop_requires_place_preserves_details_and_shared_pickup(ground_game):
    app = ground_game
    alice, bob = client_for(app), client_for(app, 2)
    before = snapshot(app)
    modal = alice.get('/characters/1/drop/item/torch')
    assert modal.status_code == 200 and b'name="place" required maxlength="200"' in modal.data
    rejected = drop(alice, place='  ')
    assert rejected.headers['HX-Retarget'] == '#modal-anchor'
    assert snapshot(app) == before
    response = drop(alice, place='<script>alert(1)</script> by the bridge')
    assert response.status_code == 200 and response.headers['HX-Trigger'] == 'refresh-stats'
    with app.app_context():
        party = db.session.get(Party, 1)
        assert ground_container(party)['name'] == 'on the ground'
        entry = ground_items(party)[0]
        assert entry['uses'] == 2 and entry['description'] == 'Keep this description'
        assert entry['dropped_by'] == 'Alice'
    page = bob.get('/party/1/ground')
    assert b'&lt;script&gt;' in page.data and b'<script>alert(1)</script>' not in page.data
    assert b'value="2"' in page.data and b'value="1"' not in page.data
    response = bob.post('/party/1/ground/torch/pickup', data={'character': '2'}, headers={'HX-Request': 'true'})
    assert response.status_code == 200 and b'There is nothing on the ground' in response.data
    with app.app_context():
        target = json.loads(db.session.get(Character, 2).items)[0]
        assert target['id'] == 'torch' and target['location'] == 0 and target['uses'] == 2
        assert 'ground_place' not in target and 'dropped_by' not in target
    before = snapshot(app)
    bob.post('/party/1/ground/torch/pickup', data={'character': '2'})
    assert snapshot(app) == before


def test_drop_container_moves_nested_contents_and_restores_carrying(ground_game):
    app = ground_game
    alice, bob = client_for(app), client_for(app, 2)
    assert b'contents' not in alice.get('/characters/1/drop/container/0').data
    before = snapshot(app)
    assert drop(alice, 'container', '0').status_code == 400
    assert snapshot(app) == before
    assert drop(alice, 'container', '2', 'In the cellar').status_code == 200
    with app.app_context():
        c = db.session.get(Character, 1)
        assert [i['id'] for i in json.loads(c.items)] == ['torch']
        assert [i['id'] for i in json.loads(c.containers)] == [0]
        entry = ground_items(db.session.get(Party, 1))[0]
        dropped_id = entry['id']
        assert len(entry['ground_bundle']['containers']) == 2
        assert len(entry['ground_bundle']['items']) == 3
    page = bob.get('/party/1/ground')
    assert all(word in page.data for word in (b'Chest', b'In the cellar', b'Gem', b'Key', b'Contents'))
    with app.app_context():
        # Occupied IDs at the destination must be remapped, not overwritten.
        db.session.get(Character, 2).containers = '[{"id":0,"name":"Main","slots":0},{"id":2,"name":"Existing","slots":1}]'
        db.session.commit()
    before = snapshot(app)
    response = bob.post(f'/party/1/ground/{dropped_id}/pickup', data={'character': '2'})
    assert b'Not enough free slots' in response.data
    assert snapshot(app) == before
    with app.app_context():
        db.session.get(Character, 2).containers = '[{"id":0,"name":"Main","slots":10},{"id":2,"name":"Existing","slots":1}]'
        db.session.commit()
    bob.post(f'/party/1/ground/{dropped_id}/pickup', data={'character': '2'})
    with app.app_context():
        target = db.session.get(Character, 2)
        containers = {c['name']: c for c in json.loads(target.containers)}
        items = {i['id']: i for i in json.loads(target.items)}
        assert len(containers) == 4
        assert items['gem']['location'] == containers['Chest']['id']
        assert items['key']['location'] == containers['Pouch']['id']
        assert containers['Pouch']['carried_by'] == containers['Chest']['id']
        assert items['marker']['carrying'] == containers['Chest']['id']
        assert items['marker']['location'] == 0
        assert target.occupiedMainSlots() == 1
        assert ground_items(db.session.get(Party, 1)) == []


def test_ground_permissions_csrf_and_live_membership(ground_game):
    app = ground_game
    alice = client_for(app)
    before = snapshot(app)
    for user in (2, 3, 4):
        assert drop(client_for(app, user)).status_code == 403
    assert snapshot(app) == before
    assert client_for(app, 4).get('/party/1/ground').status_code == 403
    assert app.test_client().get('/party/1/ground').status_code == 302
    app.config['WTF_CSRF_ENABLED'] = True
    assert drop(alice).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = False
    drop(alice)
    bob = client_for(app, 2)
    assert bob.post('/party/1/ground/torch/pickup', data={'character': '1'}).status_code == 403
    app.config['WTF_CSRF_ENABLED'] = True
    assert bob.post('/party/1/ground/torch/pickup', data={'character': '2'}).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.session.get(Party, 1).members = '[1]'
        db.session.commit()
    before = snapshot(app)
    assert bob.post('/party/1/ground/torch/pickup', data={'character': '2'}).status_code == 403
    assert snapshot(app) == before


def test_regular_inventory_routes_cannot_bypass_ground_actions(ground_game):
    app = ground_game
    drop(client_for(app))
    with app.app_context():
        party = db.session.get(Party, 1)
        inv = Inventory(party)
        ground_id = ground_container(party)['id']
        with pytest.raises(BadRequest):
            inv.delete_item(ground_id, 'torch')
        with pytest.raises(BadRequest):
            inv.transfer_item('torch', db.session.get(Character, 2))
        with pytest.raises(BadRequest):
            inv.create_item('Other', '', 0, 0, 0, ground_id, '')
        with pytest.raises(BadRequest):
            inv.delete_container(ground_id, 0)


def test_old_cancel_does_not_duplicate_dropped_container_or_erase_ground(ground_game):
    app = ground_game
    alice = client_for(app)
    before = snapshot(app)
    drop(alice, 'container', '2')
    dropped = snapshot(app)
    response = alice.post('/charedit/alice/alice/cancel', data={
        'old_items': before[0], 'old_containers': before[1], 'old_gold': '0'})
    assert response.status_code == 200
    after = snapshot(app)
    assert after[:4] == dropped[:4]
    with app.app_context():
        party = db.session.get(Party, 1)
        restored_items, restored_containers = preserve_ground(party, json.loads(before[2]), json.loads(before[3]))
        assert restored_items == json.loads(party.items)
        assert restored_containers == json.loads(party.containers)


def test_empty_container_and_rejected_fatigue_bundle(ground_game):
    app = ground_game
    alice = client_for(app)
    with app.app_context():
        source = db.session.get(Character, 1)
        source.items = '[{"id":"fatigue","name":"Fatigue","tags":[],"location":2}]'
        db.session.commit()
    before = snapshot(app)
    assert b'Clear Fatigue' in drop(alice, 'container', '2').data
    assert snapshot(app) == before
    with app.app_context():
        db.session.get(Character, 1).items = '[]'
        db.session.commit()
    assert drop(alice, 'container', '4', 'At the campsite').status_code == 200
    with app.app_context():
        entry = ground_items(db.session.get(Party, 1))[0]
        entry_id = entry['id']
        assert entry['ground_bundle']['items'] == []
    response = client_for(app, 2).post(f'/party/1/ground/{entry_id}/pickup', data={'character': '2'})
    assert response.status_code == 200
    with app.app_context():
        assert json.loads(db.session.get(Character, 2).containers)[1]['name'] == 'Pouch'


def test_stale_party_snapshot_does_not_restore_picked_up_ground_item(ground_game):
    app = ground_game
    alice = client_for(app)
    drop(alice)
    old = snapshot(app)
    client_for(app, 2).post('/party/1/ground/torch/pickup', data={'character': '2'})
    with app.app_context():
        party = db.session.get(Party, 1)
        restored, containers = preserve_ground(party, json.loads(old[2]), json.loads(old[3]))
        assert restored == []
        assert len([c for c in containers if c.get('on_the_ground')]) == 1

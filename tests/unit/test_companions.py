import json
import re
from unittest.mock import patch

import pytest
from app.models import Character, Companion, Party, User, db
from app.lib.companions import catalog, import_pet, new_hireling, pet_data

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'


@pytest.fixture
def world(app_with_babel):
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=i,username=f'keeper{i}') for i in range(1,5)])
        db.session.add(Party(id=1,owner=1,owner_username='keeper1',name='Expedition',party_url='expedition',members='[1,2]',subowners='[2,3]',items='[]',containers=CONTAINERS))
        for i in (1,2):
            db.session.add(Character(id=i,name=f'Hero{i}',owner=i+1,owner_username=f'keeper{i+1}',url_name=f'hero{i}',background='Prowler',party_id=1,
                                     items='[]',containers=CONTAINERS,hp=3,hp_max=6,strength=8,strength_max=11,dexterity=9,dexterity_max=12,willpower=10,willpower_max=13))
        db.session.commit()
        h = new_hireling(db.session.get(Party,1),'Bodyguard')
        h.id = 1
        db.session.add(h)
        pet = import_pet(pet_data(catalog('pet')['Hollow Wolf'],db.session.get(Character,1)))
        pet.id = 2
        pet.character_id = 1
        db.session.add_all([h,pet])
        db.session.commit()
    clients = {}
    for i in range(1,5):
        client = app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(i)
            session['_fresh'] = True
        clients[i] = client
    return app,clients


def test_hireling_rolls_and_all_marketplace_roles(app_with_babel):
    with app_with_babel.app_context():
        templates = catalog('hireling')
        assert len(templates) == 12
        assert {t['name']:t['daily_cost'] for t in templates} == {'Alchemist':30,'Animal Handler':5,'Blacksmith':15,'Bodyguard':10,'Local Guide':5,'Lockpick':10,'Navigator':10,'Sailor':5,'Scholar':20,'Tracker':5,'Trapper':5,'Veteran Bodyguard':20}
        for template in templates:
            with patch('app.lib.companions.randint',return_value=4) as roll:
                h = new_hireling(Party(name='Test'),template['name'])
            assert roll.call_count == 10
            assert h.hp == h.hp_max == 4
            assert h.strength == h.dexterity == h.willpower == 12
            assert h.daily_cost == template['daily_cost']
            assert any(it['name'] == 'Rations' for it in json.loads(h.items))


@pytest.mark.parametrize('user,status',[(1,204),(2,204),(3,204),(4,403)])
def test_shared_hireling_permissions(world,user,status):
    _,clients = world
    assert clients[user].post('/companions/1/stat',data=dict(stat='hp',value=0)).status_code == status


def test_restricted_hireling_and_stale_member(world):
    app,clients = world
    with app.app_context():
        db.session.get(Companion,1).shared = False
        db.session.commit()
    assert clients[2].post('/companions/1/stat',data=dict(stat='hp',value=0)).status_code == 403
    assert clients[1].post('/companions/1/stat',data=dict(stat='hp',value=0)).status_code == 204
    with app.app_context():
        db.session.get(Companion,1).shared = True
        db.session.get(Character,1).party_id = None
        db.session.commit()
    assert clients[2].post('/companions/1/stat',data=dict(stat='hp',value=0)).status_code == 403


def test_pet_is_only_editable_by_owner(world):
    _,clients = world
    for uid in (1,3,4):
        assert clients[uid].post('/companions/2/stat',data=dict(stat='hp',value=0)).status_code == 403
    assert clients[2].post('/companions/2/stat',data=dict(stat='hp',value=0)).status_code == 204
    assert clients[2].post('/companions/2/stat',data=dict(stat='hp',value=6)).status_code == 400


def test_pages_and_creation(world):
    app,clients = world
    assert clients[1].get('/parties/1/hirelings/add').status_code == 200
    assert clients[2].get('/characters/1/pets/add').status_code == 200
    assert clients[1].get('/companions/1').status_code == 200
    assert clients[2].get('/companions/2').status_code == 200
    assert b'party-hirelings' in clients[1].get('/users/keeper1/parties/expedition/').data
    assert b'character-pets' in clients[2].get('/users/keeper2/characters/hero1/').data
    assert clients[4].get('/companions/1').status_code == 403
    assert clients[2].post('/parties/1/hirelings/add',data=dict(template='Alchemist')).status_code == 403
    assert clients[1].post('/parties/1/hirelings/add',data=dict(template='Alchemist',name='Ada')).status_code == 302
    assert clients[2].post('/characters/1/pets/add',data=dict(template='Raven Familiar',name='Ink')).status_code == 302
    assert clients[2].post('/hirelings/1/pets/add',data=dict(template='Custom',name='Cat')).status_code == 404
    with app.app_context():
        assert Companion.query.filter_by(name='Ada').one().daily_cost == 30
        assert Companion.query.filter_by(name='Ink').one().strength == 3


def test_csrf_and_delete(world):
    app,clients = world
    app.config['WTF_CSRF_ENABLED'] = True
    for path in ('/companions/1/delete','/companions/1/stat','/companions/1/inventory','/companions/1/transfer'):
        assert clients[2].post(path).status_code == 400
    html = clients[1].get('/companions/1?mode=edit').get_data(as_text=True)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"',html)[1]
    assert clients[1].post('/companions/1/delete',data={'csrf_token':token}).status_code == 302
    with app.app_context():
        assert db.session.get(Companion,1) is None
        assert db.session.get(Companion,2) is not None


def test_transfers_keep_metadata_and_enforce_capacity_and_ownership(world):
    app,clients = world
    item = dict(id='relic',name='Relic',tags=['charges','petty'],charges=1,max_charges=3,armor_active=False,description='Magic',location=0)
    with app.app_context():
        db.session.get(Character,1).items = json.dumps([item])
        db.session.commit()
    transfer = dict(direction='in',source_item='character:1|relic',location=0)
    assert clients[3].post('/companions/1/transfer',data=transfer).status_code == 403
    assert clients[2].post('/companions/1/transfer',data=transfer).status_code == 302
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items) == []
        assert item in json.loads(db.session.get(Companion,1).items)
    assert clients[2].post('/companions/1/transfer',data=dict(direction='out',destination='character:1|0',item_id='relic')).status_code == 302
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items) == [item]
        item['tags'] = ['bulky']
        db.session.get(Character,1).items = json.dumps([item])
        db.session.get(Companion,1).containers = '[{"id":0,"name":"Main","slots":0}]'
        db.session.commit()
    assert clients[2].post('/companions/1/transfer',data=transfer).status_code == 400
    with app.app_context():
        assert len(json.loads(db.session.get(Character,1).items)) == 1


def test_manual_familiars_and_nightmare(app_with_babel):
    with app_with_babel.app_context():
        c = Character(name='Witch', hp=2, hp_max=6, strength=9, strength_max=12,
                      dexterity=11, dexterity_max=11, willpower=8, willpower_max=13)
        nightmare = import_pet(pet_data(catalog('pet')['Living Nightmare'], c))
        raven = import_pet(pet_data(catalog('pet')['Raven Familiar'], c))
        assert nightmare.hp == 2 and nightmare.hp_max == 6
        assert nightmare.strength == 9 and nightmare.strength_max == 12
        assert raven.hp == 8 and raven.willpower == 13


def test_pet_export_import_and_print(world):
    app,clients = world
    with app.app_context():
        c = db.session.get(Character,1)
        data = json.loads(c.toJSON())
        assert data['pets'][0]['name'] == 'Hollow Wolf'
        form = {k:json.dumps(v) if isinstance(v,(list,bool)) else v for k,v in data.items() if v is not None}
    form['gold'] = 0
    assert clients[2].post('/new_from_json/',data=form).status_code == 302
    with app.app_context():
        imported = Character.query.order_by(Character.id.desc()).first()
        assert imported.pets[0].export() == data['pets'][0]
    html = clients[2].get('/users/keeper2/characters/hero1/print/').data
    assert b'Hollow Wolf' in html


def test_invalid_pet_import():
    for data in ([],dict(name='A',hp=-1),dict(name='A',hp=5,hp_max=3),dict(name='A',hp=True),dict(name='A',items={})):
        with pytest.raises((ValueError,TypeError)):
            import_pet(data)


def test_inventory_containers_and_cascade(world):
    app,clients = world
    url = '/companions/1/inventory'
    assert clients[2].post(url,data=dict(action='container',name='Cart',slots=4)).status_code == 302
    assert clients[2].post(url,data=dict(action='item',name='Shield',tags='1 Armor',location=1,armor_active='on')).status_code == 302
    assert clients[2].post(url,data=dict(action='delete-container',container_id=1)).status_code == 400
    assert clients[2].post(url,data=dict(action='delete-container',container_id=0)).status_code == 400
    assert clients[4].post(url,data=dict(action='container',name='Bad',slots=1)).status_code == 403
    with app.app_context():
        c = db.session.get(Character,1)
        db.session.delete(c)
        db.session.commit()
        assert db.session.get(Companion,2) is None
        assert db.session.get(Companion,1) is not None


def test_full_main_inventory_has_no_available_hp_until_item_is_on_pet(world):
    app, clients = world
    with app.app_context():
        c = db.session.get(Character,1)
        c.items = json.dumps([dict(id=str(i),name='Gear',tags=[],location=0) for i in range(10)])
        c.hp = c.hp_max = 5
        pet = db.session.get(Companion,2)
        pet.containers = '[{"id":0,"name":"Main","slots":3}]'
        db.session.commit()
        assert c.hpValue() == [0,5]
    response = clients[2].post('/companions/2/transfer',data=dict(direction='in',source_item='character:1|0',location=0))
    assert response.status_code == 302
    with app.app_context():
        c = db.session.get(Character,1)
        assert c.hp == 5
        assert c.occupiedMainSlots() == 9
        assert c.hpValue() == [5,5]


def test_hireling_cart_load_and_removal(world):
    app,clients = world
    path = '/companions/1/inventory'
    assert clients[2].post(path,data=dict(action='container',name='Cart',slots=4,load=2)).status_code == 302
    with app.app_context():
        c = db.session.get(Companion,1)
        assert len([it for it in json.loads(c.items) if 'carrying' in it]) == 2
    assert clients[2].post(path,data=dict(action='delete-container',container_id=1)).status_code == 302
    with app.app_context():
        assert not any('carrying' in it for it in json.loads(db.session.get(Companion,1).items))


def test_generator_keeps_background_gear_and_creates_starting_pet(app_with_babel):
    from app.lib.char_utils import generate_character
    with app_with_babel.test_request_context('/'):
        character, raw = generate_character('Outrider')
        data = json.loads(raw)
        assert len(data['pets']) == 1
        assert data['pets'][0]['name'] == character.table2.option['pets'][0]
        assert data['items'] == character.items
        assert data['containers'] == character.containers


def test_manual_pets_have_published_stats(app_with_babel):
    with app_with_babel.test_request_context('/'):
        c = Character(name='Maker', background='Aurifex')
        pet = import_pet(pet_data(catalog('pet')['Homunculus'], c))
        assert pet.hp == 3 and pet.strength == 4
        assert pet.dexterity == 13 and pet.willpower == 5


def test_notes_never_create_pets(world):
    app, clients = world
    with app.app_context():
        c = db.session.get(Character, 2)
        c.notes = catalog('pet')['Homunculus']['notes']
        db.session.commit()
    assert clients[3].get('/users/keeper3/characters/hero2/').status_code == 200
    assert clients[3].post('/characters/2/pets/recover').status_code == 404
    with app.app_context():
        assert not db.session.get(Character, 2).pets


def test_hirelings_have_unique_item_ids(app_with_babel):
    with app_with_babel.app_context():
        party = Party(name='Test')
        first = new_hireling(party,'Bodyguard')
        second = new_hireling(party,'Bodyguard')
        assert not {i['id'] for i in json.loads(first.items)} & {i['id'] for i in json.loads(second.items)}


@pytest.fixture
def item_editor(world):
    app, clients = world
    original = dict(id='gear', name='Shield', tags=['1 Armor'], armor_active=False, location=0)
    with app.app_context():
        db.session.get(Character,1).items = json.dumps([original])
        db.session.get(Companion,2).containers = CONTAINERS
        other = import_pet(pet_data(catalog('pet')['Horse'], db.session.get(Character,2)))
        other.character_id = 2
        other.name = 'Other players horse'
        db.session.add(other)
        db.session.commit()
    data = dict(edit_item_name='Updated shield', edit_item_tags='2 Armor,uses',
                edit_item_uses='2', edit_item_charges='', edit_item_max_charges='',
                edit_item_description='Edited before moving', edit_item_armor_active='on',
                edit_item_container='companion:2:0')
    return app, clients, original, data


ITEM_URL = '/charedit/inplace-inventory/keeper2/hero1/item-edit/gear'


def test_existing_selector_only_offers_own_pets_and_hirelings(item_editor):
    app, clients, _, _ = item_editor
    html = clients[2].get(ITEM_URL).get_data(as_text=True)
    assert html.count('name="edit_item_container"') == 1
    assert 'Main (Pet: Hollow Wolf)</option>' in html
    assert ' — Hero1' not in html
    assert 'Other players horse' not in html
    assert 'value="companion:1:0"' in html
    warden = clients[1].get('/party/inventory/1/item-edit/none?mode=create').get_data(as_text=True)
    assert 'value="companion:' not in warden
    with app.app_context():
        db.session.get(Party,1).items = json.dumps([dict(id='gear', name='Gear', tags=[], location=0)])
        db.session.commit()
    warden = clients[1].get('/party/inventory/1/item-edit/gear').get_data(as_text=True)
    assert 'Other players horse' in warden
    assert 'Main (Pet: Hollow Wolf)</option>' in warden


@pytest.mark.parametrize('user,source', [(2,'character'), (1,'character'), (1,'party'), (2,'party')])
def test_existing_editor_moves_item_with_edits_and_cancel_restores_it(item_editor, user, source):
    app, clients, original, data = item_editor
    url = ITEM_URL
    cancel = '/charedit/keeper2/hero1/cancel'
    if source == 'party':
        with app.app_context():
            db.session.get(Party,1).items = json.dumps([original])
            db.session.commit()
        url = '/party/inventory/1/item-edit/gear'
        cancel = '/party/edit/keeper1/expedition/cancel'
    response = clients[user].post(url+'/save', data=data)
    assert response.status_code == 200
    assert 'HX-Retarget' not in response.headers
    with app.app_context():
        obj = db.session.get(Party if source == 'party' else Character, 1)
        assert json.loads(obj.items) == []
        item = json.loads(db.session.get(Companion,2).items)[0]
        assert item['name'] == 'Updated shield' and item['uses'] == 2
        assert item['armor_active'] is True
        assert item['description'] == 'Edited before moving'
    if user == 1 and source == 'character':
        return  # The character's full editor remains owner-only.
    assert clients[user].post(cancel, data=dict(old_items=json.dumps([original]),old_containers=CONTAINERS,old_gold=0)).status_code == 200
    with app.app_context():
        obj = db.session.get(Party if source == 'party' else Character, 1)
        assert json.loads(obj.items) == [original]
        assert json.loads(db.session.get(Companion,2).items) == []


@pytest.mark.parametrize('failure', ['full','foreign','missing','outsider','csrf','stale_party'])
def test_editor_transfer_failure_is_atomic(item_editor, failure):
    app, clients, original, data = item_editor
    client = clients[2]
    with app.app_context():
        if failure == 'full':
            db.session.get(Companion,2).containers = '[{"id":0,"name":"Main","slots":1}]'
            data['edit_item_tags'] = 'bulky'
        elif failure == 'foreign':
            data['edit_item_container'] = f'companion:{Companion.query.filter_by(name="Other players horse").one().id}:0'
        elif failure == 'missing':
            data['edit_item_container'] = 'companion:2:99'
        elif failure == 'outsider':
            client = clients[4]
        elif failure == 'csrf':
            app.config['WTF_CSRF_ENABLED'] = True
        else:
            db.session.get(Party,1).members = '[2]'
            data['edit_item_container'] = 'companion:1:0'
        db.session.commit()
        pet_items = db.session.get(Companion,2).items
    response = client.post(ITEM_URL+'/save', data=data)
    assert response.headers.get('HX-Retarget') == '#add-edit-item-modal-error-text'
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items) == [original]
        assert db.session.get(Companion,2).items == pet_items


def test_companion_uses_character_sheet_and_shared_inventory_modals(world):
    app, clients = world
    client = clients[2]
    page = client.get('/companions/1').get_data(as_text=True)
    assert 'view-character-sheet' in page and 'inventory-item-container' in page
    assert '<h3>Pets</h3>' not in page and 'Add pet' not in page
    assert 'Receive item' not in page and 'Give item' not in page
    page = client.get('/companions/1?mode=edit').get_data(as_text=True)
    assert 'companion-edit-form' in page and 'character-attribute-input' in page
    assert 'name="shared"' not in page
    assert 'name="shared"' in clients[1].get('/companions/1?mode=edit').get_data(as_text=True)
    with app.app_context():
        c = db.session.get(Companion,1)
        original_items, original_containers = c.items, c.containers
        item = json.loads(c.items)[0]
    base = '/companions/1/inventory'
    response = client.get(f'{base}/item-edit/{item["id"]}')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'data-tag="bulky"' in html
    assert 'name="edit_item_container"' in html
    assert f'{base}/item-edit/{item["id"]}/save' in html
    data = dict(edit_item_name='Gift', edit_item_tags='uses', edit_item_uses='2',
                edit_item_charges='',edit_item_max_charges='',edit_item_description='Remember me',
                edit_item_container='recipient:character:1|0')
    response = client.post(f'{base}/item-edit/{item["id"]}/save', data=data)
    assert response.status_code == 200 and 'HX-Retarget' not in response.headers
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items)[0]['name'] == 'Gift'
    assert client.post('/companions/1/cancel',data=dict(old_items=original_items,old_containers=original_containers)).status_code == 302
    with app.app_context():
        assert json.loads(db.session.get(Character,1).items) == []
        assert json.loads(db.session.get(Companion,1).items) == json.loads(original_items)
    assert client.get(base+'/container-edit/None?mode=create').status_code == 200
    assert client.post(base+'/container-edit/None/save',data=dict(mode='create',name='Cart',slots=4,carried_by=0,load=1)).status_code == 200
    with app.app_context():
        assert json.loads(db.session.get(Companion,1).containers)[-1]['name'] == 'Cart'
    assert client.post(base+'/container-edit/1/delete',data={'delete-items':''}).status_code == 200


def test_companion_shared_modal_enforces_csrf(world):
    app, clients = world
    app.config['WTF_CSRF_ENABLED'] = True
    path = '/companions/1/inventory/item-edit/None/save?mode=create'
    data = dict(edit_item_name='Tool',edit_item_tags='',edit_item_uses='',edit_item_charges='',
                edit_item_max_charges='',edit_item_description='',edit_item_container='0')
    assert clients[2].post(path,data=data).status_code == 400
    page = clients[2].get('/companions/1/inventory/item-edit/None?mode=create').get_data(as_text=True)
    data['csrf_token'] = re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page)[1]
    assert clients[2].post(path,data=data).status_code == 200


def test_character_edit_keeps_pet_cards_and_links(world):
    _, clients = world
    page = clients[2].get('/charedit/keeper2/hero1').get_data(as_text=True)
    assert 'id="character-pets"' in page
    assert 'href="/companions/2"' in page
    assert 'character-inventory-pets' in page
    # The enclosing character form must not contain nested quick-stat forms.
    assert 'class="companion-stat-form ' not in page


def test_companion_has_one_name_field_and_keeps_its_role_on_save(world):
    app, clients = world
    page = clients[2].get('/companions/1?mode=edit').get_data(as_text=True)
    assert page.count('name="name"') == 1
    assert 'name="role"' not in page
    assert 'companion-notes' in page
    with app.app_context():
        c = db.session.get(Companion,1)
        data = {key:getattr(c,key) for key in ('name','attack','notes','gold','armor','daily_cost',
            'hp','hp_max','strength','strength_max','dexterity','dexterity_max','willpower','willpower_max')}
    data['name'] = 'Renamed Hireling'
    assert clients[2].post('/companions/1', data=data).status_code == 302
    with app.app_context():
        assert db.session.get(Companion,1).role == 'Bodyguard'

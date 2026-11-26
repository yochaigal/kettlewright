"""#529: hirelings start with the Cairn SRD's gear (and pets) and a portrait, and their sheet is laid out like a
character's. #537: a mount carries for its owner: its slots are a container in the owner's inventory, kept in sync."""
import importlib.util
import json

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.lib.companions import catalog, new_hireling
from kettlewright import system
from app.models import Character, Companion, Party, db
from tests.unit.test_companions import world  # noqa: F401  (the fixture)

CONTAINERS = '[{"id":0,"name":"Main","slots":10}]'


def names(record):
    return [item['name'] for item in json.loads(record.items)]


def containers(record):
    return json.loads(record.containers)


# #529: hirelings.

def test_hirelings_start_with_the_srd_s_gear_pets_and_a_portrait(app_with_babel):
    with app_with_babel.app_context():
        expected = {'Alchemist': ['Rations', 'Torch', 'Dagger', 'Acid', 'Lens', 'Gloves'],
                    'Veteran Bodyguard': ['Rations', 'Torch', 'Long Sword', 'Helmet', 'Gambeson'],
                    'Scholar': ['Rations', 'Candle', 'Parchment & Ink', 'Stylus', 'Staff', 'Robes']}
        for role, gear in expected.items():
            assert names(new_hireling(Party(name='Test'), role)) == gear
        veteran = new_hireling(Party(name='Test'), 'Veteran Bodyguard')
        assert veteran.armorValue() == 2  # Helmet and Gambeson, from what it carries: no natural armor.
        handler = new_hireling(Party(name='Test'), 'Animal Handler')
        assert [(pet.name, pet.dexterity, pet.attack) for pet in handler.pets] == [('Hawk', 16, 'Claws (d4+d4)')]
        portraits = {new_hireling(Party(name='Test'), 'Sailor').image_url for _ in range(8)}
        assert None not in portraits and 'default-portrait.webp' not in portraits and len(portraits) > 1
        assert all(any(i['name'] == 'Rations' for i in t['items']) for t in catalog('hireling'))


def test_a_hireling_s_sheet_is_laid_out_like_a_character_s(world):
    app, clients = world
    page = clients[1].get('/companions/1').get_data(as_text=True)
    assert 'class="sheet-layout"' in page and 'class="sheet-side"' in page
    assert 'id="character-armor-container"' in page and 'id="character-gold-container"' in page
    assert 'Natural armor' not in page
    # One that was given natural armor before keeps its control, and a save without it keeps the value.
    with app.app_context():
        db.session.get(Companion, 1).armor = 1
        db.session.commit()
    assert 'Natural armor' in clients[1].get('/companions/1').get_data(as_text=True)
    with app.app_context():
        hireling = db.session.get(Companion, 1)
        form = {'name': hireling.name, 'role': hireling.role, 'attack': '', 'notes': '', 'gold': 0, 'daily_cost': 10,
                **{field: hireling.get_stat(field) for stat in system().stats for field in (stat.key, stat.key + '_max')}}
    assert clients[1].post('/companions/1', data=form).status_code == 302
    with app.app_context():
        assert db.session.get(Companion, 1).armor == 1


# #537: mounts.

def add_pet(client, template, carries=True):
    return client.post('/characters/1/pets/add', data={'template': template, 'name': '',
                                                       **({'carries': 'on'} if carries else {})})


def test_a_horse_added_to_carry_is_a_container_of_its_owner(world):
    app, clients = world
    assert add_pet(clients[2], 'Horse').status_code == 302
    assert add_pet(clients[2], 'Mule', carries=False).status_code == 302
    assert add_pet(clients[2], 'Raven Familiar').status_code == 302  # Can't carry: no container, whatever is asked.
    with app.app_context():
        hero = db.session.get(Character, 1)
        horse, mule = (Companion.query.filter_by(character_id=1, name=name).one() for name in ('Horse', 'Mule'))
        assert [(c['name'], c['slots'], c.get('mount')) for c in containers(hero)[1:]] == [('Horse', 4, horse.id)]
        assert containers(horse)[0]['slots'] == 0 and containers(mule)[0]['slots'] == 6
        horse_id = horse.id
    page = clients[2].get(f'/companions/{horse_id}').get_data(as_text=True)
    assert 'Carries for Hero1: Horse, 4 slots.' in page and '/users/keeper2/characters/hero1/' in page
    page = clients[2].get('/characters/1/pets/add').get_data(as_text=True)
    assert 'name="carries"' in page and '&#34;Horse&#34;: 4' in page and 'Raven Familiar&#34;' not in page.split('slots: ')[1][:400]


def test_a_mount_and_its_container_stay_in_sync(world):
    from app.lib.inventory import Inventory
    from app.lib.mounts import mount_container, pet_removed
    app, clients = world
    add_pet(clients[2], 'Horse')
    with app.app_context():
        horse = Companion.query.filter_by(character_id=1, name='Horse').one()
        horse_id, box = horse.id, mount_container(horse)['id']
    # Renaming the pet renames its container, and the other way round.
    assert clients[2].post(f'/companions/{horse_id}/section/name', data={'name': 'Clover'}).status_code == 200
    with app.app_context():
        assert containers(db.session.get(Character, 1))[1]['name'] == 'Clover'
        Inventory(db.session.get(Character, 1)).update_container(box, 'Old Clover', 4, None, None)
        assert db.session.get(Companion, horse_id).name == 'Old Clover'
        # Removing the container leaves a plain pet with its slots back.
        Inventory(db.session.get(Character, 1)).delete_container(box, 0)
        assert containers(db.session.get(Companion, horse_id))[0]['slots'] == 4
        assert mount_container(db.session.get(Companion, horse_id)) is None
    # A mount that goes takes its container, and what it carried goes to the main inventory.
    add_pet(clients[2], 'Mule')
    with app.app_context():
        mule = Companion.query.filter_by(character_id=1, name='Mule').one()
        hero = db.session.get(Character, 1)
        box = mount_container(mule)['id']
        hero.items = json.dumps([{'id': 9, 'name': 'Saddlebag', 'tags': [], 'location': box}])
        db.session.commit()
        mule_id = mule.id
    assert clients[2].post(f'/companions/{mule_id}/delete').status_code == 302
    with app.app_context():
        hero = db.session.get(Character, 1)
        assert [c['name'] for c in containers(hero)] == ['Main']
        assert [(i['name'], i['location']) for i in json.loads(hero.items)] == [('Saddlebag', 0)]


def test_an_outrider_s_mount_carries_its_background_container(world):
    from app.lib.companions import import_pet, pet_data
    from app.lib.mounts import link_mounts, mount_container
    app, _ = world
    with app.app_context():
        hero = db.session.get(Character, 2)
        hero.containers = json.dumps([{'id': 0, 'name': 'Main', 'slots': 10}, {'id': 1, 'name': 'Stray Fogger', 'slots': 2},
                                      {'id': 2, 'name': 'Horse', 'slots': 4, 'mount': 999}])  # A link to another site's pet.
        hero.pets.append(import_pet(pet_data(catalog('pet')['Stray Fogger'], hero)))
        link_mounts(hero)
        db.session.commit()
        fogger = Companion.query.filter_by(character_id=2, name='Stray Fogger').one()
        assert mount_container(fogger)['id'] == 1 and containers(fogger)[0]['slots'] == 0
        assert 'mount' not in containers(hero)[2]


def test_the_migration_links_existing_outriders_mounts():
    spec = importlib.util.spec_from_file_location('m537', 'migrations/versions/537a01_mounts_carry.py')
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.exec_driver_sql('create table characters (id integer primary key, containers text)')
        connection.exec_driver_sql('create table companions (id integer primary key, kind text, name text, '
                                   'character_id integer, hireling_id integer, items text, containers text)')
        hero = [{'id': 0, 'name': 'Main', 'slots': 10}, {'id': 1, 'name': 'Linden White', 'slots': 3}]
        connection.exec_driver_sql('insert into characters values (1, ?)', (json.dumps(hero),))
        pet = lambda i, name, items, slots: connection.exec_driver_sql(
            'insert into companions values (?, ?, ?, 1, null, ?, ?)',
            (i, 'pet', name, json.dumps(items), json.dumps([{'id': 0, 'name': 'Main', 'slots': slots}])))
        pet(5, 'Linden White', [], 3)
        pet(6, 'Carrion Cat', [], 0)  # Carries nothing.
        stored = lambda: (json.loads(connection.exec_driver_sql('select containers from characters').scalar()),
                          {i: json.loads(c) for i, c in connection.exec_driver_sql('select id, containers from companions')})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            owner, pets = stored()
            assert owner[1] == {'id': 1, 'name': 'Linden White', 'slots': 3, 'mount': 5} and pets[5][0]['slots'] == 0
            assert pets[6][0]['slots'] == 0 and 'mount' not in owner[0]
            migration.downgrade()
            owner, pets = stored()
            assert owner == hero and pets[5][0]['slots'] == 3

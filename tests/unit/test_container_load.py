import json

import pytest

from app.lib.inventory import Inventory
from app.models import Character, Party, Companion, User, db


@pytest.mark.parametrize('model', [Character, Party, Companion])
def test_container_edits_replace_load_and_preserve_contents(app_with_babel, model):
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='owner'))
        db.session.flush()
        values = dict(name='Inventory', items='[]', containers=json.dumps([
            dict(id=0, name='Main', slots=10), dict(id=1, name='Cart', slots=20)]))
        if model is Character:
            values.update(owner=1, background='Test')
        elif model is Party:
            values.update(owner=1)
        else:
            parent = Character(owner=1, name='Owner', background='Test', items='[]', containers='[]')
            db.session.add(parent)
            db.session.flush()
            values.update(character_id=parent.id, kind='pet')
        owner = model(**values)
        db.session.add(owner)
        db.session.commit()
        inventory = Inventory(owner)
        bag_id = inventory.add_container('Bag', 8, '0', '2')
        content = dict(id='rope', name='Rope', location=bag_id, tags=[], description='Keep me')
        other = dict(id='other', name='Other load', location=0, tags=[], carrying=1)
        items = json.loads(owner.items) + [content, other]
        # Simulate a reservation duplicated by an older version.
        items.append(dict(items[0], id='stale'))
        owner.items = json.dumps(items)
        db.session.commit()
        inventory.parse(owner)
        for parent, load in [('0', '3'), ('0', '1'), ('1', '2'), ('1', '2'), ('1', '0'), ('', '')]:
            inventory.update_container(str(bag_id), 'Renamed bag', 9, parent, load)
            items = json.loads(owner.items)
            reservations = [it for it in items if it.get('carrying') == bag_id]
            assert len(reservations) == int(load or 0)
            assert all(it['location'] == int(parent) and it['name'] == 'Carrying Renamed bag'
                       for it in reservations)
            assert content in items and other in items
            bag = inventory.get_container(bag_id)
            if int(load or 0):
                assert bag['carried_by'] == parent and bag['load'] == load
            else:
                assert 'carried_by' not in bag and 'load' not in bag

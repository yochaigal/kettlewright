"""Give to party (#476): items to the party's storage, creatures to its monsters."""
import json
import re

from app.models import db, Party, Companion
from tests.helpers import login
from tests.unit.test_campaigns import setup, create_entry  # noqa: F401 (fixture)


def party_items(app, party_id=1):
    with app.app_context():
        return json.loads(db.session.get(Party, party_id).items)


def test_a_relic_goes_to_party_storage(setup):
    app, client = setup
    entry_id = create_entry(client, category='relic', title='Mud Sieve', body='Shapes mud like water. 3 charges.')
    page = client.get(f'/campaigns/1/wiki/{entry_id}/').get_data(as_text=True)
    assert 'Give to party' in page and f'action="/materials/{entry_id}/give"' in page
    response = client.post(f'/materials/{entry_id}/give', data={'party_id': 1})
    assert response.status_code == 302
    [item] = party_items(app)
    assert item['name'] == 'Mud Sieve' and 'Shapes mud like water' in item['description']
    assert item['location'] == 0
    # The article stays in its module, private.
    login(client, 2)
    assert client.get('/party/1/materials/data').json['entries'] == []


def test_a_creature_becomes_a_party_monster(setup):
    app, client = setup
    with_stats = create_entry(client, category='bestiary', title='Cave Bear',
                              body='Huge and hungry.\n\n12 HP, 1 Armor, 16 STR, 10 DEX, 6 WIL, claws (d8)')
    plain = create_entry(client, category='bestiary', title='Olms', body='Peaceful, blind cave dwellers.')
    assert client.post(f'/materials/{with_stats}/give', data={'party_id': 1}).status_code == 302
    assert client.post(f'/materials/{plain}/give', data={'party_id': 1}).status_code == 302
    with app.app_context():
        bear, olm = Companion.query.filter_by(kind='monster', party_id=1).order_by(Companion.id).all()
        assert (bear.name, bear.hp, bear.armor, bear.strength) == ('Cave Bear', 12, 1, 16)
        assert 'claws (d8)' in bear.attack
        assert (olm.name, olm.hp) == ('Olms', 3) and 'blind cave dwellers' in olm.notes


def test_only_usable_articles_and_own_campaign_parties(setup):
    app, client = setup
    npc = create_entry(client)  # An NPC: only revealed, never given.
    assert 'Give to party' not in client.get(f'/campaigns/1/wiki/{npc}/').get_data(as_text=True)
    assert client.post(f'/materials/{npc}/give', data={'party_id': 1}).status_code == 400
    relic = create_entry(client, category='relic', title='Relic')
    assert client.post(f'/materials/{relic}/give', data={'party_id': 2}).status_code == 403  # Not in this campaign.
    assert client.post(f'/materials/{relic}/give', data={'party_id': 3}).status_code == 403  # Someone else's.
    login(client, 2)
    assert client.post(f'/materials/{relic}/give', data={'party_id': 1}).status_code in (403, 404)
    assert party_items(app) == []


def test_full_storage_is_reported(setup):
    app, client = setup
    with app.app_context():
        party = db.session.get(Party, 1)
        party.containers = json.dumps([{'id': 0, 'name': 'Main', 'slots': 1}])
        party.items = json.dumps([{'id': '1', 'name': 'Rope', 'tags': [], 'location': 0, 'description': ''}])
        db.session.commit()
    relic = create_entry(client, category='relic', title='Relic')
    response = client.post(f'/materials/{relic}/give', data={'party_id': 1}, follow_redirects=True)
    assert 'no room in its storage' in response.get_data(as_text=True)
    assert len(party_items(app)) == 1

"""#543: the Warden rolls a character's quick rolls on the whiteboard. #544: the party page shows HP that counts."""
import json

from app.models import Character, db
from tests.unit.test_shared_map import shared  # noqa: F401  (the fixture)


def test_the_warden_rolls_for_a_party_member_s_character(shared):
    app, clients, _ = shared
    with app.app_context():
        hero = db.session.get(Character, 1)
        hero.strength, hero.strength_max = 9, 12
        db.session.commit()
    roll = {'character_id': 1, 'dice': 'd8'}
    assert clients[1].post('/party/1/shared-map/roll', data=roll).status_code == 200  # The Warden.
    assert clients[2].post('/party/1/shared-map/roll', data=roll).status_code == 200  # Its player.
    assert clients[3].post('/party/1/shared-map/roll', data=roll).status_code == 403  # Another member.
    save = {'character_id': 1, 'dice': 'd20', 'save': 'strength'}
    response = clients[1].post('/party/1/shared-map/roll', data=save)
    assert response.status_code == 200 and 'STR 9' in response.get_json()['result']
    from app.models import PartyRoll
    with app.app_context():
        assert {roll.character_name for roll in PartyRoll.query} == {'Player'}  # Rolled as the character.


def test_the_party_page_shows_the_hp_that_counts(shared):
    app, clients, _ = shared
    full = [{'id': i, 'name': f'Rock {i}', 'tags': [], 'location': 0} for i in range(10)]
    with app.app_context():
        hero = db.session.get(Character, 1)
        hero.owner_username, hero.url_name = 'map2', 'player'
        hero.hp, hero.hp_max, hero.gold = 6, 6, 0
        hero.items, hero.containers = json.dumps(full), '[{"id": 0, "name": "Main", "slots": 10}]'
        for stat in ('strength', 'dexterity', 'willpower'):
            setattr(hero, stat, 10), setattr(hero, stat + '_max', 10)
        from app.models import Party
        db.session.get(Party, 1).containers = '[{"id": 0, "name": "Stash", "slots": 10}]'
        db.session.commit()
    page = clients[1].get('/users/map1/parties/party/').get_data(as_text=True)  # The Warden: the stored HP to edit.
    members = page[page.index('party-member-stats'):]
    assert 'value="6"' in members and 'Available HP: 0' in members
    with app.app_context():  # With room in the inventory, nothing to say.
        db.session.get(Character, 1).items = json.dumps(full[:5])
        db.session.commit()
    assert 'Available HP: 0' not in clients[1].get('/users/map1/parties/party/').get_data(as_text=True)

"""#543: the Warden rolls a character's quick rolls on the whiteboard."""
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


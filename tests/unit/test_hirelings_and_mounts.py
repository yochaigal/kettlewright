"""#529: hirelings start with the Cairn SRD's gear (and pets) and a portrait, and their sheet is laid out like a
character's."""
import json

from app.lib.companions import catalog, new_hireling
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
                **{field: hireling.get_stat(field) for stat in hireling.rules.stats for field in (stat.key, stat.key + '_max')}}
    assert clients[1].post('/companions/1', data=form).status_code == 302
    with app.app_context():
        assert db.session.get(Companion, 1).armor == 1

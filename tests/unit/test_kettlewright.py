"""The Kettlewright engine (kettlewright/, #487): Cairn's rules as the app had them, and room for another system."""
import subprocess
import sys
from dataclasses import dataclass

import pytest

from kettlewright import SYSTEMS, Condition, GameSystem, Inventory, Stat, register, system


def item(*tags, location=0, **extra):
    return dict(tags=list(tags), location=location, **extra)


def test_cairn_is_the_default_with_its_stats_conditions_and_saves():
    cairn = system()
    assert cairn is system('cairn') and cairn.name == 'Cairn'
    assert cairn.stat_keys == ('hp', 'strength', 'dexterity', 'willpower')
    assert [stat.key for stat in cairn.sheet_stats] == ['strength', 'dexterity', 'willpower', 'hp']
    assert cairn.save_keys == cairn.attribute_keys == ('strength', 'dexterity', 'willpower')
    assert [cairn.abbr(key) for key in cairn.stat_keys] == ['HP', 'STR', 'DEX', 'WIL']
    assert cairn.condition_keys == ('deprived', 'panicked', 'dead')
    # A save is a d20 under the attribute's current value.
    assert cairn.save_die == 20 and cairn.save_succeeds(12, 12) and not cairn.save_succeeds(13, 12)
    with pytest.raises(KeyError):
        system('no-such-system')


def test_cairn_inventory_slots_and_coins():
    inventory = system().inventory
    assert [inventory.item_size(item(*tags)) for tags in ((), ('bulky',), ('petty',), ('petty', 'bulky'))] == [1, 2, 0, 0]
    carried = [item(), item('bulky'), item('petty'), item(location=1)]
    assert inventory.occupied_main_slots(carried) == 3
    # Coins worth 100gp or more take one slot (#507).
    assert [inventory.occupied_main_slots(carried, gold) for gold in (None, 99, 100, 5000)] == [3, 3, 4, 4]
    assert inventory.main_capacity([{'id': 1, 'slots': 4}, {'id': 0, 'slots': '12'}]) == 12
    assert inventory.main_capacity([]) == 10
    assert inventory.default_containers() == [{'name': 'Main', 'slots': 10, 'id': 0}]


def test_cairn_armor_and_effective_hp():
    cairn = system()
    assert cairn.armor_value([item('1 Armor'), item('2 Armor')]) == 3  # Never above 3.
    assert cairn.armor_value([item('2 Armor', location=1)]) == 0  # Only what is carried in the main inventory.
    assert cairn.armor_value([item('1 Armor', name='Sloth-Tarp')]) == 0  # Old Sloth-Tarps need activating.
    assert cairn.armor_value([item('1 Armor', name='Sloth-Tarp', armor_active=True)]) == 1
    assert cairn.armor_value([item('1 Armor')], base=1) == 2  # A creature's own armor counts too.
    # A full inventory or Panicked: 0 HP.
    assert [cairn.effective_hp(4, slots, ()) for slots in (9, 10, 12)] == [4, 0, 0]
    assert cairn.effective_hp(4, 0, ('panicked',)) == 0 and cairn.effective_hp(4, 0, ('deprived',)) == 4


def test_another_system_plugs_in_with_its_own_stats_and_rules():
    @dataclass(frozen=True)
    class RollOver(GameSystem):
        """A made-up system: four abilities, saves roll over, no slots, no armor cap."""
        key: str = 'roll-over'
        name: str = 'Roll Over'
        hit_points: Stat = Stat('hp', 'HP', 'Hit Points')
        attributes: tuple = tuple(Stat(key, key[:3].upper(), key.title(), save=key != 'luck')
                                  for key in ('strength', 'agility', 'presence', 'luck'))
        conditions: tuple = (Condition('poisoned', 'Poisoned'),)
        inventory: Inventory = Inventory(main_slots=20)

        def save_succeeds(self, roll, score):
            return roll >= score

    rules = register(RollOver())
    try:
        assert system('roll-over') is rules and system() is system('cairn')  # Cairn stays the default.
        assert rules.save_keys == ('strength', 'agility', 'presence') and rules.abbr('presence') == 'PRE'
        assert rules.save_succeeds(15, 12) and not rules.save_succeeds(3, 12)
        assert rules.inventory.item_size(item('bulky')) == 1  # No sizes: every item takes one slot.
        assert rules.armor_value([]) == 0 and rules.effective_hp(5, 99, ('poisoned',)) == 5
    finally:
        SYSTEMS.pop('roll-over', None)


def test_the_engine_stands_alone_without_flask_or_the_database():
    code = 'import sys, kettlewright; kettlewright.system(); print(sorted(m for m in ("flask", "sqlalchemy", "app") if m in sys.modules))'
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True).stdout
    assert out.strip() == '[]'


def test_the_app_reads_cairn_s_rules_from_the_engine():
    """The sheet, rolls, monsters and Discord use the engine's lists instead of their own copies."""
    from app.lib import character_markdown, character_rolls, companions, discord_character, inventory_slots
    assert character_rolls.SAVES == {'strength': 'STR', 'dexterity': 'DEX', 'willpower': 'WIL'}
    assert character_markdown.STATS == (('strength', 'STR'), ('dexterity', 'DEX'), ('willpower', 'WIL'), ('hp', 'HP'))
    assert character_markdown.CONDITIONS == (('deprived', 'Deprived'), ('panicked', 'Panicked'), ('dead', 'Dead'))
    assert companions.STATS == ('hp', 'strength', 'dexterity', 'willpower')
    assert discord_character.STATS == {'hp': 'hp', 'str': 'strength', 'dex': 'dexterity', 'wil': 'willpower'}
    assert inventory_slots.PETTY_GOLD_LIMIT == 100 and inventory_slots.item_size(item('bulky')) == 2


# Step 2: character creation from the system: its dice and its tables.

def test_cairn_creation_dice_and_tables():
    import os
    cairn = system()
    assert [(stat.key, stat.dice) for stat in cairn.sheet_stats] == [
        ('strength', '3d6'), ('dexterity', '3d6'), ('willpower', '3d6'), ('hp', 'd6')]
    rolls = [cairn.roll_stat('strength') for _ in range(300)]
    assert min(rolls) >= 3 and max(rolls) <= 18 and len(set(rolls)) > 8
    assert {cairn.roll_stat('hp') for _ in range(200)} == {1, 2, 3, 4, 5, 6}
    for name in ('backgrounds', 'traits', 'bonds', 'omens', 'scars'):
        assert cairn.content.path(name).is_file() and os.sep + os.path.join('systems', 'cairn', 'content') in str(cairn.content_path(name)), name


def test_barebones_and_2e_creation_roll_with_the_system_s_dice():
    from app.blueprints.charcreo_barebones import ATTRIBUTES
    assert ATTRIBUTES == {'str': ('strength', 6, 3), 'dex': ('dexterity', 6, 3), 'wil': ('willpower', 6, 3), 'hp': ('hp', 6, 1)}


def test_2e_creation_rolls_and_swaps_attributes(app_with_babel):
    from app.models import User, db
    from tests.helpers import login
    from tests.unit.test_background_reroll import FormValues
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='creator'))
        db.session.commit()
    client = login(app_with_babel.test_client(), 1)
    values = FormValues(client.post('/charcreo/select-background', data={
        'background': 'Mountebank', 'items': '[]', 'containers': '[{"name": "Main", "slots": 10, "id": 0}]'}).text).values
    field = lambda html, key: int(re.search(rf'id="{key}-max-field"[^>]*value="(\d+)"', html).group(1))
    import re
    for short, key, low, high in (('str', 'strength', 3, 18), ('hp', 'hp', 1, 6)):
        assert low <= field(client.post(f'/charcreo/attr-roll/{short}', data=values).text, key) <= high
    swapped = client.post('/charcreo/attr-swap', data=dict(values, strength_max='5', dexterity_max='15',
                          swap_attribute_1='str', swap_attribute_2='dex')).text
    assert (field(swapped, 'strength'), field(swapped, 'dexterity')) == (15, 5)
    # HP can't be swapped, and an attribute with itself does nothing.
    for first, second in (('str', 'hp'), ('dex', 'dex')):
        same = client.post('/charcreo/attr-swap', data=dict(values, strength_max='5', dexterity_max='15', hp_max='4',
                           swap_attribute_1=first, swap_attribute_2=second)).text
        assert (field(same, 'strength'), field(same, 'dexterity'), field(same, 'hp')) == (5, 15, 4)


# Step 3: one slot rule everywhere: a petty item takes no slot, even if it is also bulky.

def test_petty_and_bulky_takes_no_slot_everywhere():
    from app.lib.barebones import slots_used
    from app.lib.char_utils import GeneratedCharacter
    odd = [item('petty', 'bulky'), item('bulky'), item()]
    assert slots_used(odd) == 3
    generated = GeneratedCharacter()
    generated.items = odd
    assert generated.used_slots() == 3


# Step 1: templates and scripts read the system.

def test_pages_get_the_game_system_for_their_scripts(app_with_babel):
    import json
    page = app_with_babel.test_client().get('/login').get_data(as_text=True)
    data = json.loads(page.split('<script id="game-system" type="application/json">', 1)[1].split('</script>', 1)[0])
    assert data['key'] == 'cairn' and data['hp'] == {'key': 'hp', 'abbr': 'HP', 'label': 'HP'}
    assert [(a['key'], a['abbr'], a['save']) for a in data['attributes']] == [
        ('strength', 'STR', True), ('dexterity', 'DEX', True), ('willpower', 'WIL', True)]
    assert [c['key'] for c in data['conditions']] == ['deprived', 'panicked', 'dead']


# Steps 4 and 5: a campaign plays a system, and a stat without a column is stored in system_stats.

@dataclass(frozen=True)
class Lucky(GameSystem):
    """Cairn's stats plus Luck, which has no column; saves roll over."""
    key: str = 'lucky'
    name: str = 'Lucky'
    hit_points: Stat = Stat('hp', 'HP', 'Hit Points', roll=(1, 6))
    attributes: tuple = (Stat('strength', 'STR', 'Strength', save=True, roll=(3, 6)),
                         Stat('luck', 'LCK', 'Luck', save=True, roll=(2, 6)))
    conditions: tuple = (Condition('deprived', 'Deprived'),)

    def save_succeeds(self, roll, score):
        return roll >= score


@pytest.fixture
def lucky_campaign(app_with_babel):
    """user 1 runs a Lucky campaign whose party has user 2's character Ada (STR 10/10, Luck 7/9).

    Nothing in the app offers another system: code creates them with it, and from then on it is fixed."""
    import json
    from app.lib.campaign_parties import create_campaign
    from app.models import Character, User, db
    register(Lucky())
    app = app_with_babel
    with app.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='player')])
        db.session.flush()
        party = create_campaign(1, 'Lucky Roads', game_system='lucky').parties[0]
        db.session.flush()
        ada = Character(owner=2, owner_username='player', name='Ada', url_name='ada', party_id=party.id,
                        game_system='lucky', background='Custom', edition='2e', strength=10, strength_max=10,
                        hp=4, hp_max=4, gold=0, deprived=False, panicked=False, dead=False, items='[]',
                        containers='[{"id": 0, "name": "Main", "slots": 10}]')
        ada.set_stat('luck', 7)
        ada.set_stat('luck_max', 9)
        db.session.add(ada)
        db.session.flush()
        party.members = json.dumps([ada.id])
        db.session.commit()
        ids = party.id, ada.id
    yield app, ids
    SYSTEMS.pop('lucky', None)


def test_campaigns_parties_and_characters_keep_the_system_they_were_created_with(lucky_campaign):
    from app.lib.campaign_parties import create_party
    from app.models import Campaign, Character, GameSystemChanged, Party, db
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        party, ada = db.session.get(Party, party_id), db.session.get(Character, ada_id)
        campaign = party.campaign
        assert campaign.rules is party.rules is ada.rules is system('lucky')
        assert ada.system_stats == '{"luck": 7, "luck_max": 9}' and ada.get_stat('luck') == 7
        assert ada.stat_values() == {'hp': [4, 4], 'strength': [10, 10], 'luck': [7, 9]}
        # A new party of the campaign plays its system.
        assert create_party(campaign, 'Second Table').game_system == 'lucky'
        db.session.rollback()
        # A party that leaves its campaign keeps its system; so does a character that leaves its party.
        party.campaign = None
        ada.party_id = None
        db.session.flush()
        assert party.rules is ada.rules is system('lucky')
        db.session.rollback()
        # Once created, the system can't change.
        for row in (db.session.get(Campaign, campaign.id), db.session.get(Party, party_id), db.session.get(Character, ada_id)):
            row.game_system = 'cairn'
            with pytest.raises(GameSystemChanged):
                db.session.flush()
            db.session.rollback()
        # A key that is no longer registered falls back to the default system.
        assert Campaign(game_system='gone').rules is system()


def test_a_party_only_joins_a_campaign_of_its_own_system(lucky_campaign):
    from app.lib.campaign_parties import create_campaign, create_party
    from app.models import Party, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        cairn = create_campaign(1, 'Plain Roads', with_party=False)
        loose = create_party(None, 'Loose Ends', owner_id=1)
        db.session.commit()
        cairn_id, loose_id = cairn.id, loose.id
        assert loose.game_system == 'cairn'
    warden = login(app.test_client(), 1)
    # The Lucky party can't move to a Cairn campaign, by any of the three ways a party joins one.
    assert warden.post(f'/campaigns/{cairn_id}/parties/add', data={'party_id': party_id}).status_code == 400
    assert warden.post(f'/party/{party_id}/campaign', data={'campaign_id': cairn_id}).status_code == 400
    with app.app_context():
        party = db.session.get(Party, party_id)
        url = f'/party/edit/warden/{party.party_url}/save'
    assert warden.post(url, data={'name': 'Lucky Roads', 'description': '', 'campaign_id': cairn_id}).status_code == 400
    # A Cairn party can.
    assert warden.post(f'/party/{loose_id}/campaign', data={'campaign_id': cairn_id}).status_code == 302
    with app.app_context():
        assert db.session.get(Party, party_id).campaign_id != cairn_id
        assert db.session.get(Party, loose_id).campaign_id == cairn_id


def test_a_character_only_joins_a_party_of_its_own_system(lucky_campaign):
    import json
    from app.lib import add_character_to_party
    from app.models import Character, Party, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        party = db.session.get(Party, party_id)
        code = party.join_code
        db.session.add(Character(id=50, owner=2, owner_username='player', name='Old Hand', url_name='old-hand',
                                 background='Aurifex', items='[]', containers='[{"id": 0, "name": "Main", "slots": 10}]'))
        db.session.commit()
        hand = db.session.get(Character, 50)
        assert hand.game_system == 'cairn'
        hand.party_id = party_id
        with pytest.raises(ValueError):
            add_character_to_party(hand)
        db.session.rollback()
    # Joining with the code: the Lucky party is no party for a Cairn character.
    player = login(app.test_client(), 2)
    player.post('/charedit/player/old-hand/section/party', data={'party_code': code})
    with app.app_context():
        assert db.session.get(Character, 50).party_id is None
        assert json.loads(db.session.get(Party, party_id).members) == [ada_id]
    # A character created for the party plays its system.
    form = {'party_code': code, 'name': 'Rook', 'background': '1', 'strength': '10', 'dexterity': '10',
            'willpower': '10', 'hp': '4', 'gold': '5', 'age': '20'}
    assert player.post('/charcreo/barebones/save', data=form).headers.get('HX-Redirect')
    with app.app_context():
        rook = Character.query.filter_by(name='Rook').one()
        assert rook.game_system == 'lucky' and rook.party_id == party_id


def test_a_stat_without_a_column_is_shown_saved_and_rolled(lucky_campaign):
    from app.models import Character, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    warden, player = login(app.test_client(), 1), login(app.test_client(), 2)
    actors = player.get(f'/party/{party_id}/shared-map/roll-actors').json['actors']
    assert actors[0]['attributes'] == {'strength': [10, 10], 'luck': [7, 9]}
    assert warden.post(f'/party/{party_id}/members/{ada_id}/stat', data={'stat': 'luck', 'value': '8'}).status_code == 204
    assert warden.post(f'/party/{party_id}/members/{ada_id}/stat', data={'stat': 'luck', 'value': '10'}).status_code == 400
    # Cairn's WIL isn't one of this system's stats.
    assert warden.post(f'/party/{party_id}/members/{ada_id}/stat', data={'stat': 'willpower', 'value': '1'}).status_code == 400
    with app.app_context():
        assert db.session.get(Character, ada_id).get_stat('luck') == 8
    stats = {a['id']: a for a in warden.get(f'/party/{party_id}/shared-map/stats').json['actors']}
    assert stats[str(ada_id)]['stats']['luck'] == [8, 9]
    # A Luck save: a d20 against 8, rolled over in this system.
    roll = player.post(f'/party/{party_id}/shared-map/roll', data={'character_id': ada_id, 'dice': 'd20', 'save': 'luck'}).json
    die = roll['values'][0]
    assert f'LCK 8 · {"Success" if die >= 8 else "Failure"}' in roll['result']


def test_the_app_offers_no_choice_of_system(app_with_babel):
    """Systems are internal (#487): New campaign has no choice, and a posted system is ignored."""
    from app.models import Campaign, User, db
    from tests.helpers import login
    app = app_with_babel
    with app.app_context():
        db.session.add(User(id=1, username='warden'))
        db.session.commit()
    client = login(app.test_client(), 1)
    register(Lucky())
    try:
        page = client.get('/campaigns/').get_data(as_text=True)
        assert 'game_system' not in page and 'Lucky' not in page
        assert client.post('/campaigns/', data={'name': 'Lucky Roads', 'game_system': 'lucky'}).status_code == 302
        with app.app_context():
            campaign = Campaign.query.one()
            assert campaign.game_system == 'cairn' and campaign.parties[0].game_system == 'cairn'
    finally:
        SYSTEMS.pop('lucky', None)


def test_migrations_add_system_stats_and_the_campaign_s_system():
    import pathlib
    versions = pathlib.Path('migrations/versions')
    stats, campaign = (versions / '487a01_system_stats.py').read_text(), (versions / '487a02_campaign_system.py').read_text()
    assert "down_revision = '514a01'" in stats and "server_default='{}'" in stats and 'drop_column' in stats
    assert "down_revision = '487a01'" in campaign and "server_default='cairn'" in campaign and 'drop_column' in campaign
    assert "TABLES = ('campaigns', 'parties', 'characters')" in campaign


# The systems live outside the engine's core (systems/), and each record follows its own.

def test_the_core_has_no_system_and_finds_them_in_the_systems_package():
    import pathlib
    for path in pathlib.Path('kettlewright').glob('*.py'):
        code = path.read_text()
        assert 'import cairn' not in code and 'systems.cairn' not in code and "'cairn'" not in code, path
    code = ('import sys, kettlewright; before = "systems.cairn" in sys.modules; kettlewright.system(); '
            'print(before, "systems.cairn" in sys.modules, kettlewright.default_key())')
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True).stdout.split()
    assert out == ['False', 'True', 'cairn']  # Loaded on first use; the systems package names the default.
    from systems.cairn import CAIRN
    assert system('cairn') is CAIRN and CAIRN.fatigue == 'Fatigue' and '1 Armor' in CAIRN.item_tags
    assert [field for field, _ in CAIRN.sheet_sections] == ['description', 'traits', 'bonds', 'omens', 'scars', 'notes']
    assert CAIRN.can_recover(()) and not CAIRN.can_recover(('deprived',))


def test_a_character_s_pages_forms_and_exports_follow_its_system(lucky_campaign):
    from app.lib.character_markdown import render_character
    from app.lib.discord_character import stat_field
    from app.lib.monsters import parse_monster
    from app.lib.system_forms import stat_fields, with_system_stats
    from app.forms import CharacterEditForm
    from app.models import Character, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        ada = db.session.get(Character, ada_id)
        # A stat without a column reads like one, in code and in templates.
        assert (ada.luck, ada.luck_max) == (7, 9) and ada.stat_values()['luck'] == [7, 9]
        with pytest.raises(AttributeError):
            ada.charisma
        assert stat_fields(ada.rules) == ['strength_max', 'strength', 'luck_max', 'luck', 'hp_max', 'hp']
        form = with_system_stats(CharacterEditForm, ada.rules)
        assert hasattr(form, 'luck') and hasattr(form, 'luck_max') and with_system_stats(CharacterEditForm, system()) is CharacterEditForm
        text = render_character(ada.export_data(), markdown=False)
        assert 'STR 10/10 · LCK 7/9 · HP 4/4' in text and 'DEX' not in text
        assert ada.export_data()['luck'] == 7
        assert stat_field(ada, 'lck') == 'luck' and stat_field(ada, 'dex') is None
        monster = parse_monster('# Imp\n4 HP, 12 STR, 15 LCK, claws (d6)', rules=ada.rules)
        assert (monster['luck'], monster['strength'], monster['attack']) == (15, 12, 'claws (d6)')
        assert 'dexterity' not in monster
    player = login(app.test_client(), 2)
    page = player.get('/users/player/characters/ada/').get_data(as_text=True)
    assert 'id="character-lck-container"' in page and 'id="character-dex-container"' not in page


def test_party_members_hirelings_fatigue_and_rest_follow_the_system(lucky_campaign):
    import json
    from app.lib.companions import new_hireling
    from app.lib.inventory import Inventory
    from app.lib.wilderness import rest
    from app.models import Character, Party, db
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        party, ada = db.session.get(Party, party_id), db.session.get(Character, ada_id)
        hireling = new_hireling(party, 'Custom')
        assert hireling.rules is party.rules and 2 <= hireling.get_stat('luck') <= 12
        assert hireling.get_stat('luck') == hireling.get_stat('luck_max') and json.loads(hireling.system_stats)['luck']
        inventory = Inventory(ada)
        assert inventory.rules is ada.rules
        inventory.add_fatigue(0)
        assert json.loads(ada.items) == []  # Lucky has no Fatigue.
        # Rest: Cairn's Deprived characters recover nothing; Lucky's do.
        ada.hp, ada.deprived = 1, True
        assert rest([ada])['restored'] == [('Ada', 1, 4)] and ada.hp == 4
        db.session.rollback()


def test_cairn_fatigue_and_rest_are_cairn_s(app_with_babel):
    import json
    from app.lib.campaign_parties import create_campaign
    from app.lib.inventory import Inventory
    from app.lib.wilderness import rest
    from app.models import Character, User, db
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='warden'))
        db.session.flush()
        party = create_campaign(1, 'Plain Roads').parties[0]
        db.session.flush()
        hand = Character(owner=1, owner_username='warden', name='Hand', url_name='hand', party_id=party.id,
                         background='Custom', hp=1, hp_max=4, deprived=True, items='[]',
                         containers='[{"id": 0, "name": "Main", "slots": 10}]')
        db.session.add(hand)
        db.session.commit()
        Inventory(hand).add_fatigue(0)
        assert [item['name'] for item in json.loads(hand.items)] == ['Fatigue']
        assert rest([hand]) == dict(restored=[], already_full=[], deprived=['Hand']) and hand.hp == 1


# Gaps found reviewing the tests: defaults, the registry, storage edge cases, and every place a second system
# meets content or code written for Cairn.

def test_game_system_defaults_are_the_plainest_rules():
    plain = GameSystem(key='plain', name='Plain', hit_points=Stat('hp', 'HP', 'Hit Points'))
    assert plain.hit_points.dice == '' and plain.inventory.item_size(item('bulky')) == 1
    assert plain.item_armor(item('3 Armor')) == 0 and plain.armor_value([item('3 Armor')], base=7) == 7  # No cap.
    assert plain.effective_hp(4, 99, ('panicked',)) == 4 and plain.can_recover(('deprived',))
    assert plain.fatigue is None and plain.save_succeeds(5, 5) and not plain.save_succeeds(6, 5)
    assert plain.inventory.occupied_main_slots([item()], gold=10**6) == 1  # Coins never take a slot.


def test_the_registry_refuses_an_unknown_default_and_loads_other_packages(tmp_path):
    from kettlewright import set_default
    with pytest.raises(KeyError):
        set_default('no-such-system')
    package = tmp_path / 'more_systems'
    package.mkdir()
    (package / '__init__.py').write_text(
        'from dataclasses import dataclass\n'
        'from kettlewright import GameSystem, Stat, register\n'
        '@dataclass(frozen=True)\n'
        'class Tiny(GameSystem):\n'
        "    key: str = 'tiny'\n    name: str = 'Tiny'\n    hit_points: Stat = Stat('hp', 'HP', 'HP')\n"
        'register(Tiny())\n')
    import os
    env = dict(os.environ, KETTLEWRIGHT_SYSTEMS='systems,more_systems', PYTHONPATH=f'{tmp_path}{os.pathsep}.')
    code = 'import kettlewright; print(sorted(kettlewright.SYSTEMS) if kettlewright.system() else "", kettlewright.default_key())'
    out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True, env=env).stdout
    assert out.strip() == "['cairn', 'tiny'] cairn"  # Both packages loaded; the systems package's default stays.


def test_unreadable_system_stats_read_as_empty(lucky_campaign):
    from app.models import Character, db
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        ada = db.session.get(Character, ada_id)
        for broken in ('not json', '[1, 2]', None):
            ada.system_stats = broken
            assert ada.get_stat('luck') is None and ada.get_stat('luck', 3) == 3 and ada.luck is None
        ada.set_stat('luck', 5)
        assert ada.system_stats == '{"luck": 5}'
        with pytest.raises(AttributeError):
            ada._private_name
        db.session.rollback()


def test_pets_and_hirelings_play_their_owner_s_system(lucky_campaign):
    import json
    from app.lib.companions import new_hireling, pet_data
    from app.models import Character, Companion, Party, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        party, ada = db.session.get(Party, party_id), db.session.get(Character, ada_id)
        hireling = new_hireling(party, 'Custom')
        db.session.add(hireling)
        pet = Companion(kind='pet', character=ada, name='Crow', items='[]', containers='[]')
        hound = Companion(kind='pet', hireling=hireling, name='Hound', items='[]', containers='[]')
        db.session.add_all([pet, hound])
        db.session.commit()
        assert pet.rules is hound.rules is hireling.rules is system('lucky')
        mirrored = pet_data({'name': 'Shadow', 'mirror': True}, ada)
        assert (mirrored['luck'], mirrored['luck_max'], mirrored['strength']) == (7, 9, 10) and 'dexterity' not in mirrored
        hireling_id = hireling.id
    warden = login(app.test_client(), 1)
    assert warden.post(f'/companions/{hireling_id}/stat', data={'stat': 'luck', 'value': '1'}).status_code == 204
    assert warden.post(f'/companions/{hireling_id}/stat', data={'stat': 'dexterity', 'value': '1'}).status_code == 400
    with app.app_context():
        assert json.loads(db.session.get(Companion, hireling_id).system_stats)['luck'] == 1


def test_a_bestiary_monster_joins_a_party_of_another_system(lucky_campaign):
    """The bestiary is Cairn's: in a Lucky party a goblin gets Lucky's stats it has (STR, HP), and no Luck."""
    from app.lib.monsters import monster_catalog, new_monster
    from app.models import Party, db
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        goblin = new_monster(db.session.get(Party, party_id), monster_catalog()['goblin'])
        assert goblin.rules is system('lucky') and goblin.strength == goblin.strength_max == 8
        assert goblin.get_stat('luck') is None and goblin.get_stat('luck_max') is None


def test_a_system_s_own_condition_has_a_form_field_and_is_saved(app_with_babel):
    from dataclasses import replace
    from app.forms import CharacterEditForm
    from app.lib.system_forms import condition_fields, with_system_stats
    poisoned = register(replace(Lucky(), key='poisoned', conditions=(Condition('poisoned', 'Poisoned'),)))
    try:
        form = with_system_stats(CharacterEditForm, poisoned)
        assert type(form.poisoned).__name__ == 'UnboundField' and condition_fields(poisoned) == ['poisoned']
        assert with_system_stats(CharacterEditForm, poisoned) is form  # Made once per system.
    finally:
        SYSTEMS.pop('poisoned', None)


def test_the_pdf_discord_and_make_camp_for_another_system(lucky_campaign):
    import json
    from app.lib.character_pdf import character_sheet
    from app.lib.discord_character import act
    from app.lib.wilderness import make_camp
    from app.models import Character, Party, db
    app, (party_id, ada_id) = lucky_campaign
    with app.test_request_context():
        ada, party = db.session.get(Character, ada_id), db.session.get(Party, party_id)
        for orientation in ('landscape', 'portrait'):
            assert character_sheet(ada, party, orientation).draw().getvalue()[:4] == b'%PDF'
        text = act('stat', {'stat': 'lck', 'value': -2}, ada, [ada], str)
        assert 'LCK 7 → 5/9' in text and ada.get_stat('luck') == 5
        with pytest.raises(ValueError):
            act('stat', {'stat': 'dex', 'value': 1}, ada, [ada], str)  # Not one of Lucky's stats.
        # No Fatigue in this system: making camp eats a ration and leaves the items be.
        ada.items = json.dumps([{'id': 1, 'name': 'Rations', 'tags': ['uses'], 'uses': 2, 'location': 0},
                                {'id': 2, 'name': 'Fatigue', 'tags': [], 'location': 0}])
        make_camp(party, [ada])
        assert [i['name'] for i in json.loads(ada.items)] == ['Rations', 'Fatigue']
        db.session.rollback()


def test_the_edit_page_saves_a_stat_without_a_column(lucky_campaign):
    from app.models import Character, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    player = login(app.test_client(), 2)
    page = player.get('/charedit/player/ada').get_data(as_text=True)
    assert 'id="luck-input"' in page and 'id="dexterity-input"' not in page
    form = {'strength': '9', 'strength_max': '10', 'luck': '6', 'luck_max': '11', 'hp': '3', 'hp_max': '4',
            'deprived': 'y', 'gold': '0', 'name': 'Ada', 'description': '', 'traits': '', 'bonds': '', 'omens': '',
            'scars': '', 'notes': '', 'old_items': '[]', 'old_containers': '[{"id": 0, "name": "Main", "slots": 10}]'}
    assert player.post('/charedit/player/ada/save', data=form).status_code == 200
    with app.app_context():
        ada = db.session.get(Character, ada_id)
        assert ada.stat_values() == {'hp': [3, 4], 'strength': [9, 10], 'luck': [6, 11]} and ada.deprived is True


def test_assigning_a_stat_without_a_column_keeps_it_in_system_stats(lucky_campaign):
    """character.luck = 8 (as code written for columns does) is stored like a column would store it."""
    import json
    from app.lib.compact_sheet import sheet
    from app.lib.discord_character import act
    from app.models import Character, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.test_request_context():
        ada = db.session.get(Character, ada_id)
        ada.luck, ada.strength = 8, 9
        db.session.commit()
        db.session.expire_all()
        ada = db.session.get(Character, ada_id)
        assert json.loads(ada.system_stats) == {'luck': 8, 'luck_max': 9} and ada.strength == 9
        ada.nickname = 'Ace'  # Not a stat of its system: a plain attribute, as before.
        assert 'nickname' not in ada.system_stats
        compact = sheet(ada)
        assert compact['luck'] == {'value': 8, 'max': 9} and 'dexterity' not in compact
        # Discord's conditions are the character's system's, but Dead.
        assert 'applied' in act('condition', {'condition': 'deprived', 'active': True}, ada, [ada], str) and ada.deprived
        with pytest.raises(ValueError):
            act('condition', {'condition': 'panicked', 'active': True}, ada, [ada], str)  # Not one of Lucky's.
        db.session.rollback()


def test_a_companion_s_sheet_controls_use_its_system(lucky_campaign):
    from app.lib.companions import new_hireling
    from app.models import Companion, Party, db
    from tests.helpers import login
    app, (party_id, ada_id) = lucky_campaign
    with app.app_context():
        hireling = new_hireling(db.session.get(Party, party_id), 'Custom')
        db.session.add(hireling)
        db.session.commit()
        hireling_id = hireling.id
    warden = login(app.test_client(), 1)
    assert warden.post(f'/companions/{hireling_id}/sheet-stat', data={'stat': 'luck_max', 'value': '20'}).status_code == 204
    assert warden.post(f'/companions/{hireling_id}/sheet-stat', data={'stat': 'luck', 'value': '20'}).status_code == 204
    assert warden.post(f'/companions/{hireling_id}/sheet-stat', data={'stat': 'luck', 'value': '21'}).status_code == 400
    assert warden.post(f'/companions/{hireling_id}/sheet-stat', data={'stat': 'willpower', 'value': '1'}).status_code == 400
    with app.app_context():
        assert db.session.get(Companion, hireling_id).stat_values()['luck'] == [20, 20]


# The web layer (kettlewright.web) and the browser engine (kettlewright/static/kettlewright.js).

def test_the_js_tests_play_cairn_as_the_server_sends_it():
    """tests/js/support/cairn-system.json is Cairn's manifest; regenerate it when Cairn changes:
    python -c "import json; from kettlewright import system; from kettlewright.web import browser_manifest;
    print(json.dumps(browser_manifest(system('cairn')), indent=2))" > tests/js/support/cairn-system.json"""
    import json
    from pathlib import Path
    from kettlewright.web import browser_manifest
    fixture = json.loads((Path(__file__).parents[1] / 'js/support/cairn-system.json').read_text())
    assert fixture == json.loads(json.dumps(browser_manifest(system('cairn'))))


def test_the_browser_engine_has_no_system_of_its_own():
    import re
    from pathlib import Path
    import kettlewright
    source = (Path(kettlewright.__file__).parent / 'static' / 'kettlewright.js').read_text()
    code = '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith('//'))
    assert not re.search(r'[Cc]airn|strength|deprived|panicked|bulky|petty|\d Armor', code)
    # Its plainest rules are GameSystem's defaults.
    plain = GameSystem('', '', Stat('hp', 'HP', 'Hit Points')).manifest()
    for key in ('inventory', 'armor', 'save', 'weak_die', 'fatigue', 'conditions', 'attributes'):
        assert re.sub(r'\s', '', json_js(plain[key])) in re.sub(r'\s', '', source), key


def json_js(value):
    """A manifest value as kettlewright.js writes it in PLAIN ({main_slots: 10, ...})."""
    import json
    import re
    return re.sub(r'"(\w+)":', r'\1:', json.dumps(value)).replace('"', "'")


def test_pages_serve_the_engine_and_play_their_record_s_system(lucky_campaign):
    import json
    from tests.helpers import login
    app, _ = lucky_campaign
    player = login(app.test_client(), 2)
    script = player.get('/kettlewright/static/kettlewright.js')
    assert script.status_code == 200 and b'export function gameSystem' in script.data
    page = app.test_client().get('/login').get_data(as_text=True)  # Signed out: a page without a record.
    importmap = json.loads(page.split('<script type="importmap">', 1)[1].split('</script>', 1)[0])
    assert importmap == {'imports': {'#kettlewright': '/kettlewright/static/kettlewright.js'}}
    assert page.index('type="importmap"') < page.index('type="module"')  # Before any module.
    manifest = lambda html: json.loads(html.split('<script id="game-system" type="application/json">', 1)[1]
                                       .split('</script>', 1)[0])
    assert manifest(page)['key'] == 'cairn'  # A page without a record: the default system.
    with app.app_context():
        from app.models import Character
        ada = Character.query.filter_by(name='Ada').one()
        sheet = player.get(f'/users/{ada.owner_username}/characters/{ada.url_name}/').get_data(as_text=True)
    assert manifest(sheet)['key'] == 'lucky'  # Ada's own system.
    assert [a['key'] for a in manifest(sheet)['attributes']] == ['strength', 'luck']


def test_a_system_s_own_files_and_template_pieces(app_with_babel):
    """A system's static/ and templates/<key>/ are served and found; without its own piece, the engine's."""
    from flask import render_template_string
    from kettlewright.web import system_template
    with app_with_babel.test_request_context():
        assert system_template('help/monster_format.html') == ['cairn/help/monster_format.html',
                                                               'kettlewright/help/monster_format.html']
        loader = app_with_babel.jinja_env.loader
        assert 'kettlewright/help/monster_format.html' in loader.list_templates()
        assert render_template_string("{{ rules_for(None).key }}") == 'cairn'

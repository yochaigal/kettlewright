"""Cairn artwork (experiment): off unless CAIRN_ART is set, credited where shown, and never in API or htmx 404s."""
import json

from app.lib.cairn_art import ART
from app.lib.campaign_parties import create_campaign
from app.models import Character, User, db
from helpers import login


def setup(app, art):
    """user 1 runs a campaign whose party has user 2's character; user 3 has nothing yet."""
    app.config['CAIRN_ART'] = art
    with app.app_context():
        db.session.add_all([User(id=1, username='warden'), User(id=2, username='player'), User(id=3, username='newcomer')])
        db.session.flush()
        party = create_campaign(1, 'Old Roads').parties[0]
        db.session.flush()
        hero = Character(owner=2, owner_username='player', name='Ada', url_name='ada', party_id=party.id,
                         background='Custom', custom_background='Wanderer', edition='2e',
                         strength=10, strength_max=10, dexterity=10, dexterity_max=10, willpower=10, willpower_max=10,
                         hp=4, hp_max=4, gold=0, armor='0', deprived=False, panicked=False, dead=False,
                         description='', traits='', notes='', bonds='', omens='', scars='', custom_image=False,
                         image_url='', items='[]', containers='[{"id": 0, "name": "Main", "slots": 10}]')
        db.session.add(hero)
        db.session.flush()
        party.members = json.dumps([hero.id])
        db.session.commit()
        return party.id, f'/users/warden/parties/{party.party_url}/'


def empty_party(app):
    """A second party of user 1's campaign, with no members."""
    from app.lib.campaign_parties import create_party
    from app.models import Campaign
    with app.app_context():
        party = create_party(db.session.get(Campaign, 1), 'Ferrymen')
        db.session.commit()
        return party.id, f'/users/warden/parties/{party.party_url}/'


def pages(app, party_id):
    """Every empty page, as the person who sees it empty."""
    empty_id, empty_url = empty_party(app)
    newcomer, player, warden = (login(app.test_client(), user) for user in (3, 2, 1))
    return {
        'rider': newcomer.get('/users/newcomer/characters/'),
        'stone': newcomer.get('/campaigns/?view=campaigns'),
        'roots': newcomer.get('/campaigns/?view=parties'),
        'map': player.get(f'/party/{party_id}/map/'),
        'tree': player.get(f'/party/{party_id}/wiki/'),
        'camp': warden.get(empty_url),
        'monster': warden.get(f'/parties/{empty_id}/monsters'),
    }


def test_without_the_setting_no_page_shows_cairn_art(app_with_babel):
    app = app_with_babel
    party_id, _ = setup(app, False)
    for key, response in pages(app, party_id).items():
        assert response.status_code == 200, key
        page = response.get_data(as_text=True)
        assert 'cairnrpg.com/assets' not in page and 'first-party/img' not in page and 'cairn_art.css' not in page, key
    missing = app.test_client().get('/no-such-page', headers={'Accept': 'text/html'})
    assert missing.status_code == 404 and 'cairn-art-404' not in missing.get_data(as_text=True)


def test_every_empty_page_shows_its_own_art_with_its_credit(app_with_babel):
    app = app_with_babel
    party_id, _ = setup(app, True)
    for key, response in pages(app, party_id).items():
        page = response.get_data(as_text=True)
        assert response.status_code == 200 and ART[key]['src'] in page, key
        assert ART[key]['credit'].replace("'", '&#39;') in page, key
    # Each piece in one place only.
    assert len({art['src'] for art in ART.values()}) == len(ART)


def test_art_only_where_the_page_is_empty(app_with_babel):
    app = app_with_babel
    party_id, party_url = setup(app, True)
    warden, player = login(app.test_client(), 1), login(app.test_client(), 2)
    assert ART['stone']['src'] not in warden.get('/campaigns/?view=campaigns').get_data(as_text=True)
    assert ART['roots']['src'] not in warden.get('/campaigns/?view=parties').get_data(as_text=True)
    assert ART['rider']['src'] not in player.get('/users/player/characters/').get_data(as_text=True)
    assert ART['camp']['src'] not in warden.get(party_url).get_data(as_text=True)
    # A player in a party has it under Playing in, so their Parties view isn't empty.
    assert ART['roots']['src'] not in player.get('/campaigns/?view=parties').get_data(as_text=True)


def test_the_404_has_the_bird_for_pages_only(app_with_babel):
    app = app_with_babel
    setup(app, True)
    client = app.test_client()
    missing = client.get('/no-such-page', headers={'Accept': 'text/html'})
    assert missing.status_code == 404 and ART['bird']['src'] in missing.get_data(as_text=True)
    assert 'cairn-art-404' not in client.get('/no-such-page', headers={'HX-Request': 'true'}).get_data(as_text=True)
    assert 'cairn-art-404' not in client.get('/no-such-page', headers={'Accept': 'application/json'}).get_data(as_text=True)
    assert client.get('/api/v1/no-such-thing', headers={'Accept': 'text/html'}).is_json
    # The login page has no art.
    assert 'first-party/img' not in client.get('/login').get_data(as_text=True)

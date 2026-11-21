"""#483 parties join and leave campaigns; #482/#488 a campaign's World Map, and pins (reveal with the map,
moving them, label size, the players' pins in the map editor)."""
import json

from app.models import db, Campaign, ContentEntry, MapPin, Module, Party, PartyPresentation, PointcrawlMap
from helpers import login
from test_campaigns import setup, create_map, map_entry_id, reveal, renderable_party_page  # noqa: F401 (fixture)


def campaign_of(app, party_id):
    with app.app_context():
        return db.session.get(Party, party_id).campaign_id


# ----- #483: add an existing party to a campaign, remove one from it -----

def test_parties_join_and_leave_campaigns(setup):
    app, client = setup
    with app.app_context():
        db.session.add(Campaign(id=2, owner_id=1, name='Second campaign'))
        db.session.commit()
    lobby = client.get('/campaigns/1/').text
    # Party 2 (no campaign) is offered; party 3 (someone else's) is not. The whole row opens the party.
    dialog = lobby[lobby.index('id="add-party-dialog"'):lobby.index('</dialog>', lobby.index('id="add-party-dialog"'))]
    assert 'Without a campaign' in dialog and 'value="2"' in dialog and 'value="3"' not in dialog
    assert 'class="campaign-party-remove"' in lobby
    # Remove party 1: it has no campaign, keeps what it was shown, and is listed on the Campaigns page.
    assert client.post('/campaigns/1/parties/1/remove').status_code == 302
    assert campaign_of(app, 1) is None
    index = client.get('/campaigns/').text
    assert 'Parties without a campaign' in index and 'Party 1' in index.split('class="unassigned-island"')[1]
    assert 'No parties yet' in client.get('/campaigns/1/').text  # The page still works without parties.
    # Add both back into the second campaign at once.
    assert client.post('/campaigns/2/parties/add', data={'party_id': ['1', '2']}).status_code == 302
    assert campaign_of(app, 1) == 2 and campaign_of(app, 2) == 2
    # From another campaign, a party moves: the first campaign lists it under "In Second campaign".
    lobby = client.get('/campaigns/1/').text
    assert 'In Second campaign' in lobby
    assert client.post('/campaigns/1/parties/add', data={'party_id': '1'}).status_code == 302
    assert campaign_of(app, 1) == 1
    # Not the Warden's party, a party of another campaign, or not the Warden's campaign: refused.
    assert client.post('/campaigns/1/parties/add', data={'party_id': '3'}).status_code == 400
    assert client.post('/campaigns/1/parties/2/remove').status_code == 404
    login(client, 2)
    assert client.post('/campaigns/1/parties/1/remove').status_code == 403
    assert campaign_of(app, 1) == 1


def test_party_settings_offer_no_campaign(setup):
    app, client = setup
    form = client.get('/party/edit/user1/party1').text
    assert '<option value="" >No campaign</option>' in form or 'No campaign</option>' in form
    data = {'name': 'Party 1', 'description': '', 'old_items': '[]', 'old_containers': '[]'}
    assert client.post('/party/edit/user1/party1/save', data={**data, 'campaign_id': ''}).status_code == 200
    assert campaign_of(app, 1) is None
    assert client.post('/party/edit/user1/party1/save', data={**data, 'campaign_id': '1'}).status_code == 200
    assert campaign_of(app, 1) == 1
    assert client.post('/party/edit/user1/party1/save', data=data).status_code == 200  # No field: unchanged.
    assert campaign_of(app, 1) == 1


# ----- #482, #488: the campaign's World Map -----

def world_maps(app):
    with app.app_context():
        return [item.id for item in PointcrawlMap.query.filter_by(world_map=True).all()]


def edit_map(client, map_id, **fields):
    page = client.get(f'/maps/{map_id}/edit').text
    version = page.split('name="version" value="')[1].split('"')[0]
    return client.post(f'/maps/{map_id}/edit', data={'version': version, 'title': 'A map', 'world_map_field': '1', **fields})


def test_one_world_map_per_campaign_chosen_in_the_editor(setup):
    app, client = setup
    first, _ = create_map(client, title='Realm')
    second, _ = create_map(client, title='Region')
    assert 'World Map of Secret campaign' in client.get(f'/maps/{first}/edit').text
    assert edit_map(client, first, world_map='1').status_code == 302
    assert world_maps(app) == [first]
    assert edit_map(client, second, world_map='1').status_code == 302
    assert world_maps(app) == [second]  # One per campaign.
    assert edit_map(client, second).status_code == 302  # Unchecked.
    assert world_maps(app) == []


def test_a_generated_setting_becomes_the_world_map(setup):
    app, client = setup
    draft = {'nodes': [], 'edges': []}
    response = client.post('/campaigns/1/modules', data={'name': 'Random world', 'start': 'random', 'kind': 'realm',
                                                         'title': 'Realm', 'draft': json.dumps(draft)})
    assert response.status_code == 302
    assert len(world_maps(app)) == 1
    client.post('/campaigns/1/modules', data={'name': 'Another', 'start': 'random', 'kind': 'dungeon',
                                              'title': 'Dungeon', 'draft': json.dumps(draft)})
    with app.app_context():
        assert db.session.get(PointcrawlMap, world_maps(app)[0]).entry.title == 'Realm'  # The first stays.


def test_party_world_map_button(setup):
    app, client = setup
    renderable_party_page(app)
    assert 'World Map' in client.get('/users/user1/parties/party1/').text
    first, _ = create_map(client, title='Realm')
    # Use one of the campaign's maps; it is not revealed yet, so the Warden can reveal it from here.
    assert client.post('/party/1/world-map', data={'map_id': first}).status_code == 302
    page = client.get('/party/1/map/').text
    assert 'has not been shown it yet' in page and 'Reveal the World Map to Party 1' in page
    response = client.post(f'/materials/{map_entry_id(app, first)}/reveal',
                           data={'party_ids': '1', 'version_1': '0', 'return_to': 'map'})
    assert response.location.endswith('/party/1/map/')
    # Revealed: the button opens it, even with other maps revealed too.
    second, _ = create_map(client, title='Second')
    reveal(client, map_entry_id(app, second))
    assert client.get('/party/1/map/').location.endswith(f'/party/1/map/{first}/')
    assert 'World Map' in client.get(f'/party/1/map/{first}/').text
    # Draw a new one: a new map in the campaign's module, which becomes the World Map when it has none.
    client.post(f'/maps/{first}/edit', data={'version': '1', 'title': 'Realm', 'world_map_field': '1'})
    response = client.post('/party/1/world-map', data={'create': 'draw'})
    assert '/materials/generate?' in response.location and 'world=1' in response.location
    assert 'New World Map' in client.get(response.location).text
    # Someone else's map, or a player: refused.
    with app.app_context():
        db.session.add(Campaign(id=9, owner_id=1, name='Elsewhere'))
        db.session.commit()
    other, _ = create_map(client, campaign_id=9, title='Elsewhere map')
    assert client.post('/party/1/world-map', data={'map_id': other}).status_code == 404
    login(client, 2)
    assert client.post('/party/1/world-map', data={'map_id': first}).status_code == 403


def test_moving_a_map_to_another_campaign_clears_its_world_map(setup):
    app, client = setup
    first, _ = create_map(client, title='Realm')
    edit_map(client, first, world_map='1')
    with app.app_context():
        db.session.add(Campaign(id=9, owner_id=1, name='Elsewhere'))
        db.session.add(Module(id=90, campaign_id=9, title='There'))
        db.session.commit()
    page = client.get(f'/maps/{first}/edit').text
    version = page.split('name="version" value="')[1].split('"')[0]
    client.post(f'/maps/{first}/edit', data={'version': version, 'title': 'Realm', 'module_id': '90'})
    assert world_maps(app) == []


# ----- #482: pins -----

def test_pins_revealed_with_the_map(setup):
    app, client = setup
    map_id, graph = create_map(client, nodes=0)
    graph['nodes'] = [{'id': 'new-pin', 'number': 1, 'x': 10, 'y': 20, 'title': 'Shown well', 'body': '',
                       'category': 'map_note', 'content_changed': True, 'reveal': True},
                      {'id': 'new-pin-2', 'number': 2, 'x': 30, 'y': 40, 'title': 'Hidden cave', 'body': '',
                       'category': 'map_note', 'content_changed': True, 'reveal': False}]
    saved = client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)}).json
    assert [node['reveal'] for node in saved['nodes']] == [True, False]
    reveal(client, map_entry_id(app, map_id))
    with app.app_context():
        shown = {row.title for row in PartyPresentation.query.filter_by(party_id=1, published=True)}
    assert 'Shown well' in shown and 'Hidden cave' not in shown
    # A pin added later with the option on reaches the parties already shown the map.
    saved['nodes'].append({'id': 'new-pin-3', 'number': 3, 'x': 50, 'y': 60, 'title': 'New camp', 'body': '',
                           'category': 'map_note', 'content_changed': True, 'reveal': True})
    client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(saved)})
    with app.app_context():
        assert PartyPresentation.query.filter_by(party_id=1, title='New camp', published=True).count() == 1


def test_pin_maker_or_warden_moves_a_pin_and_the_warden_sees_it_in_the_editor(setup):
    app, client = setup
    map_id, _ = create_map(client)
    reveal(client, map_entry_id(app, map_id))
    login(client, 2)  # Player A, in party 1.
    state = client.post(f'/party/1/map/{map_id}/pins', data={'x': 1, 'y': 2, 'title': 'Our camp'}).json
    pin = state['pins'][0]
    assert pin['movable'] is True
    state = client.post(f'/party/1/map/{map_id}/pins/{pin["id"]}/move', data={'x': 30, 'y': 40}).json
    assert (state['pins'][0]['x'], state['pins'][0]['y']) == (30, 40)
    with app.app_context():
        db.session.get(MapPin, pin['id']).created_by = 3  # Placed by someone else.
        db.session.commit()
    assert client.get(f'/party/1/map/{map_id}/state').json['pins'][0]['movable'] is False
    assert client.post(f'/party/1/map/{map_id}/pins/{pin["id"]}/move', data={'x': 5, 'y': 5}).status_code == 403
    login(client, 1)  # The Warden moves any pin, and sees the players' pins in the map editor.
    assert client.post(f'/party/1/map/{map_id}/pins/{pin["id"]}/move', data={'x': 5, 'y': 6}).status_code == 200
    editor = client.get(f'/maps/{map_id}/edit').text
    assert 'data-player-pins=' in editor and 'Party 1: Our camp' in editor and 'Show players' in editor


def test_pin_label_size_and_counts(setup):
    app, client = setup
    map_id, _ = create_map(client, nodes=1)
    assert client.get(f'/maps/{map_id}/data').json['pin_size'] == 24  # Medium, larger than the old 16.
    page = client.get(f'/maps/{map_id}/edit').text
    version = page.split('name="version" value="')[1].split('"')[0]
    client.post(f'/maps/{map_id}/edit', data={'version': version, 'title': 'A map', 'pin_size': 'large'})
    assert client.get(f'/maps/{map_id}/data').json['pin_size'] == 34
    client.post(f'/maps/{map_id}/edit', data={'version': str(int(version) + 1), 'title': 'A map', 'pin_size': 'huge'})
    assert client.get(f'/maps/{map_id}/data').json['pin_size'] == 34  # Unknown sizes are ignored.
    reveal(client, map_entry_id(app, map_id))
    assert client.get(f'/party/1/maps/{map_id}/data').json['pin_size'] == 34  # The party sees the same size.
    view = client.get(f'/party/1/map/{map_id}/').text
    assert 'x-text="pinCount"' in view and '&#34;pinOne&#34;: &#34;pin&#34;' in view


def test_campaigns_page_island_adds_a_party_to_a_campaign(setup):
    app, client = setup
    index = client.get('/campaigns/').text
    island = index[index.index('class="unassigned-island"'):]
    assert 'Party 2' in island and 'id="assign-party-2"' in island and 'Add to campaign' in island
    response = client.post('/party/2/campaign', data={'campaign_id': '1'})
    assert response.location.endswith('/campaigns/1/') and campaign_of(app, 2) == 1
    assert 'unassigned-island' not in client.get('/campaigns/').text  # None left.
    assert client.post('/party/3/campaign', data={'campaign_id': '1'}).status_code == 404  # Someone else's party.
    with app.app_context():
        db.session.add(Campaign(id=5, owner_id=4, name='Theirs'))
        db.session.commit()
    assert client.post('/party/1/campaign', data={'campaign_id': '5'}).status_code == 403  # Someone else's campaign.

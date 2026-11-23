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
    index = client.get('/campaigns/?view=parties').text  # Its card says so, in the Parties view.
    card = index[index.index('Party 1</a>'):]
    assert 'No campaign' in card[:card.index('</li>')]
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


def test_reveal_map_and_all_its_pins_with_a_pin_marked_reveal_with_the_map(setup):
    """#500: Also reveal its pins on a map whose pin is marked Reveal with the map showed it twice in one save:
    the second row broke the one-row-per-party rule and the Warden read "changed in another tab"."""
    app, client = setup
    map_id, graph = create_map(client, nodes=0)
    graph['nodes'] = [{'id': 'new-pin', 'number': 1, 'x': 10, 'y': 20, 'title': 'Waterfall City', 'body': '',
                       'category': 'map_note', 'content_changed': True, 'reveal': True},
                      {'id': 'new-pin-2', 'number': 2, 'x': 30, 'y': 40, 'title': 'Hidden cave', 'body': '',
                       'category': 'map_note', 'content_changed': True, 'reveal': False}]
    client.post(f'/maps/{map_id}/data', data={'graph': json.dumps(graph)})
    response = reveal(client, map_entry_id(app, map_id), with_contents='1')
    assert response.status_code == 302, response.text
    with app.app_context():
        shown = sorted(row.title for row in PartyPresentation.query.filter_by(party_id=1, published=True))
    assert shown == ['Hidden cave', 'SECRET MAP', 'Waterfall City']


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


def test_a_party_without_a_campaign_is_added_to_one_from_its_card(setup):
    app, client = setup
    # The Parties view has every party; the Campaigns view no longer repeats the ones without a campaign.
    assert 'unassigned-island' not in client.get('/campaigns/?view=campaigns').text
    index = client.get('/campaigns/?view=parties').text
    card = index[index.index('Party 2</a>'):]
    card = card[:card.index('</li>')]
    assert 'id="assign-party-2"' in card and 'Add to campaign' in card
    assert 'id="assign-party-1"' not in index  # Party 1 is in a campaign.
    response = client.post('/party/2/campaign', data={'campaign_id': '1'})
    assert response.location.endswith('/campaigns/1/') and campaign_of(app, 2) == 1
    assert 'Add to campaign' not in client.get('/campaigns/?view=parties').text  # None left.
    assert client.post('/party/3/campaign', data={'campaign_id': '1'}).status_code == 404  # Someone else's party.
    with app.app_context():
        db.session.add(Campaign(id=5, owner_id=4, name='Theirs'))
        db.session.commit()
    assert client.post('/party/1/campaign', data={'campaign_id': '5'}).status_code == 403  # Someone else's campaign.


# ----- Discord feedback: every party at once, beside Campaigns -----

def parties_view(page):
    return page[page.index('class="campaigns-island parties-island"'):]


def test_the_parties_view_lists_every_party_and_its_characters(setup):
    app, client = setup
    with app.app_context():
        from app.models import Character
        hero = db.session.get(Character, 1)
        hero.owner_username, hero.url_name = 'user2', 'player-a'
        hero.hp, hero.hp_max, hero.strength, hero.strength_max, hero.dexterity, hero.dexterity_max = 3, 6, 8, 12, 11, 11
        hero.deprived = True
        db.session.commit()
    page = parties_view(client.get('/campaigns/?view=parties').text)
    # The Warden's parties, in a campaign or not, never someone else's.
    assert 'Party 1' in page and 'Party 2' in page and 'Party 3' not in page
    assert 'Secret campaign' in page and 'No campaign' in page
    # Each character at a glance: HP, STR (current/max when lowered), DEX, Deprived; the name opens the sheet.
    row = page[page.index('Player A') - 300:page.index('</li>', page.index('Player A'))]
    assert 'href="/users/user2/characters/player-a/"' in row
    assert '<strong>3</strong>/6' in row and '<strong>8</strong>/12' in row and '<strong>11</strong></span>' in row
    assert 'Deprived' in row
    # The campaigns themselves are not in this view.
    assert 'class="campaign-gallery"' not in page


def test_the_chosen_view_is_remembered_and_the_old_parties_page_opens_it(setup):
    app, client = setup
    assert client.get('/users/user1/parties/').location.endswith('/campaigns/?view=parties')
    first = client.get('/campaigns/?view=parties')
    assert 'kw-campaigns-view=parties' in first.headers['Set-Cookie']
    assert 'class="party-overviews"' in client.get('/campaigns/').text  # Back to it without asking.
    assert 'aria-current="page"><i class="fa-solid fa-users"' in client.get('/campaigns/').text
    client.get('/campaigns/?view=campaigns')
    assert 'class="party-overviews"' not in client.get('/campaigns/').text
    assert client.get('/campaigns/?view=nonsense').status_code == 200


def test_players_see_the_parties_they_play_in(setup):
    app, client = setup
    login(client, 2)  # Plays Player A in party 1; runs no party.
    page = client.get('/campaigns/?view=parties').text
    assert 'Your parties' not in page  # Nothing to run: no empty box.
    played = parties_view(page)
    assert 'Party 1' in played and 'Warden: user1' in played and 'Party 2' not in played


def test_new_party_from_the_parties_view_in_a_campaign_or_none(setup):
    """Discord feedback: New party in the Parties view, in one of your campaigns or in none."""
    from app.models import Party
    app, client = setup
    page = client.get('/campaigns/?view=parties').text
    dialog = page[page.index('id="new-party-overview-dialog"'):page.index('</dialog>', page.index('id="new-party-overview-dialog"'))]
    assert 'action="/parties/new"' in dialog and '<option value="">No campaign</option>' in dialog and 'Secret campaign' in dialog
    assert 'New party' in page and 'New campaign' not in page.split('characters-create-actions')[1][:400]
    assert 'New campaign' in client.get('/campaigns/?view=campaigns').text  # The Campaigns view keeps its own New.
    loose = client.post('/parties/new', data={'name': 'Wanderers', 'campaign_id': ''})
    in_campaign = client.post('/parties/new', data={'name': 'Raiders', 'description': 'West Marches', 'campaign_id': '1'})
    assert loose.status_code == in_campaign.status_code == 302
    with app.app_context():
        wanderers, raiders = (Party.query.filter_by(name=name).one() for name in ('Wanderers', 'Raiders'))
        assert wanderers.campaign_id is None and wanderers.owner == 1 and wanderers.join_code
        assert raiders.campaign_id == 1 and raiders.owner == 1 and raiders.description == 'West Marches'
    with app.app_context():
        db.session.add(Campaign(id=9, owner_id=4, name='Theirs'))
        db.session.commit()
    assert client.post('/parties/new', data={'name': 'Sneaky', 'campaign_id': '9'}).status_code in (403, 404)
    assert client.post('/parties/new', data={'name': '', 'campaign_id': ''}).status_code == 400

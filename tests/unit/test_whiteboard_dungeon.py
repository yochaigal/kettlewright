"""Whiteboard Dungeon brush (#439): Warden-only controls, and its shapes save like any drawing."""
import json
import re

from tests.unit.test_shared_map import URL, shared  # noqa: F401  (fixture)

# A 3x2 room with a door, as whiteboard_dungeon.js dungeonShapes() draws it.
SHAPES = json.loads('[{"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "rectangle", "id": "dungeon-80-floor--1_-1_3_2", "x": -80, "y": -80, "width": 240, "height": 160, "backgroundColor": "#efe6d2", "strokeColor": "#efe6d2", "fillStyle": "solid", "strokeWidth": 1, "opacity": 85}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "line", "id": "dungeon-80-wall-h--1_-10_3", "x": -80, "y": -80, "width": 104, "height": 0, "points": [[0, 0], [104, 0]], "strokeColor": "#2b2b2b", "backgroundColor": "transparent", "strokeWidth": 8, "opacity": 100}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "line", "id": "dungeon-80-wall-h--1_7_20", "x": 56, "y": -80, "width": 104, "height": 0, "points": [[0, 0], [104, 0]], "strokeColor": "#2b2b2b", "backgroundColor": "transparent", "strokeWidth": 8, "opacity": 100}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "line", "id": "dungeon-80-wall-v--1_-10_10", "x": -80, "y": -80, "width": 0, "height": 160, "points": [[0, 0], [0, 160]], "strokeColor": "#2b2b2b", "backgroundColor": "transparent", "strokeWidth": 8, "opacity": 100}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "line", "id": "dungeon-80-wall-h-1_-10_20", "x": -80, "y": 80, "width": 240, "height": 0, "points": [[0, 0], [240, 0]], "strokeColor": "#2b2b2b", "backgroundColor": "transparent", "strokeWidth": 8, "opacity": 100}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "line", "id": "dungeon-80-wall-v-2_-10_10", "x": 160, "y": -80, "width": 0, "height": 160, "points": [[0, 0], [0, 160]], "strokeColor": "#2b2b2b", "backgroundColor": "transparent", "strokeWidth": 8, "opacity": 100}, {"roughness": 0, "locked": true, "angle": 0, "strokeStyle": "solid", "roundness": null, "type": "rectangle", "id": "dungeon-80-door-h-0_-1", "x": 24, "y": -86.5, "width": 32, "height": 13, "backgroundColor": "#9a6a3a", "strokeColor": "#2b2b2b", "fillStyle": "solid", "strokeWidth": 2, "opacity": 100}]')


def config(html):
    return json.loads(re.search(r'id="shared-map-config" type="application/json">(.*?)</script>', html, re.S)[1])


def test_only_the_warden_gets_the_dungeon_tools(shared):
    app, clients, _ = shared
    warden = clients[1].get('/party/1/shared-map').get_data(as_text=True)
    assert 'class="board-toolbar board-island"' in warden and 'class="warden-board"' in warden
    # Dungeon tools come first (left), Fog of War second (right).
    assert warden.index('data-dungeon-tool="floor"') < warden.index('id="fog-enabled"')
    for tool in ('floor', 'erase', 'door'):
        assert f'data-dungeon-tool="{tool}"' in warden
    assert 'data-dungeon-tool="room"' not in warden
    # Fog controls keep the IDs and data attributes shared_map.js uses.
    for control in ('id="fog-enabled"', 'data-fog-tool="reveal"', 'data-fog-tool="cover"', 'id="fog-radius"',
                    'data-fog-action="undo"', 'data-fog-action="hide_all"', 'data-fog-action="reveal_all"',
                    'id="player-preview"', 'id="fog-status"', 'id="discard-fog"'):
        assert control in warden, control
    assert 'id="dungeon-size"' not in warden and 'id="dungeon-clear"' in warden
    messages = config(warden)['messages']
    assert messages['dungeonTooBig'] and messages['confirmClearDungeon']
    player = clients[2].get('/party/1/shared-map').get_data(as_text=True)
    assert 'board-toolbar' not in player and 'data-dungeon-tool' not in player and 'warden-board' not in player


def test_dungeon_shapes_save_and_load_unchanged(shared):
    app, clients, _ = shared
    drawing = {'elements': SHAPES, 'files': {}}
    assert clients[1].post(URL, json={'version': 0, 'drawing': drawing}).json == {'version': 1}
    saved = {element['id']: element for element in clients[2].get(URL).json['drawing']['elements']}
    assert list(saved) == [shape['id'] for shape in SHAPES]
    for shape in SHAPES:
        for key in ('type', 'x', 'y', 'width', 'height', 'points', 'locked', 'opacity', 'strokeWidth', 'backgroundColor'):
            assert saved[shape['id']].get(key) == shape.get(key), (shape['id'], key)

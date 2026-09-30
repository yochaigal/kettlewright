"""Whiteboard snapshots and independent, Warden-controlled fog operations."""
from copy import deepcopy
import hashlib
import json
import math
import re
from uuid import NAMESPACE_URL, uuid5

from flask import abort
from app.lib.map_drawing import EMPTY_DRAWING, validate_drawing


def empty_fog():
    return {'enabled': False, 'base': 'covered', 'strokes': [], 'applied': []}


def board_state(row):
    return {'drawing': row.drawing if row else deepcopy(EMPTY_DRAWING),
            'version': row.version if row else 0, 'generation': row.generation if row else 1,
            'fog': row.fog if row else empty_fog(), 'fog_version': row.fog_version if row else 0}


def drawing_value(value):
    drawing = validate_drawing(value, allow_frames=True)
    state = value.get('appState', {}) if isinstance(value, dict) else {}
    color = state.get('viewBackgroundColor', '#ffffff') if isinstance(state, dict) else None
    if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        abort(400, 'Invalid canvas background.')
    drawing['appState'] = {'viewBackgroundColor': color}
    return drawing


def integer(data, key, default=None):
    value = data.get(key, default)
    if type(value) is not int or value < 0:
        abort(400, f'Invalid {key}.')
    return value


def source_snapshot(pointcrawl):
    """Only visual data; never copy material bodies, metadata or nested maps."""
    drawing = deepcopy(pointcrawl.drawing or EMPTY_DRAWING)
    elements = drawing['elements']
    nodes = {node.id: node for node in pointcrawl.nodes}
    def shape(key, kind, x, y, **values):
        return {'id': key, 'type': kind, 'x': x, 'y': y, 'width': 60, 'height': 60,
                'angle': 0, 'strokeColor': '#1b1b1f', 'backgroundColor': 'transparent',
                'fillStyle': 'solid', 'strokeWidth': 2, 'strokeStyle': 'solid',
                'roughness': 0, 'opacity': 100, 'groupIds': [], 'seed': 1, 'version': 1,
                'versionNonce': 1, 'isDeleted': False, 'locked': False, **values}
    for edge in sorted(pointcrawl.edges, key=lambda edge: edge.id):
        a, b = nodes.get(edge.source_id), nodes.get(edge.target_id)
        if a is None or b is None:
            continue
        elements.append(shape(f'kw-edge-{edge.id}', 'line', a.x, a.y,
            width=abs(b.x-a.x), height=abs(b.y-a.y), points=[[0, 0], [b.x-a.x, b.y-a.y]],
            strokeStyle='dashed' if edge.entry.path_type == 'hidden' else
                        'dotted' if edge.entry.path_type == 'conditional' else 'solid'))
    for node in sorted(nodes.values(), key=lambda node: (node.number, node.id)):
        elements.append(shape(f'kw-node-{node.id}', 'ellipse', node.x-30, node.y-30,
                              backgroundColor='#ffffff'))
        title = re.sub(r'(.{1,24})(?:\s+|$)', r'\1\n', f'{node.number}. {node.entry.title}').strip()
        lines = title.split('\n')
        elements.append(shape(f'kw-label-{node.id}', 'text', node.x-55, node.y+36,
            text=title, originalText=title, fontSize=16, fontFamily=2, lineHeight=1.25,
            textAlign='left', verticalAlign='top', autoResize=True,
            width=max(map(len, lines), default=1)*9, height=len(lines)*20))
    # Stable per snapshot, fresh relative to the source, including groups/files.
    namespace = uuid5(NAMESPACE_URL, f'whiteboard-source:{pointcrawl.id}')
    remap = lambda value: uuid5(namespace, str(value)).hex
    ids = {element['id']: remap(element['id']) for element in elements}
    file_ids = {key: remap('file:'+key) for key in drawing['files']}
    for element in elements:
        element['id'] = ids[element['id']]
        element.pop('customData', None)
        element['link'] = None
        element['groupIds'] = [remap('group:'+key) for key in element.get('groupIds', [])]
        for key in ('containerId', 'frameId'):
            element[key] = ids.get(element.get(key))
        for key in ('startBinding', 'endBinding'):
            if element.get(key):
                element[key]['elementId'] = ids.get(element[key].get('elementId'))
        if element.get('boundElements'):
            element['boundElements'] = [{**item, 'id': ids[item['id']]} for item in element['boundElements'] if item['id'] in ids]
        if element.get('fileId'):
            element['fileId'] = file_ids.get(element['fileId'])
    drawing['files'] = {file_ids[key]: {**value, 'id': file_ids[key]} for key, value in drawing['files'].items()}
    drawing = drawing_value(drawing)
    digest = hashlib.sha256(json.dumps(drawing, sort_keys=True).encode()).hexdigest()
    return drawing, digest


def fog_operation(current, operation):
    if not isinstance(operation, dict):
        abort(400)
    op_id = operation.get('id')
    if not isinstance(op_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', op_id):
        abort(400, 'Invalid fog operation ID.')
    fog = deepcopy(current)
    if op_id in fog['applied']:
        return fog, False
    kind = operation.get('type')
    if kind in ('reveal', 'cover'):
        radius, points = operation.get('radius'), operation.get('points')
        if type(radius) not in (int, float) or not math.isfinite(radius) or not 1 <= radius <= 2000:
            abort(400, 'Invalid brush radius.')
        if not isinstance(points, list) or not 1 <= len(points) <= 5000:
            abort(400, 'Invalid fog stroke.')
        for point in points:
            if not isinstance(point, list) or len(point) != 2 or any(
                    type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1000000 for n in point):
                abort(400, 'Invalid fog coordinates.')
        if not fog['enabled']:
            abort(400, 'Enable fog before painting.')
        fog['strokes'].append({'id': op_id, 'type': kind, 'radius': radius, 'points': points})
    elif kind in ('hide_all', 'reveal_all'):
        fog.update(enabled=True, base='covered' if kind == 'hide_all' else 'clear', strokes=[])
    elif kind == 'disable':
        fog['enabled'] = False
    elif kind == 'undo':
        if fog['strokes']:
            fog['strokes'].pop()
    else:
        abort(400, 'Invalid fog operation.')
    if len(json.dumps(fog)) > 2 * 1024 * 1024:
        abort(400, 'Fog is too complex. Reset it before adding more strokes.')
    fog['applied'] = (fog['applied'] + [op_id])[-1000:]
    return fog, True


def board_update(before, after):
    """Broadcast visual deltas without resending unchanged embedded images."""
    if before['generation'] != after['generation']:
        return {'state': after}
    update = {}
    if before['version'] != after['version']:
        old, new = before['drawing'], after['drawing']
        previous = {element['id']: element for element in old['elements']}
        update['drawing'] = {
            'base_version': before['version'],
            'elements': [element for element in new['elements'] if previous.get(element['id']) != element],
            'order': [element['id'] for element in new['elements']],
            'files': {key: value for key, value in new['files'].items() if old['files'].get(key) != value},
            'appState': new.get('appState', {}),
        }
    if before['fog_version'] != after['fog_version']:
        update['fog'] = after['fog']
    return update

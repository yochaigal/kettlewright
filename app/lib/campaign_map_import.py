"""Validate portable map references before any private originals are created."""
import json
import posixpath
from pathlib import PurePosixPath

from werkzeug.exceptions import HTTPException

from app.lib.campaigns import coordinate
from app.lib.content_types import ARTICLE_MAP_KINDS, POINT_TYPES
from app.lib.map_drawing import validate_drawing, validate_node_geometry


def read_json(text, name):
    def mapping(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f'Invalid JSON number: {value}')

    try:
        return json.loads(text, object_pairs_hook=mapping, parse_constant=invalid_constant)
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValueError(f'{name}: invalid JSON ({exc}).') from exc


def prepare_maps(payload, files):
    rows = payload['rows']
    ids = {row['id']: i for i, row in enumerate(rows) if row['id']}
    used, warnings = set(), []
    payload['warnings'] = warnings
    payload['links'] = []
    payload['reference_bindings'] = []
    manifests = [name for name in files if PurePosixPath(name).name == 'manifest.json']
    if len(manifests) > 1:
        raise ValueError('Use one campaign manifest per archive.')
    base = (str(PurePosixPath(manifests[0]).parent) if manifests else
            posixpath.commonpath([str(PurePosixPath(name).parent) for name in files]))

    def path_for(reference):
        if not isinstance(reference, str) or not reference:
            raise ValueError('Map filenames must be nonempty strings.')
        path = PurePosixPath(reference)
        if path.is_absolute() or '..' in path.parts or any(c in reference for c in ('\\', ':', '\x00')):
            raise ValueError(f'Unsafe map reference: {reference}')
        name = str(PurePosixPath(base) / path)
        if path.suffix.lower() not in ('.json', '.excalidraw'):
            raise ValueError('Maps require JSON or .excalidraw files; export Obsidian drawings to .excalidraw first.')
        if name not in files or files[name] is None:
            raise ValueError(f'Missing map file: {reference}')
        return name

    def article(ref):
        if not isinstance(ref, str) or ref not in ids or rows[ids[ref]]['category'] == 'campaign':
            raise ValueError(f'Unknown article ID: {ref}')
        return ids[ref]

    def campaign_root(i):
        while rows[i]['parent'] is not None:
            i = rows[i]['parent']
        return i if rows[i]['category'] == 'campaign' else None

    def same_campaign(source, target):
        if campaign_root(source) != campaign_root(target):
            raise ValueError('Map and link references must stay within the same campaign.')

    manifest = {}
    if manifests:
        name = manifests[0]
        manifest = read_json(files[name], name)
        if not isinstance(manifest, dict) or manifest.get('format') != 'kettlewright-campaign' or type(manifest.get('version')) is not int or manifest['version'] != 1:
            raise ValueError('Unsupported campaign manifest format/version.')
        used.add(name)
    declared = {}
    for i, row in enumerate(rows):
        if row['map_file']:
            if row['category'] == 'campaign':
                raise ValueError('Attach maps to articles, not Campaign records.')
            declared[i] = path_for(row['map_file'])
    manifest_maps = manifest.get('maps', [])
    if not isinstance(manifest_maps, list) or len(manifest_maps) > 500:
        raise ValueError('Invalid manifest map list.')
    cache = {}

    def load(name):
        if name not in cache:
            cache[name] = read_json(files[name], name)
        if not isinstance(cache[name], dict):
            raise ValueError(f'{name}: map must be a JSON object.')
        return cache[name]

    for reference in manifest_maps:
        name = path_for(reference)
        i = article(load(name).get('article_id'))
        if i in declared and declared[i] != name:
            raise ValueError('Multiple map files for the same article.')
        declared[i] = name

    # Validate every canvas before graph relationships. Nested maps can appear
    # before or after their entrance in archive order.
    for i, name in declared.items():
        raw, row = load(name), rows[i]
        expected = row['kind'] if row['category'] == 'map' else ARTICLE_MAP_KINDS.get(row['category'])
        if expected is None:
            raise ValueError(f'{name}: this article type does not support a map. Use Freeform or a spatial type.')
        scene = raw.get('type') == 'excalidraw'
        if not scene and (raw.get('article_id') != row['id'] or not row['id']):
            raise ValueError(f'{name}: article_id must match the attached article id.')
        kind = expected if scene else raw.get('kind')
        if kind != expected:
            raise ValueError(f'{name}: map kind must match the article type ({expected}).')
        drawing = {'elements': raw.get('elements'), 'files': raw.get('files', {})} if scene else raw.get('drawing')
        try:
            clean_drawing = validate_drawing(drawing)
        except HTTPException as exc:
            raise ValueError(f'{name}: {exc.description}') from exc
        if scene:
            warnings.append(f'{name}: imported as an editable drawing; shapes do not automatically become article points or paths. Obsidian links and canvas settings are not imported.')
        row['map'] = {'file': name, 'kind': kind, 'drawing': clean_drawing, 'nodes': [], 'edges': []}
        used.add(name)

    used_path_articles = set()
    for i, name in declared.items():
        raw, graph = load(name), rows[i]['map']
        if raw.get('type') == 'excalidraw':
            continue
        nodes, edges = raw.get('nodes', []), raw.get('edges', [])
        if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes) > 200 or len(edges) > 800:
            raise ValueError(f'{name}: a map supports up to 200 points and 800 paths.')
        resolved, numbers, entries = {}, set(), set()
        for item in nodes:
            if not isinstance(item, dict):
                raise ValueError(f'{name}: invalid map point.')
            key, number = item.get('id'), item.get('number')
            if not isinstance(key, str) or not key or len(key) > 200 or key in resolved:
                raise ValueError(f'{name}: map point IDs must be unique nonempty strings.')
            if type(number) is not int or number < 1 or number in numbers:
                raise ValueError(f'{name}: point numbers must be positive unique integers.')
            target = article(item.get('article_id'))
            same_campaign(i, target)
            target_category = rows[target]['kind'] if rows[target]['category'] == 'map' and rows[target]['kind'] != 'freeform' else rows[target]['category']
            if target in entries or target_category not in POINT_TYPES | {'location'}:
                raise ValueError(f'{name}: each point must refer to a unique point article.')
            nested = item.get('nested_map')
            nested = article(nested) if nested is not None else None
            if nested is not None:
                same_campaign(i, nested)
                if nested == i or (nested not in declared and rows[nested]['category'] != 'map'):
                    raise ValueError(f'{name}: nested_map must refer to another imported map.')
            try:
                if isinstance(item.get('x'), bool) or isinstance(item.get('y'), bool):
                    raise ValueError('Invalid coordinate.')
                x, y = coordinate(item.get('x')), coordinate(item.get('y'))
                geometry = validate_node_geometry(item.get('geometry'), target_category)
            except HTTPException as exc:
                raise ValueError(f'{name}: {exc.description}') from exc
            node = {'id': key, 'article': target, 'number': number, 'x': x, 'y': y,
                    'geometry': geometry, 'nested_map': nested}
            resolved[key] = node
            numbers.add(number)
            entries.add(target)
            graph['nodes'].append(node)
        pairs = set()
        for item in edges:
            if not isinstance(item, dict) or not isinstance(item.get('source'), str) or not isinstance(item.get('target'), str):
                raise ValueError(f'{name}: invalid map path.')
            source, target = item['source'], item['target']
            pair = tuple(sorted((source, target)))
            if source not in resolved or target not in resolved or source == target or pair in pairs:
                raise ValueError(f'{name}: paths must connect distinct points without duplicate connections.')
            entry = article(item.get('article_id'))
            same_campaign(i, entry)
            if rows[entry]['category'] != 'path' or entry in used_path_articles:
                raise ValueError(f'{name}: a path article must belong to exactly one map edge.')
            used_path_articles.add(entry)
            pairs.add(pair)
            graph['edges'].append({'article': entry, 'source': source, 'target': target})
    links = manifest.get('links', [])
    if not isinstance(links, list) or len(links) > 10000:
        raise ValueError('Invalid article link list.')
    pairs = set()
    for link in links:
        if not isinstance(link, dict):
            raise ValueError('Invalid article link.')
        source, target = article(link.get('source')), article(link.get('target'))
        same_campaign(source, target)
        if source == target or (source, target) in pairs:
            raise ValueError('Article links must be distinct and unique.')
        pairs.add((source, target))
        payload['links'].append({'source': source, 'target': target})
    payload['ignored'].extend(name for name in files if name not in used
        and PurePosixPath(name).suffix.lower() in ('.json', '.excalidraw'))
    references = manifest.get('references', [])
    if not isinstance(references, list) or len(references) > 10000:
        raise ValueError('Invalid article reference list.')
    keys = set()
    from app.lib.article_references import tokens
    for link in references:
        if not isinstance(link, dict):
            raise ValueError('Invalid article reference.')
        source, target = article(link.get('source')), article(link.get('target'))
        same_campaign(source, target)
        token = link.get('token')
        if not isinstance(token, str) or token not in tokens(rows[source]['body']) or (source, token) in keys:
            raise ValueError('Invalid or duplicate article reference token.')
        keys.add((source, token))
        payload['reference_bindings'].append({'source': source, 'target': target, 'token': token})

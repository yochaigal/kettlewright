"""Bounded archive parsing. Never extract paths or resolve references outside a batch."""
import io
import stat
import tarfile
import zipfile
from pathlib import PurePosixPath

import yaml
from werkzeug.exceptions import HTTPException

from app.models import db, Campaign, ContentEntry, PointcrawlMap, MapNode, MapEdge, ContentLink
from app.lib.campaigns import CATEGORIES, MAP_KINDS, PATH_TYPES
from app.lib.rich_content import normalize_content
from app.lib.campaign_map_import import prepare_maps
from app.lib.article_references import prepare_archive_references

MAX_ARCHIVE = 50 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
MAX_FILE = 512 * 1024
MAX_MAP_FILE = 16 * 1024 * 1024
MAX_MEMBERS = 500


class ImportError(ValueError):
    pass


def archive_files(data):
    if len(data) > MAX_ARCHIVE:
        raise ImportError('Archive exceeds 50 MB.')
    stream = io.BytesIO(data)
    total = 0
    seen = set()
    try:
        zipped = zipfile.is_zipfile(stream)
        stream.seek(0)
        with (zipfile.ZipFile(stream) if zipped else tarfile.open(fileobj=stream, mode='r:*')) as archive:
            members = archive.infolist() if zipped else archive
            for count, member in enumerate(members, 1):
                if count > MAX_MEMBERS:
                    raise ImportError('Archive contains more than 500 entries.')
                name = member.filename if zipped else member.name
                path = PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or '\x00' in name:
                    raise ImportError(f'Unsafe archive path: {name}')
                if (member.is_dir() if zipped else member.isdir()):
                    continue
                if (stat.S_ISLNK(member.external_attr >> 16) if zipped else not member.isfile()):
                    raise ImportError(f'Links and special files are not supported: {name}')
                size = member.file_size if zipped else member.size
                total += size
                is_map = path.suffix.lower() in ('.json', '.excalidraw') and path.name != 'manifest.json'
                limit = MAX_MAP_FILE if is_map else MAX_FILE
                if size > limit or total > MAX_TOTAL:
                    raise ImportError('Files exceed the 512 KB Markdown/attachment, 16 MB map or 100 MB total limit.')
                normalized = str(path)
                if normalized in seen:
                    raise ImportError(f'Duplicate archive path: {name}')
                seen.add(normalized)
                if path.suffix.lower() not in ('.md', '.json', '.excalidraw') or name.lower().endswith('.excalidraw.md'):
                    yield name, None
                    continue
                with (archive.open(member) if zipped else archive.extractfile(member)) as file:
                    contents = file.read(limit + 1)
                if len(contents) > limit:
                    raise ImportError(f'File exceeds its size limit: {name}')
                yield normalized, contents.decode('utf-8-sig')
    except (tarfile.TarError, zipfile.BadZipFile, UnicodeError, RuntimeError, OSError, EOFError) as exc:
        raise ImportError('Use a valid ZIP or TAR archive containing UTF-8 Markdown files.') from exc


def parse_markdown(name, text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise ImportError('Missing YAML Front Matter.')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise ImportError('Unclosed Front Matter.')
    header = '\n'.join(lines[1:end])
    if len(header) > 8192:
        raise ImportError('Front Matter exceeds 8 KB.')
    try:
        # This contract is a flat mapping of scalar strings, not arbitrary YAML.
        node = yaml.compose(header, Loader=yaml.BaseLoader)
        if not isinstance(node, yaml.MappingNode):
            raise ImportError('Front Matter must be a mapping.')
        metadata = {}
        for key, value in node.value:
            if not isinstance(key, yaml.ScalarNode) or not isinstance(value, yaml.ScalarNode):
                raise ImportError('Front Matter values must be plain strings.')
            if key.value in metadata:
                raise ImportError(f'Duplicate metadata key: {key.value}')
            metadata[key.value] = value.value.strip()
    except (yaml.YAMLError, RecursionError) as exc:
        raise ImportError('Invalid YAML Front Matter.') from exc
    for key in ('layout', 'title', 'type'):
        if not metadata.get(key):
            raise ImportError(f'Missing {key}.')
    if metadata['layout'] != 'default':
        raise ImportError('layout must be default.')
    if len(metadata['title']) > 200:
        raise ImportError('Title exceeds 200 characters.')
    kind = metadata['type'].casefold()
    aliases = {label.casefold(): key for key, label in CATEGORIES.items()}
    aliases.update({key: key for key in CATEGORIES})
    aliases.update({'npcs': 'npc', 'factions': 'faction', 'settlements': 'settlement',
                    'waypoints': 'waypoint', 'curiosities': 'curiosity', 'lairs': 'lair'})
    aliases.update({'location': 'custom', 'locations': 'custom', 'article': 'custom', 'gear': 'item', 'weapon': 'item', 'weapons': 'item', 'armor': 'item'})
    category = 'campaign' if kind == 'campaign' else 'map' if kind in MAP_KINDS else aliases.get(kind)
    if category is None:
        raise ImportError(f'Unknown type: {metadata["type"]}')
    if category == 'campaign' and metadata.get('parent'):
        raise ImportError('A Campaign cannot have a parent.')
    if category == 'campaign' and metadata.get('parent_id'):
        raise ImportError('A Campaign cannot have a parent.')
    if metadata.get('heart', 'false').casefold() not in ('true', 'false'):
        raise ImportError('heart must be true or false.')
    if metadata.get('path_type', 'standard') not in PATH_TYPES:
        raise ImportError('Unknown path_type.')
    source_path = metadata.get('source_path', name)
    path = PurePosixPath(source_path)
    if len(source_path) > 500 or path.is_absolute() or '..' in path.parts or any(c in source_path for c in ('\\', ':', '\x00')):
        raise ImportError('Invalid source_path.')
    try:
        body = normalize_content('\n'.join(lines[end + 1:]).strip())
    except HTTPException as exc:
        raise ImportError(exc.description) from exc
    return {'file': name, 'title': metadata['title'], 'type': metadata['type'],
            'category': category, 'kind': kind if kind in MAP_KINDS else 'freeform',
            'parent_title': metadata.get('parent', ''), 'parent': None,
            'id': metadata.get('id', ''), 'parent_id': metadata.get('parent_id', ''),
            'is_heart': metadata.get('heart', 'false').casefold() == 'true',
            'path_type': metadata.get('path_type', 'standard'),
            'map_file': metadata.get('map', ''),
            'source_path': str(path),
            'body': body}


def preview_archive(data):
    rows, errors, ignored, files = [], [], [], {}
    for name, text in archive_files(data):
        files[name] = text
        if text is None:
            ignored.append(name)
            continue
        if PurePosixPath(name).suffix.lower() != '.md':
            continue
        try:
            rows.append(parse_markdown(name, text))
        except ImportError as exc:
            errors.append(f'{name}: {exc}')
    if not rows and not errors:
        errors.append('No Markdown files found.')
    titles, ids = {}, {}
    for i, row in enumerate(rows):
        titles.setdefault(row['title'], []).append(i)
        if row['id']:
            if row['id'] in ids:
                errors.append(f'{row["file"]}: duplicate id "{row["id"]}".')
            ids[row['id']] = i
    for row in rows:
        if row['parent_id']:
            if row['parent_id'] not in ids:
                errors.append(f'{row["file"]}: parent_id "{row["parent_id"]}" is missing.')
            else:
                row['parent'] = ids[row['parent_id']]
        elif row['parent_title']:
            matches = titles.get(row['parent_title'], [])
            if len(matches) != 1:
                errors.append(f'{row["file"]}: parent "{row["parent_title"]}" is missing or ambiguous.')
            else:
                row['parent'] = matches[0]
    order = []
    visited, active = set(), set()

    def visit(i, depth=0):
        if i in active or depth > 20:
            raise ImportError('Hierarchy contains a cycle or exceeds 20 levels.')
        if i in visited:
            return
        active.add(i)
        row = rows[i]
        parent = row['parent']
        if parent is not None:
            visit(parent, depth + 1)
            row['destination'] = rows[parent]['destination'] + ' / ' + rows[parent]['title']
            row['depth'] = rows[parent]['depth'] + 1
        else:
            row['destination'] = 'Campaigns' if row['category'] == 'campaign' else 'Unfiled articles'
            row['depth'] = 0
        if row['depth'] > 20:
            raise ImportError('Hierarchy exceeds 20 levels.')
        active.remove(i)
        visited.add(i)
        order.append(i)

    try:
        for i in range(len(rows)):
            visit(i)
    except ImportError as exc:
        errors.append(str(exc))
    # Depth-first display puts siblings together, irrespective of archive ordering.
    children = {i: [] for i in range(len(rows))}
    for i, row in enumerate(rows):
        if row['parent'] is not None:
            children[row['parent']].append(i)
    display = []
    def show(i):
        display.append(i)
        for child in children[i]:
            show(child)
    if not errors:
        for i, row in enumerate(rows):
            if row['parent'] is None:
                show(i)
    payload = {'rows': rows, 'order': order, 'display': display, 'errors': errors, 'ignored': ignored}
    if not errors:
        try:
            prepare_maps(payload, files)
            prepare_archive_references(payload)
        except ValueError as exc:
            errors.append(str(exc))
    return payload


def import_preview(payload, owner_id):
    """Caller claims the preview and commits this entire operation atomically."""
    objects, campaigns = {}, {}
    for i in payload['order']:
        row = payload['rows'][i]
        if row['category'] == 'campaign':
            campaign = Campaign(owner_id=owner_id, name=row['title'])
            db.session.add(campaign)
            campaigns[i] = campaign
            if row['body']:
                db.session.add(ContentEntry(owner_id=owner_id, campaign=campaign,
                    title=row['title'], category='overview', body=normalize_content(row['body'])))
            continue
        parent = row['parent']
        campaign = campaigns.get(parent)
        parent_entry = objects.get(parent)
        if parent_entry:
            campaign = parent_entry.campaign
        entry = ContentEntry(owner_id=owner_id, campaign=campaign, parent=parent_entry,
            title=row['title'], category=row['category'], body=normalize_content(row['body']),
            source_path=row.get('source_path', row['file']), references={},
            is_heart=row.get('is_heart', False), path_type=row.get('path_type', 'standard'))
        db.session.add(entry)
        graph = row.get('map')
        if graph or row['category'] == 'map':
            db.session.add(PointcrawlMap(entry=entry, kind=graph['kind'] if graph else row['kind'],
                                         drawing=graph['drawing'] if graph else None))
            if row['kind'] != 'freeform':
                entry.category = row['kind']
        objects[i] = entry
    # Create all articles and canvases before resolving graph references. Archive
    # identifiers are never interpreted as existing database identifiers.
    db.session.flush()
    for i, entry in objects.items():
        entry.references = {token: objects[target].reference_key for token, target in payload['rows'][i].get('references', {}).items()}
    for i, entry in objects.items():
        graph = payload['rows'][i].get('map')
        if not graph:
            continue
        nodes = {}
        for item in graph['nodes']:
            node = MapNode(map=entry.pointcrawl, entry=objects[item['article']],
                number=item['number'], x=item['x'], y=item['y'], geometry=item['geometry'],
                nested_map=objects[item['nested_map']].pointcrawl if item['nested_map'] is not None else None)
            db.session.add(node)
            nodes[item['id']] = node
        db.session.flush()
        for item in graph['edges']:
            db.session.add(MapEdge(map=entry.pointcrawl, entry=objects[item['article']],
                source_id=nodes[item['source']].id, target_id=nodes[item['target']].id))
    for link in payload.get('links', []):
        db.session.add(ContentLink(source_id=objects[link['source']].id, target_id=objects[link['target']].id))
    return len(campaigns), len(objects)

"""Bounded archive parsing. Never extract paths or resolve references outside a batch."""
import io
import re
import stat
import tarfile
import zipfile
from pathlib import PurePosixPath

import yaml
from werkzeug.exceptions import HTTPException, Conflict

from app.models import db, Campaign, ContentEntry, PointcrawlMap, MapNode, MapEdge, ContentLink
from app.lib.campaigns import CATEGORIES, MAP_KINDS, PATH_TYPES
from app.lib.rich_content import normalize_content
from app.lib.campaign_map_import import prepare_maps
from app.lib.article_references import prepare_archive_references
from app.lib.campaign_backgrounds import BackgroundError, add_backgrounds, background_from_markdown

MAX_ARCHIVE = 50 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
MAX_FILE = 512 * 1024
MAX_MAP_FILE = 16 * 1024 * 1024
MAX_MEMBERS = 500

# Errors from parse_markdown that indicate missing/incomplete frontmatter.
# These trigger automatic metadata inference rather than a hard error.
_INFERABLE_ERRORS = frozenset({
    'Missing YAML Front Matter.',
    'Unclosed Front Matter.',
    'Missing layout.',
    'Missing title.',
    'Missing type.',
})


class ImportError(ValueError):
    pass


MAP_BLOCK = re.compile(r'^```kettlewright-map[ \t]*\n(.*?)\n```[ \t]*$', re.M | re.S)


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
                is_map = ((path.suffix.lower() in ('.json', '.excalidraw') and path.name != 'manifest.json')
                          or (path.suffix.lower() == '.md' and 'maps' in path.parts[:-1]))  # A map file (format 2).
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
    if len(header) > 65536:
        raise ImportError('Front Matter exceeds 64 KB.')
    try:
        # This contract is a flat mapping of scalar strings, not arbitrary YAML. Only links (a list of
        # ids) and references (link text: id) hold more, and only plain strings.
        node = yaml.compose(header, Loader=yaml.BaseLoader)
        if not isinstance(node, yaml.MappingNode):
            raise ImportError('Front Matter must be a mapping.')
        metadata, links, references = {}, [], {}
        for key, value in node.value:
            if not isinstance(key, yaml.ScalarNode):
                raise ImportError('Front Matter values must be plain strings.')
            if key.value in metadata or (key.value == 'links' and links) or (key.value == 'references' and references):
                raise ImportError(f'Duplicate metadata key: {key.value}')
            if key.value == 'links' and isinstance(value, yaml.SequenceNode):
                if len(value.value) > 1000 or not all(isinstance(item, yaml.ScalarNode) for item in value.value):
                    raise ImportError('links must be a list of ids.')
                links = [item.value.strip() for item in value.value]
                continue
            if key.value == 'references' and isinstance(value, yaml.MappingNode):
                if len(value.value) > 1000 or not all(isinstance(k, yaml.ScalarNode) and isinstance(v, yaml.ScalarNode)
                                                      for k, v in value.value):
                    raise ImportError('references must map link text to ids.')
                references = {k.value: v.value.strip() for k, v in value.value}
                continue
            if not isinstance(value, yaml.ScalarNode):
                raise ImportError('Front Matter values must be plain strings.')
            metadata[key.value] = value.value.strip()
    except (yaml.YAMLError, RecursionError) as exc:
        raise ImportError('Invalid YAML Front Matter.') from exc
    for key in ('layout', 'title', 'type'):
        if not metadata.get(key):
            raise ImportError(f'Missing {key}.')
    if metadata['layout'] != 'default':
        raise ImportError('layout must be default.')
    if metadata.get('format') and (metadata['format'] != 'kettlewright-module' or metadata.get('version') not in ('1', '2')):
        raise ImportError('Unsupported module format or version.')
    if len(metadata['title']) > 200:
        raise ImportError('Title exceeds 200 characters.')
    kind = metadata['type'].casefold()
    aliases = {label.casefold(): key for key, label in CATEGORIES.items()}
    aliases.update({key: key for key in CATEGORIES})
    aliases.update({'npcs': 'npc', 'factions': 'faction', 'settlements': 'settlement',
                    'waypoints': 'waypoint', 'curiosities': 'curiosity', 'lairs': 'lair'})
    aliases.update({'location': 'custom', 'locations': 'custom', 'article': 'custom', 'gear': 'item', 'weapon': 'item', 'weapons': 'item', 'armor': 'item'})
    # A module's front page: type Campaign, or Module. Backgrounds are character options, not articles.
    category = ('campaign' if kind in ('campaign', 'module') else 'background' if kind in ('background', 'backgrounds')
                else 'map' if kind in MAP_KINDS or kind == 'map' else aliases.get(kind))
    if category is None:
        raise ImportError(f'Unknown type: {metadata["type"]}')
    map_block = None
    if kind == 'map':
        # A map file (format 2): type: Map, map_type, and its points, paths and drawing in one fenced block.
        kind = metadata.get('map_type', 'freeform').casefold()
        if kind not in MAP_KINDS:
            raise ImportError(f'Unknown map_type: {metadata.get("map_type")}')
        blocks = MAP_BLOCK.findall('\n'.join(lines[end + 1:]))
        if len(blocks) > 1:
            raise ImportError('A map file has one kettlewright-map block.')
        map_block = blocks[0] if blocks else None
    elif metadata.get('article'):
        raise ImportError('article belongs to a map file (type: Map).')
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
        # A background's body is its own small format (campaign_backgrounds), read as written. A map file's
        # body is its map: maps have no text of their own.
        body = '\n'.join(lines[end + 1:]).strip()
        body = '' if kind_is_map_file(metadata) else body if category == 'background' else normalize_content(body)
    except HTTPException as exc:
        raise ImportError(exc.description) from exc
    return {'file': name, 'title': metadata['title'], 'type': metadata['type'],
            'category': category, 'kind': kind if kind in MAP_KINDS else 'freeform',
            'parent_title': metadata.get('parent', ''), 'parent': None,
            'id': metadata.get('id', ''), 'parent_id': metadata.get('parent_id', ''),
            'is_heart': metadata.get('heart', 'false').casefold() == 'true',
            'path_type': metadata.get('path_type', 'standard'),
            'map_file': metadata.get('map', ''),
            'map_block': map_block, 'attach_to': metadata.get('article', ''),
            'format_version': metadata.get('version', '') if category == 'campaign' and metadata.get('format') else '',
            'links': links, 'reference_ids': references,
            'source_path': str(path),
            'body': body}


def kind_is_map_file(metadata):
    return metadata['type'].casefold() == 'map'


def infer_metadata(name, text):
    """Infer article metadata from a Markdown file without valid frontmatter.

    Extracts the title from the first level-1 heading, falling back to the
    filename stem. The article type defaults to 'Note'.
    """
    lines = text.splitlines()
    # Skip any partial frontmatter block so we don't treat YAML keys as headings.
    start = 0
    if lines and lines[0].strip() == '---':
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
        start = (end + 1) if end is not None else len(lines)
    body_lines = lines[start:]
    title = None
    first = next((i for i, line in enumerate(body_lines) if line.strip()), None)
    for i, line in enumerate(body_lines):
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:].strip()[:200] or None
            # A leading heading is the title; drop it so it isn't repeated in the body.
            if title and i == first:
                body_lines = body_lines[i + 1:]
            break
    if not title:
        stem = PurePosixPath(name).stem
        title = (stem.replace('-', ' ').replace('_', ' ').title())[:200] or 'Untitled'
    body_text = '\n'.join(body_lines).strip()
    try:
        body = normalize_content(body_text)
    except HTTPException as exc:
        raise ImportError(exc.description) from exc
    return {
        'file': name, 'title': title, 'type': 'Note', 'category': 'note', 'kind': 'freeform',
        'parent_title': '', 'parent': None, 'id': '', 'parent_id': '',
        'is_heart': False, 'path_type': 'standard', 'map_file': '',
        'source_path': name, 'body': body,
    }


def single_file_preview(data, filename, owner_id=None):
    """Preview one Markdown file using the same rules as an archive member."""
    if len(data) > MAX_FILE:
        raise ImportError('File exceeds 512 KB.')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ImportError('File must be UTF-8 encoded.') from exc
    return preview_files([(PurePosixPath(filename).name, text)], owner_id)


def preview_archive(data, owner_id=None):
    return preview_files(archive_files(data), owner_id)


def preview_files(entries, owner_id=None):
    """Stage (name, text) pairs; text is None for files that are skipped."""
    rows, errors, warnings, ignored, files = [], [], [], [], {}
    backgrounds = {}
    for name, text in entries:
        files[name] = text
        if text is None:
            ignored.append(name)
            continue
        if is_backgrounds_file(name):
            # Backgrounds are Markdown files (type: Background), like everything people write.
            errors.append(f'{name}: backgrounds are Markdown files (type: Background), not JSON.')
            continue
        if PurePosixPath(name).suffix.lower() != '.md':
            continue
        try:
            row = parse_markdown(name, text)
            if row['category'] == 'background':
                found = dict([background_from_markdown(row['title'], row['body'])])
                for title in set(found) & set(backgrounds):
                    errors.append(f'{name}: background "{title}" is defined twice.')
                backgrounds.update(found)
                continue
            rows.append(row)
        except BackgroundError as exc:
            errors.append(f'{name}: {exc}')
        except ImportError as exc:
            if str(exc) not in _INFERABLE_ERRORS:
                errors.append(f'{name}: {exc}')
                continue
            try:
                row = infer_metadata(name, text)
            except ImportError as inner:
                errors.append(f'{name}: {inner}')
                continue
            row['inferred'] = True
            rows.append(row)
            warnings.append(f'{name}: No metadata found. Defaults applied: '
                            f'title "{row["title"]}", type "{row["type"]}". You can change them below.')
    if any(row.get('format_version') == '2' for row in rows):
        # Format 2: only map files (type: Map) are maps. A Realm, Dungeon or Forest article is an article
        # (older archives made every such article a map).
        for row in rows:
            if row['category'] == 'map' and row['type'].casefold() != 'map':
                row['category'] = row['kind'] if row['kind'] != 'freeform' else 'topography'
    # Format 2 map files: the block is the map; a map of an article (article: id) goes on that article.
    by_id = {row['id']: row for row in rows if row['id']}
    for row in list(rows):
        if row.get('map_block') is not None:
            virtual = f'{row["file"]}#map'
            files[virtual], row['map_block'] = row['map_block'], None  # Read once, from files, like a sidecar.
            if row['attach_to']:
                target = by_id.get(row['attach_to'])
                if target is None or target['category'] in ('campaign', 'map') or target.get('map_file'):
                    errors.append(f'{row["file"]}: article "{row["attach_to"]}" is missing or already has a map.')
                else:
                    target['map_file'] = virtual
                rows.remove(row)
            else:
                row['map_file'] = virtual
    if not rows and not backgrounds and not errors:
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
            if not matches:
                # Everything is imported into one module: a parent outside it (say, a campaign's name) is dropped.
                warnings.append(f'{row["file"]}: parent "{row["parent_title"]}" is not in this module; '
                                'it is imported at the top level of the module.')
            elif len(matches) != 1:
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
            row['destination'] = 'Module'
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
    payload = {'rows': rows, 'order': order, 'display': display, 'errors': errors, 'warnings': warnings, 'ignored': ignored,
               'backgrounds': backgrounds,
               # Links and [[link]] targets written in each file's front matter (format 2), by id.
               'front_links': [{'source': row['id'], 'target': target} for row in rows for target in row.get('links', [])],
               'front_references': [{'source': row['id'], 'token': token, 'target': target}
                                    for row in rows for token, target in row.get('reference_ids', {}).items()]}
    if not errors and rows:
        try:
            prepare_maps(payload, files)
            prepare_archive_references(payload)
        except ValueError as exc:
            errors.append(str(exc))
    return payload


# Inferred rows have no parent or map, so any plain article type is safe to choose.
EDITABLE_CATEGORIES = frozenset(CATEGORIES) - {'map', 'overview'}


def apply_overrides(payload, form):
    """Apply title/type corrections the user made to rows with inferred metadata."""
    for i, row in enumerate(payload['rows']):
        if not row.get('inferred'):
            continue
        title = (form.get(f'title_{i}') or '').strip()
        if title:
            if len(title) > 200:
                raise ImportError('Title exceeds 200 characters.')
            row['title'] = title
        category = form.get(f'category_{i}')
        if category:
            if category not in EDITABLE_CATEGORIES:
                raise ImportError(f'Unknown type: {category}')
            row['category'], row['type'] = category, CATEGORIES[category]
    return payload


def is_backgrounds_file(name):
    path = PurePosixPath(name)
    return path.suffix.lower() == '.json' and (path.name.lower() == 'backgrounds.json' or path.parent.name.lower() == 'backgrounds')


def module_title(payload, fallback=''):
    """The module's name: the title of its campaign (front page) file."""
    return next((row['title'] for row in payload['rows'] if row['category'] == 'campaign'), fallback)


def import_preview(payload, owner_id, into=None, slug='', module=None, name=''):
    """Import a staged module. Caller claims the preview and commits this entire operation atomically.

    Everything goes into one module of a campaign: module (add files to an existing module), else a
    new module of into (one of the owner's campaigns), else a new campaign (with its party) named after
    the module. The module's front page becomes an Overview article; its backgrounds join the module.
    slug names a bundled module. Returns (new campaigns, articles)."""
    from app.models import Module
    objects = {}
    payload.setdefault('backgrounds', {})
    title = module_title(payload, name or 'Imported module')
    created = 0
    if module is not None:
        into = module.campaign
    elif into is None:
        from app.lib.campaign_parties import create_campaign
        into = create_campaign(owner_id, title)
        created = 1
    if module is None:
        module = Module(campaign=into, title=title[:200], slug=slug)
        db.session.add(module)
    for i in payload['order']:
        row = payload['rows'][i]
        if row['category'] == 'campaign':
            if row['body']:
                db.session.add(ContentEntry(owner_id=owner_id, campaign=into, module=module,
                    title=row['title'], category='overview', body=normalize_content(row['body'])))
            continue
        parent = row['parent']
        parent_entry = objects.get(parent)
        entry = ContentEntry(owner_id=owner_id, campaign=into, module=module, parent=parent_entry,
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
            elif row['category'] == 'map':
                entry.category = 'topography'
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
    if payload['backgrounds']:
        add_backgrounds(module, payload['backgrounds'])
    return created, len(objects)

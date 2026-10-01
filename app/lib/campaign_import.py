"""Bounded archive parsing. Never extract paths or resolve references outside a batch."""
import io
import stat
import tarfile
import zipfile
from pathlib import PurePosixPath

import yaml
from werkzeug.exceptions import HTTPException

from app.models import db, Campaign, ContentEntry, PointcrawlMap
from app.lib.campaigns import CATEGORIES, MAP_KINDS
from app.lib.rich_content import normalize_content

MAX_ARCHIVE = 10 * 1024 * 1024
MAX_TOTAL = 20 * 1024 * 1024
MAX_FILE = 512 * 1024
MAX_MEMBERS = 500


class ImportError(ValueError):
    pass


def archive_files(data):
    if len(data) > MAX_ARCHIVE:
        raise ImportError('Archive exceeds 10 MB.')
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
                if size > MAX_FILE or total > MAX_TOTAL:
                    raise ImportError('Files exceed the 512 KB per-file or 20 MB total limit.')
                normalized = str(path)
                if normalized in seen:
                    raise ImportError(f'Duplicate archive path: {name}')
                seen.add(normalized)
                if path.suffix.lower() != '.md':
                    yield name, None
                    continue
                with (archive.open(member) if zipped else archive.extractfile(member)) as file:
                    contents = file.read(MAX_FILE + 1)
                if len(contents) > MAX_FILE:
                    raise ImportError(f'File exceeds 512 KB: {name}')
                yield name, contents.decode('utf-8-sig')
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
    aliases.update({'article': 'custom', 'gear': 'item', 'weapon': 'item', 'weapons': 'item', 'armor': 'item'})
    category = 'campaign' if kind == 'campaign' else 'map' if kind in MAP_KINDS else aliases.get(kind)
    if category is None:
        raise ImportError(f'Unknown type: {metadata["type"]}')
    if category == 'campaign' and metadata.get('parent'):
        raise ImportError('A Campaign cannot have a parent.')
    try:
        body = normalize_content('\n'.join(lines[end + 1:]).strip())
    except HTTPException as exc:
        raise ImportError(exc.description) from exc
    return {'file': name, 'title': metadata['title'], 'type': metadata['type'],
            'category': category, 'kind': kind if kind in MAP_KINDS else 'freeform',
            'parent_title': metadata.get('parent', ''), 'parent': None,
            'body': body}


def preview_archive(data):
    rows, errors, ignored = [], [], []
    for name, text in archive_files(data):
        if text is None:
            ignored.append(name)
            continue
        try:
            rows.append(parse_markdown(name, text))
        except ImportError as exc:
            errors.append(f'{name}: {exc}')
    if not rows and not errors:
        errors.append('No Markdown files found.')
    titles = {}
    for i, row in enumerate(rows):
        titles.setdefault(row['title'], []).append(i)
    for row in rows:
        if row['parent_title']:
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
    return {'rows': rows, 'order': order, 'display': display, 'errors': errors, 'ignored': ignored}


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
            title=row['title'], category=row['category'], body=normalize_content(row['body']))
        db.session.add(entry)
        if row['category'] == 'map':
            db.session.add(PointcrawlMap(entry=entry, kind=row['kind']))
        objects[i] = entry
    return len(campaigns), len(objects)

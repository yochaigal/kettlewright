"""Portable modules: an archive of Markdown files, one folder per module part (format 2)."""
import io
import json
import zipfile

import yaml
from sqlalchemy.orm import selectinload

from app.models import ContentEntry, PointcrawlMap
from app.lib.article_references import bind_references
from pathlib import PurePosixPath


def markdown_file(metadata, body=''):
    header = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
    return f'---\n{header}\n---\n{body or ""}\n'


def _entries(owner_id, **scope):
    # Query the owner as well as the campaign or module: never export another owner's data
    # even if a corrupt record or cross-campaign reference exists.
    return ContentEntry.query.filter_by(owner_id=owner_id, **scope).options(selectinload(ContentEntry.links),
            selectinload(ContentEntry.pointcrawl).selectinload(PointcrawlMap.nodes),
            selectinload(ContentEntry.pointcrawl).selectinload(PointcrawlMap.edges)
        ).order_by(ContentEntry.id).all()


MAP_BLOCK = 'kettlewright-map'


def _slug_paths(folder, titles):
    """Readable, unique file names: folder/the-title.md."""
    from slugify import slugify
    used, paths = set(), []
    for title in titles:
        base = slugify(title or '')[:80] or folder.rstrip('s')
        stem, counter = base, 1
        while stem in used:
            stem, counter = f'{base}-{counter}', counter + 1
        used.add(stem)
        paths.append(f'{folder}/{stem}.md')
    return paths


def export_campaign(campaign):
    return export_archive(campaign.name, 'Campaign', _entries(campaign.owner_id, campaign_id=campaign.id))


def export_module(module):
    """A module as an archive of Markdown files that imports again, one folder per part (see MODULE_PARTS)."""
    return export_archive(module.title, 'Module', _entries(module.campaign.owner_id, module_id=module.id),
                          module.backgrounds or {}, module.items or {}, description=module.description)


def background_files(backgrounds):
    from app.lib.campaign_backgrounds import background_markdown
    names = sorted(backgrounds)
    for name, path in zip(names, _slug_paths('backgrounds', names)):
        yield path, background_markdown(name, backgrounds[name])


def map_markdown(metadata, graph):
    """A map file: its metadata, then its drawing, points and paths in one fenced block (read back on import)."""
    block = json.dumps(graph, ensure_ascii=False, indent=2, allow_nan=False)
    return markdown_file(metadata, f'Points, paths and drawing of this map. Edit the map in Kettlewright.\n\n'
                                   f'```{MAP_BLOCK}\n{block}\n```')


def export_archive(title, front_type, entries, backgrounds=None, items=None, description=''):
    """Format 2: every file is Markdown with YAML front matter. One folder per module part:

    module.md (type: Module, the front page), maps/*.md (type: Map), articles/*.md (their own types) and
    backgrounds/*.md (type: Background) and items/items.md (type: Items). Ids tie them together: parent_id, links, references, and a
    map's points and paths. There is no manifest: each file carries its own metadata.

    description: the module's front page. Without one, an Overview article named after it is the front page
    (campaigns, and modules added before the front page became the description)."""
    from app.lib.campaigns import map_only
    front = None if description else next((entry for entry in entries if entry.category == 'overview' and entry.title == title
                                           and entry.parent_id is None and not entry.pointcrawl), None)
    maps = [entry for entry in entries if map_only(entry)]
    articles = [entry for entry in entries if entry is not front and not map_only(entry)]
    ids = {entry.id: f'map-{i:04d}' for i, entry in enumerate(maps, 1)}
    ids.update({entry.id: f'article-{i:04d}' for i, entry in enumerate(articles, 1)})
    reference_ids = {entry.reference_key: ids[entry.id] for entry in entries if entry.id in ids}
    canvases = {entry.pointcrawl.id: ids[entry.id] for entry in entries if entry.pointcrawl and entry.id in ids}
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('module.md', markdown_file({
            'layout': 'default', 'title': title, 'type': front_type,
            'format': 'kettlewright-module', 'version': 2}, description or (front.body if front else '')))
        for filename, text in background_files(backgrounds or {}):
            archive.writestr(filename, text)
        if items:
            from app.lib.module_items import items_file
            archive.writestr('items/items.md', items_file('Items', items))

        def common(entry):
            metadata = {'layout': 'default', 'id': ids[entry.id], 'title': entry.title}
            if entry.parent_id in ids:
                metadata['parent_id'] = ids[entry.parent_id]
            return metadata

        def graph(entry):
            pointcrawl = entry.pointcrawl
            nodes = {node.id: f'point-{i:04d}' for i, node in enumerate(
                sorted(pointcrawl.nodes, key=lambda node: node.id), 1) if node.entry_id in ids}
            return {'article_id': ids[entry.id], 'kind': pointcrawl.kind, 'drawing': pointcrawl.drawing,
                'nodes': [{'id': nodes[node.id], 'article_id': ids[node.entry_id], 'number': node.number,
                           'x': node.x, 'y': node.y, 'geometry': node.geometry,
                           'nested_map': canvases.get(node.nested_map_id)}
                          for node in sorted(pointcrawl.nodes, key=lambda node: node.id) if node.id in nodes],
                'edges': [{'article_id': ids[edge.entry_id], 'source': nodes[edge.source_id], 'target': nodes[edge.target_id]}
                          for edge in sorted(pointcrawl.edges, key=lambda edge: edge.id)
                          if edge.entry_id in ids and edge.source_id in nodes and edge.target_id in nodes]}

        for entry, filename in zip(maps, _slug_paths('maps', [entry.title for entry in maps])):
            metadata = dict(common(entry), type='Map', map_type=entry.pointcrawl.kind)
            archive.writestr(filename, map_markdown(metadata, graph(entry)))
        # An article with a map of its own (a dungeon point and its rooms): its map is a map file too.
        owned = [entry for entry in articles if entry.pointcrawl]
        for entry, filename in zip(owned, _slug_paths('maps', [f'{entry.title} map' for entry in owned])):
            metadata = {'layout': 'default', 'title': entry.title, 'type': 'Map', 'map_type': entry.pointcrawl.kind,
                        'article': ids[entry.id]}
            archive.writestr(filename, map_markdown(metadata, graph(entry)))
        used = set()
        slugs = iter(_slug_paths('articles', [entry.title for entry in articles]))
        for entry in articles:
            filename = next(slugs)
            path = PurePosixPath(entry.source_path or '')
            # Keep an imported file's own path when it is safe: relative Markdown links between files still work.
            if (entry.source_path and path.suffix.lower() == '.md' and not path.is_absolute() and '..' not in path.parts
                    and not any(c in entry.source_path for c in ('\\', ':', '\x00')) and path.parts[0] not in ('maps', 'backgrounds', 'items')
                    and str(path) not in used and str(path) != 'module.md'):
                filename = str(path)
            used.add(filename)
            metadata = dict(common(entry), type=entry.category)
            if entry.is_heart:
                metadata['heart'] = 'true'
            if entry.path_type != 'standard':
                metadata['path_type'] = entry.path_type
            if entry.image:
                metadata['image'] = entry.image
            links = [ids[link.target_id] for link in sorted(entry.links, key=lambda link: link.target_id)
                     if link.target_id in ids]
            if links:
                metadata['links'] = links
            references = {token: reference_ids[target] for token, target in
                          bind_references(entry, entry.body, entry.references, entries).items() if target in reference_ids}
            if references:
                metadata['references'] = references
            archive.writestr(filename, markdown_file(metadata, entry.body))
    output.seek(0)
    return output

"""Portable private originals: readable Markdown and versioned map sidecars."""
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


def export_campaign(campaign):
    # Query the owner as well as the campaign: never export another owner's data
    # even if a corrupt record or cross-campaign reference exists.
    entries = ContentEntry.query.filter_by(campaign_id=campaign.id,
        owner_id=campaign.owner_id).options(selectinload(ContentEntry.links),
            selectinload(ContentEntry.pointcrawl).selectinload(PointcrawlMap.nodes),
            selectinload(ContentEntry.pointcrawl).selectinload(PointcrawlMap.edges)
        ).order_by(ContentEntry.id).all()
    ids = {entry.id: f'article-{i:04d}' for i, entry in enumerate(entries, 1)}
    maps = {entry.pointcrawl.id: ids[entry.id] for entry in entries if entry.pointcrawl}
    reference_ids = {entry.reference_key: ids[entry.id] for entry in entries}
    manifest = {'format': 'kettlewright-campaign', 'version': 1,
        'campaign': 'campaign.md', 'articles': [], 'maps': [], 'links': [],
        'warnings': [], 'references': []}
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('campaign.md', markdown_file({
            'layout': 'default', 'id': 'campaign', 'title': campaign.name, 'type': 'Campaign'}))
        filenames = {'campaign.md', 'manifest.json'}
        for entry in entries:
            ref = ids[entry.id]
            path = PurePosixPath(entry.source_path or f'articles/{ref}.md')
            filename = str(path)
            if path.is_absolute() or '..' in path.parts or any(c in filename for c in ('\\', ':', '\x00')) or path.suffix.lower() != '.md' or filename in filenames:
                filename = f'articles/{ref}.md'
            filenames.add(filename)
            metadata = {'layout': 'default', 'id': ref, 'title': entry.title,
                'type': (entry.pointcrawl.kind if entry.pointcrawl else 'Freeform') if entry.category == 'map' else entry.category,
                'parent_id': ids.get(entry.parent_id, 'campaign'),
                'source_path': entry.source_path or filename,
                'heart': 'true' if entry.is_heart else 'false', 'path_type': entry.path_type}
            if entry.parent_id is not None and entry.parent_id not in ids:
                manifest['warnings'].append(f'{ref}: parent outside this campaign omitted.')
            if entry.pointcrawl:
                metadata['map'] = f'maps/{ref}.json'
            archive.writestr(filename, markdown_file(metadata, entry.body))
            manifest['articles'].append(filename)
            manifest['references'].extend({'source': ref, 'token': token, 'target': reference_ids[target]}
                for token, target in bind_references(entry, entry.body, entry.references, entries).items() if target in reference_ids)
            manifest['links'].extend({'source': ref, 'target': ids[link.target_id]}
                for link in sorted(entry.links, key=lambda link: link.target_id) if link.target_id in ids)
            pointcrawl = entry.pointcrawl
            if not pointcrawl:
                continue
            nodes = {node.id: f'node-{i:04d}' for i, node in enumerate(
                sorted(pointcrawl.nodes, key=lambda node: node.id), 1) if node.entry_id in ids}
            graph = {'article_id': ref, 'kind': pointcrawl.kind, 'drawing': pointcrawl.drawing,
                'nodes': [{'id': nodes[node.id], 'article_id': ids[node.entry_id],
                    'number': node.number, 'x': node.x, 'y': node.y, 'geometry': node.geometry,
                    'nested_map': maps.get(node.nested_map_id)}
                    for node in sorted(pointcrawl.nodes, key=lambda node: node.id) if node.id in nodes],
                'edges': [{'article_id': ids[edge.entry_id], 'source': nodes[edge.source_id],
                    'target': nodes[edge.target_id]}
                    for edge in sorted(pointcrawl.edges, key=lambda edge: edge.id)
                    if edge.entry_id in ids and edge.source_id in nodes and edge.target_id in nodes]}
            map_file = f'maps/{ref}.json'
            archive.writestr(map_file, json.dumps(graph, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
            manifest['maps'].append(map_file)
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    output.seek(0)
    return output

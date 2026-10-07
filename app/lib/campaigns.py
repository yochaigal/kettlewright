"""Authorization and explicit player projections for warden content."""
import math
import random
from flask import abort, current_app
from flask_login import current_user

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap, MapNode, MapEdge)
from app.socket_events import party_recipient_ids
from app.lib.map_drawing import EMPTY_DRAWING, validate_drawing, validate_node_geometry
from app.lib.rich_content import normalize_content, render_content, RICH_PREFIX
from app.lib.article_references import private_reference_urls, reference_urls
from app.lib.feature_access import require_party_features, party_features_enabled

from app.lib.content_types import CATEGORIES, POINT_TYPES, ARTICLE_MAP_KINDS, legacy_point_type
PATH_TYPES = ('standard', 'hidden', 'conditional')
MAP_KINDS = ('realm', 'dungeon', 'forest', 'freeform')


def owned(model, object_id):
    obj = db.get_or_404(model, object_id)
    owner_id = obj.entry.owner_id if isinstance(obj, PointcrawlMap) else obj.owner_id
    if owner_id != current_user.id:
        abort(403)
    return obj


def party_access(party_id, editing=False):
    require_party_features(party_id)
    party = db.get_or_404(Party, party_id)
    if (party.owner != current_user.id if editing else current_user.id not in party_recipient_ids(party)):
        abort(403)
    return party


def text_value(value, limit=50000, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        abort(400, 'Invalid or missing text.')
    return value.strip()


def integer(value):
    try:
        if isinstance(value, bool):
            raise ValueError()
        return int(str(value))
    except (TypeError, ValueError):
        abort(400, 'Invalid integer.')


def coordinate(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        abort(400, 'Invalid coordinate.')
    if not math.isfinite(number) or abs(number) > 100000:
        abort(400, 'Invalid coordinate.')
    return number


def check_version(obj, supplied):
    if integer(supplied) != (obj.version if obj else 0):
        abort(409, 'This content changed in another tab. Reload before saving.')


def campaign_for(value):
    return owned(Campaign, integer(value)) if value not in (None, '') else None


def publishable_party(entry, party_id):
    party = party_access(party_id, editing=True)
    if entry.campaign_id and not db.session.get(CampaignParty, (entry.campaign_id, party.id)):
        abort(400, 'Connect this party to the campaign first.')
    return party


def content_value(value):
    return normalize_content(text_value(value, 5 * 1024 * 1024))


def map_related_ids(entry):
    """Structural links follow geometry, including maps created before this feature."""
    targets = set()
    if entry.pointcrawl:
        for node in entry.pointcrawl.nodes:
            targets.add(node.entry_id)
            if node.nested_map:
                targets.add(node.nested_map.entry_id)
    for node in entry.map_nodes:
        if node.nested_map:
            targets.add(node.nested_map.entry_id)
    return targets - {entry.id}


def material_hierarchy(entries):
    """Project existing map containment, without turning POIs into root cards.

    Locations may be reused and legacy maps may contain cycles. Expand each
    original once, keeping subsequent occurrences as navigable references.
    Only entries in the requested owner/workspace scope can enter the tree.
    """
    by_id = {entry.id: entry for entry in entries}
    maps = {pointcrawl.id: pointcrawl.entry_id for pointcrawl in
            PointcrawlMap.query.filter(PointcrawlMap.entry_id.in_(by_id)).all()}
    children = {entry_id: {} for entry_id in by_id}
    contained = set()
    for entry in by_id.values():
        if entry.parent_id in by_id:
            children[entry.parent_id][entry.id] = None
            contained.add(entry.id)
    for node in MapNode.query.filter(MapNode.map_id.in_(maps)).order_by(MapNode.number, MapNode.id):
        if node.entry_id not in by_id:
            continue
        parent_id = by_id[node.entry_id].parent_id
        ancestor, seen = parent_id, set()
        while ancestor in by_id and ancestor not in seen and ancestor != maps[node.map_id]:
            seen.add(ancestor)
            ancestor = by_id[ancestor].parent_id
        grouped = parent_id in by_id and ancestor == maps[node.map_id]
        children[parent_id if grouped else maps[node.map_id]][node.entry_id] = node.number
        contained.add(node.entry_id)
        if node.nested_map_id in maps and maps[node.nested_map_id] != node.entry_id:
            nested_id = maps[node.nested_map_id]
            children[node.entry_id][nested_id] = None
            contained.add(nested_id)
    for edge in MapEdge.query.filter(MapEdge.map_id.in_(maps)):
        if edge.entry_id in by_id:
            parent_id = by_id[edge.entry_id].parent_id
            children[parent_id if parent_id in by_id else maps[edge.map_id]][edge.entry_id] = None
            contained.add(edge.entry_id)
    expanded = set()

    def branch(entry_id, number=None, depth=0):
        item = {'entry': by_id[entry_id], 'number': number, 'children': []}
        if entry_id in expanded or depth >= 20:
            return item
        expanded.add(entry_id)
        item['children'] = [branch(child_id, child_number, depth + 1)
                            for child_id, child_number in children[entry_id].items()]
        return item

    roots = [branch(entry_id) for entry_id in by_id if entry_id not in contained]
    # Keep rootless legacy cycles accessible instead of silently hiding them.
    for entry_id in by_id:
        if entry_id not in expanded:
            roots.append(branch(entry_id))
    return roots


def material_parents(entry):
    parents = {node.map.entry_id: node.map.entry for node in entry.map_nodes}
    if entry.parent:
        parents[entry.parent.id] = entry.parent
    if entry.pointcrawl:
        parents.update({node.entry_id: node.entry for node in entry.pointcrawl.entrances})
    return [parent for _, parent in sorted(parents.items())
            if parent.id != entry.id and parent.owner_id == entry.owner_id
            and parent.campaign_id == entry.campaign_id]


def material_deletion_plan(selected, owner_id, campaign_id):
    """Follow containment, never arbitrary related-material links; tolerate cycles."""
    entries, maps = {}, {}
    pending = list(selected)
    while pending:
        entry = pending.pop()
        if entry.id in entries:
            continue
        if entry.owner_id != owner_id or entry.campaign_id != campaign_id:
            abort(409, 'Linked content belongs to another workspace. Move it before deleting.')
        entries[entry.id] = entry
        pending.extend(entry.children)
        if entry.pointcrawl:
            pointcrawl = entry.pointcrawl
            maps[pointcrawl.id] = pointcrawl
            pending.extend(node.entry for node in pointcrawl.nodes)
            pending.extend(edge.entry for edge in pointcrawl.edges)
            for entrance in pointcrawl.entrances:
                maps[entrance.map_id] = entrance.map
        for node in entry.map_nodes:
            maps[node.map_id] = node.map
            if node.nested_map:
                pending.append(node.nested_map.entry)
            pending.extend(edge.entry for edge in list(node.outgoing) + list(node.incoming))
        for edge in entry.map_edges:
            maps[edge.map_id] = edge.map
    # Even indirect changes to geometry must remain in the authorized workspace.
    if any(m.entry.owner_id != owner_id or m.entry.campaign_id != campaign_id for m in maps.values()):
        abort(409, 'Linked content belongs to another workspace. Move it before deleting.')
    return entries, maps


def delete_material_plan(entries, maps):
    audiences = set()
    for pointcrawl in maps.values():
        audiences.update(entry_audiences(pointcrawl.entry))
        if pointcrawl.entry_id not in entries:
            pointcrawl.version += 1
    for entry in entries.values():
        audiences.update(entry_audiences(entry))
        db.session.delete(entry)
    db.session.commit()
    notify_parties(audiences)


def known_entries(party_id):
    """Only independently published fields; never serialize an ORM original."""
    rows = PartyPresentation.query.filter_by(party_id=party_id, published=True).all()
    known = {row.entry_id: {'id': row.entry_id, 'category': row.entry.category,
                           'reference_key': row.entry.reference_key,
                           'title': row.title, 'body': row.body, 'path_type': row.path_type,
                           'links': [], 'map_id': row.entry.pointcrawl.id if row.entry.pointcrawl else None}
             for row in rows}
    # A path cannot be read indirectly while its map or either endpoint is hidden.
    for row in rows:
        if row.entry.category == 'path':
            edges = row.entry.map_edges
            if edges and not any(edge.map.entry_id in known and
                    db.session.get(MapNode, edge.source_id).entry_id in known and
                    db.session.get(MapNode, edge.target_id).entry_id in known for edge in edges):
                known.pop(row.entry_id, None)
    for row in rows:
        if row.entry_id in known:
            known[row.entry_id]['references'] = reference_urls(row.body, row.references, known, party_id)
            known[row.entry_id]['links'] = [
                {'id': target_id, 'title': known[target_id]['title']}
                for target_id in sorted({link.target_id for link in row.entry.links} | map_related_ids(row.entry))
                if target_id in known]
    for entry in known.values():
        entry.pop('reference_key', None)
    return known


def map_projection(pointcrawl, party_id=None):
    known = known_entries(party_id) if party_id is not None else None
    if known is not None and pointcrawl.entry_id not in known:
        abort(404)

    def content(entry):
        if known is not None:
            return known.get(entry.id)
        return {'id': entry.id, 'title': entry.title, 'body': entry.body, 'path_type': entry.path_type,
                'references': private_reference_urls(entry)}

    root = content(pointcrawl.entry)
    result = {'id': pointcrawl.id, 'kind': pointcrawl.kind, 'title': root['title'], 'body': root['body'], 'nodes': [], 'edges': []}
    if party_id is None:
        result['drawing'] = pointcrawl.drawing or EMPTY_DRAWING
    else:
        publication = PartyPresentation.query.filter_by(entry_id=pointcrawl.entry_id, party_id=party_id, published=True).first_or_404()
        result['drawing'] = publication.drawing or EMPTY_DRAWING
    if known is None:
        result.update(version=pointcrawl.version, kind=pointcrawl.kind)
        result['has_contents'] = bool(pointcrawl.entry.children or pointcrawl.nodes or pointcrawl.edges
                                      or (pointcrawl.drawing or {}).get('elements'))
        if pointcrawl.kind == 'realm':
            result['article_version'] = pointcrawl.entry.version
            result['realm_sections'] = [child.category for child in pointcrawl.entry.children
                                        if child.category in ('topography', 'pois', 'paths')]
    for node in sorted(pointcrawl.nodes, key=lambda n: (n.number, n.id)):
        item = content(node.entry)
        if item is None:
            continue
        nested = node.nested_map or node.entry.pointcrawl
        result['nodes'].append({'id': node.id, 'entry_id': node.entry_id,
            **({'entry_version': node.entry.version} if known is None else {}),
            **({'has_contents': bool(node.entry.children or (nested and (nested.nodes or nested.edges
                or (nested.drawing or {}).get('elements'))))} if known is None else {}),
            'number': node.number, 'x': node.x, 'y': node.y,
            'geometry': node.geometry,
            'category': node.entry.category if known is None else item['category'],
            **({'is_heart': node.entry.is_heart} if known is None else {}),
            'title': item['title'], 'body': item['body'],
            'references': item.get('references', {}),
            'nested_map_id': nested.id if nested and (known is None or nested.entry_id in known) else None,
            'nested_entry_id': nested.entry_id if nested and (known is None or nested.entry_id in known) else None})
    visible = {node['id'] for node in result['nodes']}
    # Expose the seed relationship only when both articles are visible.
    terrain_nodes = {node.entry_id: node.id for node in pointcrawl.nodes
                     if node.id in visible and node.entry.category == 'terrain'}
    parents = {node.id: node.entry.parent_id for node in pointcrawl.nodes}
    for node in result['nodes']:
        if node['category'] == 'landmark' and parents[node['id']] in terrain_nodes:
            node['terrain_id'] = terrain_nodes[parents[node['id']]]
    for edge in pointcrawl.edges:
        item = content(edge.entry)
        if item is not None and edge.source_id in visible and edge.target_id in visible:
            result['edges'].append({'id': edge.id, 'entry_id': edge.entry_id,
                **({'entry_version': edge.entry.version} if known is None else {}),
                'source': edge.source_id, 'target': edge.target_id,
                'title': item['title'], 'body': item['body'], 'path_type': item['path_type'],
                'references': item.get('references', {})})
    return result


def notify_parties(party_ids):
    from app import socketio
    for party_id in set(party_ids):
        if not party_features_enabled(party_id):
            continue
        party = db.session.get(Party, party_id)
        if party is None:
            continue
        for user_id in party_recipient_ids(party):
            try:
                socketio.emit('campaign_content_changed', {'party_id': party.id}, room=f'user_{user_id}')
            except Exception:
                current_app.logger.exception('Unable to notify party about published content')


def entry_audiences(entry):
    return {p.party_id for p in entry.presentations if p.published}


def save_geometry(pointcrawl, data, *, nested_draft=False):
    """Save geometry and explicitly edited private cards with separate version checks."""
    check_version(pointcrawl, data.get('version'))
    if 'drawing' in data:
        pointcrawl.drawing = validate_drawing(data['drawing'])
    nodes, edges = data.get('nodes'), data.get('edges')
    if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes) > 200 or len(edges) > 800:
        abort(400, 'A map supports up to 200 locations and 800 paths.')
    if sum(isinstance(node, dict) and node.get('nested_draft') is not None for node in nodes) > 20:
        abort(400, 'Generate at most 20 linked maps in one save.')
    groups = {child.category: child for child in pointcrawl.entry.children if child.category in ('pois', 'paths')}
    existing_nodes = {n.id: n for n in pointcrawl.nodes}
    existing_edges = {e.id: e for e in pointcrawl.edges}
    def edit_card(entry, item):
        if not item.get('content_changed'):
            return
        check_version(entry, item.get('entry_version'))
        entry.title = text_value(item.get('title', ''), 200, True)
        entry.body = content_value(item.get('body', ''))
        if entry.category != 'path':
            category = point_category(item, entry.category)
            if entry.pointcrawl and ARTICLE_MAP_KINDS.get(category) != entry.pointcrawl.kind:
                abort(400, 'Keep the map type for this article.')
            entry.category = category
            entry.is_heart = heart_value(item, entry.category, entry.is_heart)
        if entry.category == 'path':
            if item.get('path_type') not in PATH_TYPES:
                abort(400, 'Invalid path type.')
            entry.path_type = item['path_type']
        entry.version += 1

    resolved, used_entries, numbers = {}, set(), set()
    for item in nodes:
        if not isinstance(item, dict):
            abort(400)
        key = str(item.get('id', ''))
        if not key or key in resolved:
            abort(400, 'Duplicate location.')
        if key.startswith('new-'):
            if item.get('entry_id'):
                entry = owned(ContentEntry, integer(item['entry_id']))
                if entry.category not in POINT_TYPES | {'location'} or entry.campaign_id != pointcrawl.entry.campaign_id:
                    abort(400, 'Choose a location from this campaign.')
            else:
                entry = ContentEntry(owner_id=current_user.id, campaign_id=pointcrawl.entry.campaign_id,
                    category=point_category(item), is_heart=heart_value(item, point_category(item)),
                    title=text_value(item.get('title', ''), 200, True),
                    body=content_value(item.get('body', '')))
                db.session.add(entry)
                db.session.flush()
            if not entry.parent and 'pois' in groups:
                entry.parent = groups['pois']
            node = MapNode(map=pointcrawl, entry=entry)
            db.session.add(node)
        else:
            node = existing_nodes.get(integer(key))
            if node is None:
                abort(400, 'Location does not belong to this map.')
            edit_card(node.entry, item)
        if node.entry.id in used_entries:
            abort(400, 'A location can appear only once on a map.')
        used_entries.add(node.entry.id)
        node.number = integer(item.get('number'))
        if node.number < 1 or node.number in numbers:
            abort(400, 'Location numbers must be positive and unique.')
        numbers.add(node.number)
        node.x, node.y = coordinate(item.get('x')), coordinate(item.get('y'))
        if 'geometry' in item:
            node.geometry = validate_node_geometry(item['geometry'], node.entry.category)
        nested_id = item.get('nested_map_id')
        draft = item.get('nested_draft')
        if draft is not None:
            # Only one generated level per request; never overwrite a linked map's contents.
            if nested_draft or nested_id not in (None, '') or not isinstance(draft, dict):
                abort(400, 'Invalid nested map draft.')
            if draft.get('kind') not in ('dungeon', 'forest'):
                abort(400, 'Choose a dungeon or forest.')
            nested_entry = node.entry
            nested = nested_entry.pointcrawl
            if nested and (nested.nodes or nested.edges or (nested.drawing and nested.drawing != EMPTY_DRAWING)):
                abort(409, 'This article already has a map. Open it to edit its contents.')
            if not key.startswith('new-') or item.get('entry_id'):
                check_version(nested_entry, integer(item.get('entry_version')) + (1 if item.get('content_changed') else 0))
                if not item.get('content_changed'):
                    nested_entry.version += 1
            nested_entry.category = draft['kind']
            nested_entry.is_heart = False
            generated_body = content_value(draft.get('body', ''))
            if nested_entry.body.startswith(RICH_PREFIX):
                nested_entry.body = content_value(nested_entry.body + str(render_content(generated_body)))
            else:
                nested_entry.body = content_value('\n\n'.join(filter(None, [nested_entry.body, generated_body])))
            if nested is None:
                nested = PointcrawlMap(entry=nested_entry, kind=draft['kind'])
            else:
                nested.kind = draft['kind']
            db.session.add(nested)
            # Flush only once the parent node has all required geometry fields.
            db.session.flush()
            save_geometry(nested, {**draft, 'version': nested.version}, nested_draft=True)
            save_article_children(nested_entry, draft.get('children', []))
            nested_id = nested.id
        nested = owned(PointcrawlMap, integer(nested_id)) if nested_id not in (None, '') else None
        if nested and (nested.id == pointcrawl.id or nested.entry.campaign_id != pointcrawl.entry.campaign_id):
            abort(400, 'Choose another map from this campaign.')
        node.nested_map = nested or node.entry.pointcrawl
        resolved[key] = node
    # Populate IDs only after all required geometry fields have been assigned.
    db.session.flush()
    used_edges, pairs = set(), set()
    for item in edges:
        if not isinstance(item, dict):
            abort(400)
        source, target = resolved.get(str(item.get('source'))), resolved.get(str(item.get('target')))
        if source is None or target is None or source == target:
            abort(400, 'Paths must connect two locations on this map.')
        pair = tuple(sorted((source.id, target.id)))
        if pair in pairs:
            abort(400, 'Duplicate path.')
        pairs.add(pair)
        key = str(item.get('id', ''))
        if key.startswith('new-'):
            kind = item.get('path_type', 'standard')
            if kind not in PATH_TYPES:
                abort(400)
            entry = ContentEntry(owner_id=current_user.id, campaign_id=pointcrawl.entry.campaign_id,
                category='path', title=text_value(item.get('title', 'Path'), 200, True),
                body=content_value(item.get('body', '')), path_type=kind)
            if 'paths' in groups:
                entry.parent = groups['paths']
            edge = MapEdge(map=pointcrawl, entry=entry)
            db.session.add(edge)
        else:
            edge = existing_edges.get(integer(key))
            if edge is None or edge.id in used_edges:
                abort(400, 'Invalid path.')
            edit_card(edge.entry, item)
        edge.source_id, edge.target_id = source.id, target.id
        used_edges.add(edge.id)
    # Explicitly remove path originals, including their party presentations.
    for edge in existing_edges.values():
        if edge.id not in used_edges:
            db.session.delete(edge.entry)
    retained = {node.id for node in resolved.values()}
    for node in existing_nodes.values():
        if node.id not in retained:
            parent = node.entry.parent
            if parent and parent.category == 'pois' and parent.parent_id == pointcrawl.entry_id:
                node.entry.parent = None
            db.session.delete(node)
    for node in resolved.values():
        if node.nested_map and node.nested_map.entry is not node.entry:
            continue  # Preserve legacy linked originals and their saved contents.
        own_map = ensure_article_map(node.entry)
        if own_map and not node.nested_map:
            node.nested_map = own_map
    pointcrawl.version += 1


def point_category(item, fallback='custom'):
    category = item.get('category') or item.get('poi_kind') or fallback
    if category == 'location':
        category = legacy_point_type(item.get('title'))
    if category not in POINT_TYPES:
        abort(400, 'Choose a point of interest type.')
    return category


def heart_value(item, category, fallback=False):
    value = item.get('is_heart', fallback)
    if not isinstance(value, bool) or (value and category != 'settlement'):
        abort(400, 'Only a settlement can be the Heart.')
    return value


def save_article_children(parent, children):
    """Persist a reviewed draft with server-owned ancestry and a bounded size."""
    remaining = 1000
    def create(owner, rows, depth):
        nonlocal remaining
        if not isinstance(rows, list) or depth > 10:
            abort(400, 'Invalid article hierarchy.')
        for row in rows:
            remaining -= 1
            if remaining < 0 or not isinstance(row, dict):
                abort(400, 'An article draft supports up to 1000 descendants.')
            category = row.get('category')
            if category not in CATEGORIES or category == 'map':
                abort(400, 'Invalid article type.')
            path_type = row.get('path_type', 'standard')
            if path_type not in PATH_TYPES:
                abort(400, 'Invalid path type.')
            child = ContentEntry(owner_id=parent.owner_id, campaign=parent.campaign,
                parent=owner, category=category, title=text_value(row.get('title'), 200, True),
                body=content_value(row.get('body', '')), path_type=path_type,
                is_heart=heart_value(row, category))
            db.session.add(child)
            create(child, row.get('children', []), depth + 1)
    create(parent, children, 0)


def set_article_parent(entry, value):
    parent = owned(ContentEntry, integer(value)) if value not in (None, '') else None
    if parent and (parent.campaign.id if parent.campaign else None) != (entry.campaign.id if entry.campaign else None):
        abort(400, 'Choose a parent in the same campaign.')
    if parent and entry.id:
        pending, descendants = [entry], set()
        while pending:
            child = pending.pop()
            if child.id in descendants:
                continue
            descendants.add(child.id)
            pending.extend(child.children)
            if child.pointcrawl:
                pending.extend(node.entry for node in child.pointcrawl.nodes)
                pending.extend(edge.entry for edge in child.pointcrawl.edges)
            pending.extend(node.nested_map.entry for node in child.map_nodes if node.nested_map)
        if parent.id in descendants:
            abort(400, 'An article cannot contain itself.')
    seen = {entry.id} if entry.id else set()
    cursor = parent
    while cursor:
        if cursor.id in seen:
            abort(400, 'An article cannot contain itself.')
        seen.add(cursor.id)
        cursor = cursor.parent
    if entry.parent is not parent:
        entry.parent = parent


def ensure_article_map(entry):
    """Attach a canvas to the original, reusing its existing child articles."""
    kind = ARTICLE_MAP_KINDS.get(entry.category)
    if not kind or entry.pointcrawl:
        return entry.pointcrawl
    canvas = PointcrawlMap(entry=entry, kind=kind)
    db.session.add(canvas)
    if kind == 'realm':
        populate_realm_map(canvas)
        return canvas
    points = []
    for child in entry.children:
        if child.category == 'pois':
            points.extend(row for row in child.children if row.category in POINT_TYPES)
        elif child.category in POINT_TYPES:
            points.append(child)
    for index, point in enumerate(points[:200]):
        db.session.add(MapNode(map=canvas, entry=point, number=index + 1,
            x=150 + (index % 5) * 220, y=150 + (index // 5) * 180,
            nested_map=point.pointcrawl))
    return canvas


def ensure_article_tree_maps(entry):
    for child in entry.children:
        ensure_article_tree_maps(child)
    ensure_article_map(entry)


def populate_realm_map(canvas):
    """Place existing setting articles without duplicating or moving saved points."""
    root = canvas.entry
    terrains, landmarks, waters, forests, pois, paths = [], [], [], [], [], []
    def geography(entry, terrain=None):
        if entry.category == 'terrain':
            terrains.append(entry)
            terrain = entry
        elif entry.category == 'water':
            waters.append((entry, terrain))
        elif entry.category == 'landmark':
            landmarks.append((entry, terrain))
        elif entry.category == 'forest':
            forests.append((entry, terrain))
            return  # Forest interiors have their own map.
        for child in entry.children:
            if child.category in ('topography', 'terrain', 'landmark', 'water', 'forest'):
                geography(child, terrain)
    for child in root.children:
        if child.category in ('topography', 'terrain', 'water'):
            geography(child)
        elif child.category == 'pois':
            pois.extend(point for point in child.children if point.category in POINT_TYPES)
        elif child.category == 'paths':
            paths.extend(path for path in child.children if path.category == 'path')
        elif child.category in POINT_TYPES:
            pois.append(child)
        elif child.category == 'path':
            paths.append(child)
    existing = {node.entry: node for node in canvas.nodes}
    new_points = set(terrains + [entry for entry, _ in landmarks + waters + forests] + pois) - set(existing)
    if len(existing) + len(new_points) > 200:
        abort(400, 'A map supports up to 200 points of interest.')
    # An upgrade goes beside an existing layout; existing coordinates stay intact.
    offset = max((node.x for node in canvas.nodes), default=-500) + 900 if canvas.nodes else 350
    number = max((node.number for node in canvas.nodes), default=0)
    changed = False
    def place(entry, x, y):
        nonlocal number, changed
        if entry.owner_id != root.owner_id or entry.campaign_id != root.campaign_id:
            abort(409, 'Geography must belong to the same campaign and owner.')
        if entry not in existing:
            number += 1
            node = MapNode(map=canvas, entry=entry, number=number, x=x, y=y,
                           nested_map=entry.pointcrawl)
            db.session.add(node)
            existing[entry] = node
            changed = True
        return existing[entry]
    # A digital die drop: spaced, scattered seeds instead of a row of boxes.
    # Persist their positions once; upgrades never move existing map objects.
    rng = random.Random(root.id)
    regions = []
    for entry in terrains:
        candidates = [(offset + rng.randrange(1600), 350 + rng.randrange(1200)) for _ in range(40)]
        x, y = max(candidates, key=lambda p: min(
            (math.hypot(p[0] - node.x, p[1] - node.y) for node in regions), default=0))
        regions.append(place(entry, x, y))
    for i, (entry, terrain) in enumerate(landmarks):
        region = existing.get(terrain)
        place(entry, region.x if region else offset + i * 220, region.y if region else 350)
    for i, (entry, terrain) in enumerate(waters):
        region = existing.get(terrain)
        place(entry, region.x + 110 if region else offset + i * 220,
              region.y + 270 if region else 160)
    for i, entry in enumerate(pois):
        region = regions[i % len(regions)] if regions else None
        slot = i // len(regions) if regions else i
        place(entry, region.x - 200 + (slot % 3) * 200 if region else offset + (i % 5) * 220,
              region.y - 230 + (slot // 3) * 170 if region else 350 + (i // 5) * 200)
    for i, (entry, terrain) in enumerate(forests):
        region = existing.get(terrain)
        place(entry, region.x - 180 if region else offset + i * 220,
              region.y + 270 if region else 600)
    # Paths use their existing articles; the initial layout is schematic.
    route = list(dict.fromkeys(existing[entry] for entry in pois))
    used_paths = {edge.entry for edge in canvas.edges}
    pairs = {frozenset((edge.source_id, edge.target_id)) for edge in canvas.edges}
    if paths:
        db.session.flush()
    for path, (source, target) in zip(paths, zip(route, route[1:])):
        pair = frozenset((source.id, target.id))
        if path in used_paths or path.map_edges or pair in pairs:
            continue
        if path.owner_id != root.owner_id or path.campaign_id != root.campaign_id:
            abort(409, 'Paths must belong to the same campaign and owner.')
        db.session.add(MapEdge(map=canvas, entry=path, source_id=source.id, target_id=target.id))
        pairs.add(pair)
        changed = True
    return changed

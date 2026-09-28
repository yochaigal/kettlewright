"""Authorization and explicit player projections for warden content."""
import math
from flask import abort, current_app
from flask_login import current_user

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap, MapNode, MapEdge)
from app.socket_events import party_recipient_ids
from app.lib.map_drawing import EMPTY_DRAWING, validate_drawing
from app.lib.rich_content import normalize_content, render_content

CATEGORIES = {'overview': 'Overview', 'npc': 'NPCs', 'location': 'Locations',
              'lore': 'Lore', 'faction': 'Factions', 'relic': 'Relics',
              'note': 'Notes', 'map': 'Maps'}
PATH_TYPES = ('standard', 'hidden', 'conditional')
MAP_KINDS = ('dungeon', 'forest', 'realm')


def owned(model, object_id):
    obj = db.get_or_404(model, object_id)
    owner_id = obj.entry.owner_id if isinstance(obj, PointcrawlMap) else obj.owner_id
    if owner_id != current_user.id:
        abort(403)
    return obj


def party_access(party_id, editing=False):
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


def known_entries(party_id):
    """Only independently published fields; never serialize an ORM original."""
    rows = PartyPresentation.query.filter_by(party_id=party_id, published=True).all()
    known = {row.entry_id: {'id': row.entry_id, 'category': row.entry.category,
                           'title': row.title, 'body': row.body, 'path_type': row.path_type,
                           'links': [], 'map_id': row.entry.pointcrawl.id if row.entry.pointcrawl else None}
             for row in rows}
    # A path cannot be read indirectly while its map or either endpoint is hidden.
    for row in rows:
        if row.entry.category == 'path':
            edges = row.entry.map_edges
            if not edges or not any(edge.map.entry_id in known and
                    db.session.get(MapNode, edge.source_id).entry_id in known and
                    db.session.get(MapNode, edge.target_id).entry_id in known for edge in edges):
                known.pop(row.entry_id, None)
    for row in rows:
        if row.entry_id in known:
            known[row.entry_id]['links'] = [
                {'id': target_id, 'title': known[target_id]['title']}
                for target_id in sorted({link.target_id for link in row.entry.links} | map_related_ids(row.entry))
                if target_id in known]
    return known


def map_projection(pointcrawl, party_id=None):
    known = known_entries(party_id) if party_id is not None else None
    if known is not None and pointcrawl.entry_id not in known:
        abort(404)

    def content(entry):
        if known is not None:
            return known.get(entry.id)
        return {'id': entry.id, 'title': entry.title, 'body': entry.body, 'path_type': entry.path_type}

    root = content(pointcrawl.entry)
    result = {'id': pointcrawl.id, 'title': root['title'], 'body': root['body'], 'nodes': [], 'edges': []}
    if party_id is None:
        result['drawing'] = pointcrawl.drawing or EMPTY_DRAWING
    else:
        publication = PartyPresentation.query.filter_by(entry_id=pointcrawl.entry_id, party_id=party_id, published=True).first_or_404()
        result['drawing'] = publication.drawing or EMPTY_DRAWING
    if known is None:
        result.update(version=pointcrawl.version, kind=pointcrawl.kind)
    for node in sorted(pointcrawl.nodes, key=lambda n: (n.number, n.id)):
        item = content(node.entry)
        if item is None:
            continue
        nested = node.nested_map
        result['nodes'].append({'id': node.id, 'entry_id': node.entry_id,
            'number': node.number, 'x': node.x, 'y': node.y,
            'title': item['title'], 'body': item['body'],
            'nested_map_id': nested.id if nested and (known is None or nested.entry_id in known) else None})
    visible = {node['id'] for node in result['nodes']}
    for edge in pointcrawl.edges:
        item = content(edge.entry)
        if item is not None and edge.source_id in visible and edge.target_id in visible:
            result['edges'].append({'id': edge.id, 'entry_id': edge.entry_id,
                'source': edge.source_id, 'target': edge.target_id,
                'title': item['title'], 'body': item['body'], 'path_type': item['path_type']})
    return result


def notify_parties(party_ids):
    from app import socketio
    for party_id in set(party_ids):
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
    """Replace geometry atomically, keeping existing prose in its own editor."""
    check_version(pointcrawl, data.get('version'))
    if 'drawing' in data:
        pointcrawl.drawing = validate_drawing(data['drawing'])
    nodes, edges = data.get('nodes'), data.get('edges')
    if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes) > 200 or len(edges) > 800:
        abort(400, 'A map supports up to 200 locations and 800 paths.')
    if sum(isinstance(node, dict) and node.get('nested_draft') is not None for node in nodes) > 20:
        abort(400, 'Generate at most 20 linked maps in one save.')
    existing_nodes = {n.id: n for n in pointcrawl.nodes}
    existing_edges = {e.id: e for e in pointcrawl.edges}
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
                if entry.category != 'location' or entry.campaign_id != pointcrawl.entry.campaign_id:
                    abort(400, 'Choose a location from this campaign.')
            else:
                entry = ContentEntry(owner_id=current_user.id, campaign_id=pointcrawl.entry.campaign_id,
                    category='location', title=text_value(item.get('title', ''), 200, True),
                    body=content_value(item.get('body', '')))
                db.session.add(entry)
                db.session.flush()
            node = MapNode(map=pointcrawl, entry=entry)
            db.session.add(node)
        else:
            node = existing_nodes.get(integer(key))
            if node is None:
                abort(400, 'Location does not belong to this map.')
        if node.entry.id in used_entries:
            abort(400, 'A location can appear only once on a map.')
        used_entries.add(node.entry.id)
        node.number = integer(item.get('number'))
        if node.number < 1 or node.number in numbers:
            abort(400, 'Location numbers must be positive and unique.')
        numbers.add(node.number)
        node.x, node.y = coordinate(item.get('x')), coordinate(item.get('y'))
        nested_id = item.get('nested_map_id')
        draft = item.get('nested_draft')
        if draft is not None:
            # Only one generated level per request; never overwrite a linked map's contents.
            if nested_draft or nested_id not in (None, '') or not isinstance(draft, dict):
                abort(400, 'Invalid nested map draft.')
            if draft.get('kind') not in ('dungeon', 'forest'):
                abort(400, 'Choose a dungeon or forest.')
            nested_entry = ContentEntry(owner_id=current_user.id, campaign_id=pointcrawl.entry.campaign_id,
                category='map', title=text_value(item.get('title', node.entry.title), 200, True),
                body=content_value(draft.get('body', '')))
            nested = PointcrawlMap(entry=nested_entry, kind=draft['kind'])
            db.session.add(nested)
            # Flush only once the parent node has all required geometry fields.
            db.session.flush()
            save_geometry(nested, {**draft, 'version': nested.version}, nested_draft=True)
            nested_id = nested.id
        nested = owned(PointcrawlMap, integer(nested_id)) if nested_id not in (None, '') else None
        if nested and (nested.id == pointcrawl.id or nested.entry.campaign_id != pointcrawl.entry.campaign_id):
            abort(400, 'Choose another map from this campaign.')
        node.nested_map = nested
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
            edge = MapEdge(map=pointcrawl, entry=entry)
            db.session.add(edge)
        else:
            edge = existing_edges.get(integer(key))
            if edge is None or edge.id in used_edges:
                abort(400, 'Invalid path.')
        edge.source_id, edge.target_id = source.id, target.id
        used_edges.add(edge.id)
    # Explicitly remove path originals, including their party presentations.
    for edge in existing_edges.values():
        if edge.id not in used_edges:
            db.session.delete(edge.entry)
    retained = {node.id for node in resolved.values()}
    for node in existing_nodes.values():
        if node.id not in retained:
            db.session.delete(node)
    pointcrawl.version += 1

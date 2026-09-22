"""Normalize old and current inventory exports before storing an imported character."""
import json
import uuid


def normalize_inventory(items_json, containers_json):
    items = json.loads(items_json or '[]')
    containers = json.loads(containers_json or '[]')
    if not isinstance(items, list) or not isinstance(containers, list):
        raise ValueError('Inventory must contain arrays')
    if not containers:
        containers = [dict(id=0, name='Main', slots=10)]
    ids = set()
    for container in containers:
        if not isinstance(container, dict) or not isinstance(container.get('name'), str):
            raise ValueError('Invalid container')
        container['id'] = int(container['id'])
        container['slots'] = int(container['slots'])
        if container['id'] in ids or container['slots'] < 0:
            raise ValueError('Invalid container capacity or ID')
        ids.add(container['id'])
        container.pop('items', None)  # Old decorated exports duplicate items here.
    if 0 not in ids:
        raise ValueError('Missing main container')
    item_ids = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('name'), str):
            raise ValueError('Invalid item')
        item['id'] = str(item.get('id', uuid.uuid4().hex))
        item['location'] = int(item.get('location', 0))
        item['tags'] = item.get('tags') or []
        if item['id'] in item_ids or item['location'] not in ids:
            raise ValueError('Invalid item ID or location')
        if not isinstance(item['tags'], list) or any(not isinstance(tag, str) for tag in item['tags']):
            raise ValueError('Invalid tags')
        for field in ('uses', 'charges', 'max_charges'):
            if field in item:
                item[field] = int(item[field])
        if 'armor_active' in item and not isinstance(item['armor_active'], bool):
            raise ValueError('Invalid armor state')
        item_ids.add(item['id'])
    return items, containers

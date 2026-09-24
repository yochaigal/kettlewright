"""Stable, backwards-compatible slot positions inside the existing item JSON."""
from copy import deepcopy


def item_size(item):
    tags = item.get('tags') or []
    return 0 if 'petty' in tags else 2 if 'bulky' in tags else 1


def arrange_slots(items, capacity, first_id=None):
    """Reserve saved positions, then fill gaps. Keep overloaded items visible."""
    items = [deepcopy(item) for item in items if not item.get('is_empty')]
    capacity = max(0, int(capacity))
    limit = max(capacity, sum(item_size(item) for item in items))
    occupied = {}
    positions = {}
    pending = []
    ordered = sorted(items, key=lambda item: str(item['id']) != str(first_id)) if first_id is not None else items
    for item in ordered:
        size = item_size(item)
        if not size:
            continue
        slot = item.get('slot')
        if (type(slot) is int and 0 <= slot <= limit - size and (size == 1 or slot % 2 == 0)
                and all(index not in occupied for index in range(slot, slot + size))):
            positions[str(item['id'])] = slot
            occupied.update({index: item for index in range(slot, slot + size)})
        else:
            pending.append(item)
    for item in pending:
        size = item_size(item)
        slot = 0
        while (size == 2 and slot % 2) or any(index in occupied for index in range(slot, slot + size)):
            slot += 1
        positions[str(item['id'])] = slot
        occupied.update({index: item for index in range(slot, slot + size)})
    rows = []
    slot = 0
    while slot < max(capacity, max(occupied, default=-1) + 1):
        item = occupied.get(slot)
        span = item_size(item) if item else 1
        rows.append(dict(slot=slot, span=span, item=item, overflow=slot + span > capacity))
        slot += span
    return dict(rows=rows, petty=[item for item in items if not item_size(item)], positions=positions,
                used=sum(item_size(item) for item in items), capacity=capacity,
                overflow=any(row['overflow'] for row in rows))

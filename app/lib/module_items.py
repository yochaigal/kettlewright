"""Module items (#476): gear, relics and spellbooks a module holds, to give the party as it finds them.

Items live in Module.items (name -> item, in the item format of background gear: name, tags,
description, uses, charges, max_charges, armor_active). Modules bring them as Markdown
(type: Items): each item a ### heading with its tags in brackets, its description below:

    ### The Eye of Vuk [charges 1/1]
    A heavy iron medallion strung on a fine silver chain.

The Warden sends a copy to a party: into one of its storage containers or a character's
inventory. The module keeps its item, private; the party's copy is its own to use or change.
"""
import json
import re

from app.lib.campaign_backgrounds import BackgroundError, BRACKETS, _item_markdown, _localized, item_from_tokens, shown_words

MAX_ITEMS = 200

HEADING = re.compile(r'^###\s+(?!#)(.+?)\s*$')

# What "New item" starts from: a complete, valid example to change.
ITEM_TEMPLATE = """### Lantern of the Drowned [charges 3/3]
A green glass lantern that burns underwater. Its light shows the way to the nearest corpse.
- **Recharge**: Leave it a night at the bottom of a lake.
"""


class ItemError(BackgroundError):
    pass


def items_from_markdown(body, where='Items'):
    """Items from a Markdown body (after any front matter): {name: item}, in order. Raises ItemError."""
    found, current = [], None
    for line in body.splitlines():
        heading = HEADING.match(line)
        if heading:
            current = [heading.group(1), []]
            found.append(current)
        elif current is not None:
            current[1].append(line)
        elif line.strip():
            raise ItemError(f'{where}: write each item as a ### heading (### Name [tags]), its description below.')
    items = {}
    for head, lines in found:
        match = BRACKETS.match(head)
        name, tokens = ((match.group('name').strip(), [t.strip() for t in match.group('tags').split(',') if t.strip()])
                        if match else (head.strip(), []))
        description = '\n'.join(lines).strip()
        try:
            item = item_from_tokens(name, tokens, description or None, f'{where}: item "{name}"')
        except BackgroundError as exc:
            raise ItemError(str(exc)) from exc
        if item['name'] in items:
            raise ItemError(f'{where}: item "{item["name"]}" is written twice.')
        items[item['name']] = item
    if not items:
        raise ItemError(f'{where}: no items found. Write each item as a ### heading (### Name [tags]).')
    return items


def item_template():
    """What "New item" starts from, in the reader's language."""
    if not _localized():
        return ITEM_TEMPLATE
    from flask_babel import gettext
    return gettext(ITEM_TEMPLATE)


def item_markdown(item, localized=False):
    """One item as Markdown: its heading, then its description. Reads back as the same item.
    localized=True writes its tag words in the reader's language (the editor)."""
    head = _item_markdown({key: value for key, value in item.items() if key != 'description'}, shown_words(localized))
    description = item.get('description', '')
    return f'### {head}\n' + (f'{description}\n' if description else '')


def item_details(item, localized=False):
    """Its tags as written in brackets: 'petty, charges 2/3' ('' for none)."""
    head = _item_markdown({key: value for key, value in item.items() if key != 'description'}, shown_words(localized))
    match = BRACKETS.match(head)
    return match.group('tags') if match else ''


def items_file(title, items):
    """A Markdown file (type: Items) holding these items."""
    lines = ['---', 'layout: default', f'title: {json.dumps(title, ensure_ascii=False)}', 'type: Items', '---']
    return '\n'.join(lines) + '\n' + '\n'.join(item_markdown(item) for item in items.values())


def parse_item_text(text):
    """One item, as the Warden wrote it on its page. Raises ItemError."""
    found = items_from_markdown(text.lstrip('﻿').replace('\r\n', '\n'), 'Item')
    if len(found) != 1:
        raise ItemError('Write one item: a ### heading with its description below.')
    return next(iter(found.items()))


def add_items(module, items):
    """Add or replace a module's items by name. The caller commits."""
    merged = dict(module.items or {})
    merged.update(items)
    if len(merged) > MAX_ITEMS:
        raise ItemError(f'A module can have at most {MAX_ITEMS} items.')
    module.items = merged


def remove_item(module, name):
    remaining = {key: value for key, value in (module.items or {}).items() if key != name}
    module.items = remaining or None


def item_anchor(name):
    from slugify import slugify
    return 'item-' + (slugify(name) or 'unnamed')


def sorted_items(module):
    return sorted((module.items or {}).items(), key=lambda pair: pair[0].casefold())


# ----- Send to party: a copy, into a party container or a character's inventory -----

def destinations(campaign):
    """Where the Warden can send an item: each party's storage containers and its characters' containers.

    [(party, [(value, label), ...])]; value is 'party:<id>:<container>' or 'character:<id>:<container>'."""
    from app.models import Character
    choices = []
    for party in sorted(campaign.parties, key=lambda party: (party.name or '').casefold()):
        options = [(f'party:{party.id}:{c["id"]}', c['name']) for c in _containers(party)]
        members = json.loads(party.members or '[]')
        characters = Character.query.filter(Character.id.in_(members), Character.party_id == party.id) \
            .order_by(Character.name).all() if members else []
        for character in characters:
            options += [(f'character:{character.id}:{c["id"]}', f'{character.name} · {c["name"]}')
                        for c in _containers(character)]
        choices.append((party, options))
    return choices


def _containers(holder):
    return [c for c in json.loads(holder.containers or '[]') if not c.get('on_the_ground')]


def destination(campaign, value):
    """(party, holder, container id) for a destination value, or None if it is not one of the campaign's."""
    from app.models import db, Character, Party
    parts = (value or '').split(':')
    if len(parts) != 3 or parts[0] not in ('party', 'character') or not all(p.isdigit() for p in parts[1:]):
        return None
    kind, holder_id, container_id = parts[0], int(parts[1]), int(parts[2])
    if kind == 'party':
        holder = db.session.get(Party, holder_id)
        party = holder
    else:
        holder = db.session.get(Character, holder_id)
        party = db.session.get(Party, holder.party_id) if holder and holder.party_id else None
        if party is not None and holder.id not in json.loads(party.members or '[]'):
            party = None
    if holder is None or party is None or party.campaign_id != campaign.id:
        return None
    if not any(c['id'] == container_id for c in _containers(holder)):
        return None
    return party, holder, container_id


def send_item(item, holder, container_id):
    """A copy of the item in the holder's container. Returns it, or None when the container is full.
    The caller commits."""
    from app.lib.inventory import Inventory
    tags = item.get('tags', [])
    charges = item.get('charges', 0)
    return Inventory(holder).create_item(item['name'], ','.join(tags), item.get('uses', 0), charges,
                                         item.get('max_charges', charges), container_id,
                                         item.get('description', ''), armor_active=item.get('armor_active'),
                                         commit=False)

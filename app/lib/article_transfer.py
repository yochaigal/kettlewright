"""Give to party (#476): copy a module article into a party, as something it can use.

Items, relics and spellbooks go to the party's storage as an item; bestiary and monster
articles become one of the party's monsters. The article stays in its module, private
until revealed; the party gets its own copy to change, use or give away.
"""
import json
import re

from app.models import db
from app.lib.rich_content import RICH_PREFIX, content_excerpt

GIVE_KINDS = {'item': 'storage', 'relic': 'storage', 'spellbook': 'storage', 'bestiary': 'monster', 'monster': 'monster'}


def give_kind(entry):
    """'storage', 'monster' or None (other articles can only be revealed)."""
    return GIVE_KINDS.get(entry.category)


def plain_name(title, limit):
    text = content_excerpt(title or '', limit) or 'Untitled'
    return text[:limit]


def article_text(entry):
    """The article's text as plain lines (rich text loses its formatting; Markdown is kept)."""
    body = entry.body or ''
    if body.startswith(RICH_PREFIX):
        html = body[len(RICH_PREFIX):]
        html = re.sub(r'(?i)<br\s*/?>|</(?:p|li|h[1-6]|div|blockquote)>', '\n', html)
        return '\n'.join(content_excerpt(line, 10000) for line in html.splitlines()).strip()
    return body.strip()


def give_to_storage(entry, party):
    """An item in the party's first storage container, named after the article. Returns it, or None when full."""
    from app.lib.inventory import Inventory
    containers = json.loads(party.containers or '[]')
    container = next((c for c in containers if not c.get('on_the_ground')), None)
    if container is None:
        return None
    description = content_excerpt(entry.body or '', 2000)
    return Inventory(party).create_item(plain_name(entry.title, 100), '', 0, 0, 0, container['id'], description)


def give_monster(entry, party):
    """One of the party's monsters. A stat line (8 HP, 10 STR, 12 DEX, 2 WIL, claws (d6)) sets its stats;
    without one it starts with 3 HP and 10s, to change on its sheet."""
    from app.lib.monsters import new_monster, parse_monster
    name = plain_name(entry.title, 100)
    text = article_text(entry)
    try:
        template = parse_monster(text if re.match(r'^#{1,6}\s+\S', text) else f'# {name}\n{text}')
    except ValueError:
        template = dict(name=name, hp=3, armor=0, strength=10, dexterity=10, willpower=10, attack='',
                        notes=text[:10000])
    monster = new_monster(party, template)
    db.session.add(monster)
    db.session.commit()
    return monster

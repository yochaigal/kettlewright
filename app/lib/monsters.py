"""Cairn stat blocks and party-owned monster instances."""
import json
import re
from pathlib import Path

from app.models import Companion, Character, db

CATALOG = Path(__file__).resolve().parents[1] / 'static/json/monsters.json'


def parse_monster(markdown):
    if not isinstance(markdown, str) or len(markdown.encode('utf-8')) > 65536:
        raise ValueError('Choose a Markdown monster file smaller than 64 KB.')
    body = re.sub(r'\A\ufeff?---\s*\n.*?\n---\s*\n', '', markdown, count=1, flags=re.S).strip()
    lines = body.splitlines()
    heading = next((i for i, line in enumerate(lines) if re.match(r'^#{1,6}\s+\S', line)), None)
    if heading is None:
        raise ValueError('Include a Markdown heading with the monster name.')
    name = re.sub(r'^#{1,6}\s+', '', lines[heading]).strip()
    stats_line = next((i for i in range(heading + 1, len(lines)) if re.search(r'\b\d+\s+HP\b', lines[i], re.I)), None)
    if stats_line is None or not name or len(name) > 100:
        raise ValueError('Include a monster name and a stat line such as 8 HP, 10 STR, 12 DEX, 2 WIL, vines (d4).')
    stats = lines[stats_line]
    result = dict(name=name, armor=0, strength=10, dexterity=10, willpower=10)
    fields = {'HP': 'hp', 'Armor': 'armor', 'STR': 'strength', 'DEX': 'dexterity', 'WIL': 'willpower'}
    for label, field in fields.items():
        matches = re.findall(r'\b(\d+)\s+' + label + r'\b', stats, re.I)
        if len(matches) > 1:
            raise ValueError('Each stat must appear only once.')
        if matches:
            result[field] = int(matches[0])
        if result.get(field, 0) > (3 if field == 'armor' else 100000):
            raise ValueError('Monster stats are outside the allowed range.')
    attack = re.sub(r'\b\d+\s+(?:HP|Armor|STR|DEX|WIL)\b\s*,?\s*', '', stats, flags=re.I).strip(' ,')
    result['attack'] = attack
    result['notes'] = '\n'.join(lines[stats_line + 1:]).strip()
    if len(attack) > 200 or len(result['notes']) > 10000:
        raise ValueError('Monster attack or notes are too long.')
    return result


def monster_catalog():
    return json.loads(CATALOG.read_text())


def new_monster(party, template):
    from app.lib.companions import import_pet
    data = dict(template, role=template['name'], gold=0, items=[], containers=[dict(id=0, name='Main', slots=10)])
    for stat in ('hp', 'strength', 'dexterity', 'willpower'):
        data[stat + '_max'] = data[stat]
    c = import_pet(data)
    c.kind, c.party, c.shared = 'monster', party, False
    return c


def give_monster(c, character):
    if c.kind != 'monster' or character.party_id != c.party_id or character.id not in json.loads(c.party.members or '[]'):
        raise ValueError('Choose a current character in this monster’s party.')
    # Avoid delete-orphan cascades when moving between parent collections.
    moved = db.session.execute(db.update(Companion).where(Companion.id == c.id, Companion.kind == 'monster')
                       .values(kind='pet', party_id=None, character_id=character.id, shared=True))
    if moved.rowcount != 1:
        raise ValueError('This monster has already been transferred.')
    db.session.expire_all()


def monster_members(party):
    return Character.query.filter(Character.party_id == party.id,
                                  Character.id.in_(json.loads(party.members or '[]'))).order_by(Character.name).all()

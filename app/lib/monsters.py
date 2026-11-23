"""Cairn stat blocks and party-owned monster instances."""
import json
import re
from pathlib import Path
from functools import lru_cache

from app.models import Companion, Character, db

CATALOG = Path(__file__).resolve().parents[1] / 'static/json/monsters.json'
# The art a party's new monsters get: Kettlewright's tokens, or Oozejar's Illustrated Bestiary
# (from the Cairn collection for Atlas VTT, CC BY-SA 4.0), which has one token for each bestiary monster.
MONSTER_ARTS = ('kettlewright', 'oozejar')
MAX_MONSTER_BATCH = 100


def _monster_body(markdown):
    body = markdown.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n').strip()
    # A leading separator before a monster is not YAML front matter.
    front_matter = re.match(r'\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)', body, re.S)
    if front_matter:
        first = next((line.strip() for line in front_matter[1].splitlines()
                      if line.strip() and not line.lstrip().startswith('#')), '')
        if re.match(r'[\w-]+[ \t]*:', first):
            return body[front_matter.end():].strip()
    return body


def parse_monsters(markdown):
    """Validate the entire import before any instances are created."""
    if not isinstance(markdown, str) or len(markdown.encode('utf-8')) > 65536:
        raise ValueError('Choose a Markdown monster file smaller than 64 KB.')
    blocks, lines, fence = [], [], None
    for line in _monster_body(markdown).splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
        if fence is None and re.fullmatch(r'[ \t]*---[ \t]*', line):
            if '\n'.join(lines).strip():
                blocks.append('\n'.join(lines))
            lines = []
        else:
            lines.append(line)
    if '\n'.join(lines).strip():
        blocks.append('\n'.join(lines))
    if not blocks:
        raise ValueError('Include a Markdown heading with the monster name.')
    if len(blocks) > MAX_MONSTER_BATCH:
        raise ValueError('Add at most 100 monster instances at a time.')
    templates = []
    for index, block in enumerate(blocks, 1):
        try:
            templates.append(parse_monster(block))
        except ValueError as problem:
            raise ValueError(f'Monster {index}: {problem}') from problem
    return templates


def parse_monster(markdown):
    if not isinstance(markdown, str) or len(markdown.encode('utf-8')) > 65536:
        raise ValueError('Choose a Markdown monster file smaller than 64 KB.')
    body = _monster_body(markdown)
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


def monster_catalog(art='kettlewright'):
    templates = json.loads(CATALOG.read_text())
    for template in templates.values():
        template['art'] = {choice: monster_portrait(template['name'], choice) for choice in MONSTER_ARTS}
        template['image_url'] = template['art'].get(art, template['art']['kettlewright'])
    return templates


def localized_monster_catalog(art='kettlewright'):
    """The bestiary in the reader's language, for pages and new monsters. Portraits and
    keys stay tied to the English names, so they are set before translating."""
    from flask_babel import gettext
    templates = monster_catalog(art)
    labels = {'hp': gettext('HP'), 'armor': gettext('Armor'), 'strength': gettext('STR'),
              'dexterity': gettext('DEX'), 'willpower': gettext('WIL')}
    for template in templates.values():
        template['labels'] = labels
        for field in ('name', 'attack', 'notes'):
            if template.get(field):
                template[field] = gettext(template[field])
    return templates


@lru_cache(maxsize=1)
def _monster_portraits(version):
    return json.loads(CATALOG.with_name('monster-portraits.json').read_text())


def monster_portraits():
    return _monster_portraits(CATALOG.with_name('monster-portraits.json').stat().st_mtime_ns)


def monster_portrait(name, art='kettlewright'):
    """A bestiary monster's portrait in the given art. A name outside the bestiary has no Oozejar
    token, so it gets Kettlewright's."""
    from slugify import slugify
    slug = slugify(name or '')
    if art == 'oozejar' and slug in monster_portraits():
        return f'oozejar/{slug}.webp'
    return monster_portraits().get(slug, 'monster/monster11.png')


def new_monster(party, template):
    from app.lib.companions import import_pet
    data = dict(template, role=template['name'], gold=0, items=[], containers=[dict(id=0, name='Main', slots=10)],
                image_url=template.get('image_url') or monster_portrait(template['name'], party.monster_art))
    data.pop('labels', None)
    data.pop('art', None)
    for stat in ('hp', 'strength', 'dexterity', 'willpower'):
        data[stat + '_max'] = data[stat]
    c = import_pet(data)
    c.kind, c.party, c.shared = 'monster', party, False
    return c


def number_monsters(party, instances):
    """Several of the same monster at once get numbers (Goblin 1, Goblin 2…), so their tokens, rolls and
    HP can be told apart (#375). Numbering continues after the party's monsters already numbered."""
    import re
    from collections import Counter
    counts = Counter(c.name for c in instances)
    taken = {}
    for c in party.monsters:
        if c in instances:
            continue
        match = re.fullmatch(r'(.+) ([0-9]{1,4})', c.name or '')
        if match:
            taken[match[1]] = max(taken.get(match[1], 0), int(match[2]))
    for c in instances:
        if counts[c.name] < 2 and c.name not in taken:
            continue
        base = c.name[:94]
        taken[base] = taken.get(base, 0) + 1
        c.name = f'{base} {taken[base]}'


def give_monster(c, character):
    if c.kind != 'monster' or c.party is None or character.party_id != c.party_id or character.id not in json.loads(c.party.members or '[]'):
        raise ValueError('Choose a current character in this monster’s party.')
    # Avoid delete-orphan cascades when moving between parent collections.
    moved = db.session.execute(db.update(Companion).where(Companion.id == c.id, Companion.kind == 'monster')
                       .values(kind='pet', party_id=None, character_id=character.id, shared=True,
                               image_url=c.image_url or monster_portrait(c.role or c.name, c.party.monster_art)))
    if moved.rowcount != 1:
        raise ValueError('This monster has already been transferred.')
    db.session.expire_all()


def monster_members(party):
    return Character.query.filter(Character.party_id == party.id,
                                  Character.id.in_(json.loads(party.members or '[]'))).order_by(Character.name).all()


def attack_dice(attack):
    """Extract distinct supported damage expressions without inventing attacks."""
    from app.lib.character_rolls import parse_dice
    expressions = []
    for match in re.finditer(r'(?<![\w+])(?:\d*)d\d+(?:\s*\+\s*(?:\d*)d\d+)*(?!\w)', attack or '', re.I):
        try:
            dice = '+'.join(f'd{side}' for side in parse_dice(match[0]))
        except ValueError:
            continue
        if dice not in expressions:
            expressions.append(dice)
    return expressions

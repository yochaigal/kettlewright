"""Character sheets as Markdown or plain text, and Markdown back to export data.

Both renderers work on the dictionary from ``Character.export_data()``, the same
shape as the JSON export. The parser returns that shape too, so a Markdown file
is imported through the same form and validation as a JSON file.

Labels, tags and background names are written in the reader's language. The
parser accepts them in English and in the current language, so a file exported
and imported in the same language round-trips. Lost on the way: item IDs, armor
switched off on an item, the portrait, and pet containers other than Main.
"""
from kettlewright import system
import re

from flask_babel import _

from app.lib.translations import translate_term

# The sheet's stats and conditions with their labels (kettlewright): (('strength', 'STR'), ..., ('hp', 'HP')).
STATS = tuple((stat.key, stat.abbr) for stat in system().sheet_stats)
SECTIONS = system().sheet_sections  # (('description', 'Description'), ...) (kettlewright)
CONDITIONS = tuple((condition.key, condition.label) for condition in system().conditions)
EXTRA_TAGS = system().item_tags  # The system's item vocabulary (kettlewright).
SEPARATOR = ' · '
DESCRIPTION_SEPARATOR = ' — '
MAX_MARKDOWN = 200_000


def _uses(current, maximum):
    return _('%(current)s/%(maximum)s uses', current=current, maximum=maximum)


def _charges(current, maximum):
    return _('%(current)s/%(maximum)s charges', current=current, maximum=maximum)


def _one_line(text):
    return ' '.join(str(text or '').split())


class _Sheet:
    """Collect blocks once, then write them as Markdown or as plain text."""

    def __init__(self, markdown):
        self.markdown = markdown
        self.blocks = []

    def heading(self, level, text):
        if self.markdown:
            self.blocks.append('#' * level + ' ' + text)
        elif level < 3:
            self.blocks.append(text + '\n' + ('=' if level == 1 else '-') * max(3, len(text)))
        else:
            self.blocks.append(text + ':')

    def fields(self, pairs):
        if self.markdown:
            self.blocks.append(SEPARATOR.join(f'**{label}** {value}' for label, value in pairs))
        else:
            self.blocks.append(SEPARATOR.join(f'{label} {value}' for label, value in pairs))

    def field(self, label, value):
        self.blocks.append(f'**{label}:** {value}' if self.markdown else f'{label}: {value}')

    def strong(self, text):
        self.blocks.append(f'**{text}**' if self.markdown else text)

    def text(self, text):
        if text and str(text).strip():
            self.blocks.append(str(text).strip())

    def bullets(self, lines):
        if lines:
            self.blocks.append('\n'.join('- ' + line for line in lines))

    def render(self):
        return '\n\n'.join(self.blocks) + '\n'


def _rules(data):
    """The sheet's game system (kettlewright, #487): its game_system, or the default one (an import, a pet)."""
    from kettlewright import system_or_default
    return system_or_default(data.get('game_system'))


def _stat_pairs(data, with_armor=True):
    pairs = []
    for field, label in ((stat.key, stat.abbr) for stat in _rules(data).sheet_stats):
        if data.get(field) is None:
            continue
        maximum = data.get(field + '_max')
        pairs.append((_(label), f'{data[field]}/{maximum}' if maximum is not None else str(data[field])))
    if with_armor:
        pairs.append((_('Armor'), str(data.get('armor') or 0)))
    if data.get('gold'):
        pairs.append((_('Gold'), str(data['gold'])))
    return pairs


def item_line(item):
    details = []
    for tag in item.get('tags') or []:
        if tag == 'uses':
            uses = item.get('uses', 0)
            details.append(_uses(uses, max(uses, item.get('max_uses', uses))))
        elif tag == 'charges':
            charges = item.get('charges', 0)
            details.append(_charges(charges, max(charges, item.get('max_charges', charges))))
        else:
            details.append(translate_term(tag))
    line = _one_line(translate_term(item.get('name') or '', 'equipment'))
    if details:
        line += ' (' + ', '.join(details) + ')'
    if item.get('description'):
        line += DESCRIPTION_SEPARATOR + _one_line(item['description'])
    return line


def render_character(data, markdown=True):
    sheet = _Sheet(markdown)
    sheet.heading(1, _one_line(data.get('name')))
    background = translate_term(data.get('background') or '')
    if data.get('edition') == 'barebones':
        background += f" ({_('Barebones')})"
    sheet.field(_('Background'), background)
    sheet.fields(_stat_pairs(data))
    rules = _rules(data)
    conditions = [_(condition.label) for condition in rules.conditions if data.get(condition.key)]
    if conditions:
        sheet.field(_('Conditions'), ', '.join(conditions))
    for field, label in rules.sheet_sections:
        if data.get(field) and str(data[field]).strip():
            sheet.heading(2, _(label))
            sheet.text(translate_term(data[field]) if field in ('bonds', 'omens') else data[field])
    past = [(data.get(f'background_table{i}_question'), data.get(f'background_table{i}_answer')) for i in (1, 2)]
    if any(question or answer for question, answer in past):
        sheet.heading(2, _('Your Past'))
        for question, answer in past:
            if question or answer:
                sheet.strong(_one_line(translate_term(question or '')))
                sheet.text(translate_term(answer or ''))
    sheet.heading(2, _('Inventory'))
    items = data.get('items') or []
    for container in data.get('containers') or []:
        sheet.heading(3, f"{_one_line(translate_term(container['name']))} ({container['slots']} {_('slots')})")
        sheet.bullets([item_line(item) for item in items if item.get('location', 0) == container['id']])
    pets = data.get('pets') or []
    if pets:
        sheet.heading(2, _('Pets'))
    for pet in pets:
        title = _one_line(pet.get('name'))
        if pet.get('role'):
            title += f" ({_one_line(translate_term(pet['role']))})"
        sheet.heading(3, title)
        sheet.fields(_stat_pairs(pet))
        if pet.get('attack'):
            sheet.field(_('Attack'), _one_line(pet['attack']))
        sheet.bullets([item_line(item) for item in pet.get('items') or []])
        sheet.text(pet.get('notes'))
    return sheet.render()


# ----- Parsing -----

def _labels(english):
    """A label as written in English and in the current language, lowercased."""
    return {english.lower(), _(english).lower()}


def _find(labels, text):
    text = text.strip().lower()
    return next((key for key, names in labels.items() if text in names), None)


def _known_equipment():
    """Tags and item names from the built-in equipment, to undo their translation."""
    tags, names = set(EXTRA_TAGS), set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get('tags'), list):
                tags.update(tag for tag in node['tags'] if isinstance(tag, str))
                if isinstance(node.get('name'), str):
                    names.add(node['name'])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    from app.lib.data import load_market
    from kettlewright.web import plugin
    walk(load_market())
    walk(plugin().barebones_data())
    return tags, names


def _known_backgrounds():
    from app.lib.data import load_backgrounds
    from kettlewright.web import plugin
    names = set(load_backgrounds())
    bare = plugin().barebones_data()
    names.update(entry['name'] for entry in bare.get('backgrounds', []) if isinstance(entry, dict) and 'name' in entry)
    names.update(bare.get('gear_packages', {}))
    return names


def _reverse(names, context=None):
    result = {}
    for name in names:
        result.setdefault(name.lower(), name)
        result.setdefault(translate_term(name, context).lower(), name)
    return result


def _number_pattern(message):
    """Turn a translated '%(current)s/%(maximum)s uses' into a regex."""
    sample = message('\x00', '\x01')
    return re.compile('^' + re.escape(sample).replace('\x00', r'(\d+)').replace('\x01', r'(\d+)') + '$', re.I)


class _Parser:
    def __init__(self):
        self.sections = {key: _labels(label) for key, label in SECTIONS}
        self.sections.update(past=_labels('Your Past'), inventory=_labels('Inventory'), pets=_labels('Pets'))
        self.stats = {key: _labels(label) for key, label in STATS}
        self.stats.update(armor=_labels('Armor'), gold=_labels('Gold'))
        self.conditions = {key: _labels(label) for key, label in CONDITIONS}
        self.fields = {'background': _labels('Background'), 'conditions': _labels('Conditions'),
                       'attack': _labels('Attack')}
        self.barebones = _labels('Barebones')
        self.slots = _labels('slots')
        tags, names = _known_equipment()
        self.tags = _reverse(tags)
        self.item_names = _reverse(names, 'equipment')
        self.backgrounds = _reverse(_known_backgrounds())
        self.uses = [_number_pattern(_uses)]
        self.charges = [_number_pattern(_charges)]
        from flask_babel import force_locale
        with force_locale('en'):
            self.uses.append(_number_pattern(_uses))
            self.charges.append(_number_pattern(_charges))

    # -- line helpers --

    def field(self, line):
        """'**Label:** value' or 'Label: value' -> (key, value)."""
        match = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', line) or re.match(r'^([^:*]+):\s*(.*)$', line)
        if not match:
            return None, None
        return _find(self.fields, match.group(1)), match.group(2).strip()

    def stat_line(self, line):
        """'**STR** 3/12 · **HP** 4/6 · …' -> {'strength': 3, 'strength_max': 12, …}, or None."""
        result = {}
        for part in line.split('·'):
            match = re.match(r'^\s*\*{0,2}(.+?)\*{0,2}\s+(\d+)(?:\s*/\s*(\d+))?\s*$', part)
            key = match and _find(self.stats, match.group(1))
            if not key:
                return None
            result[key] = int(match.group(2))
            if key in dict(STATS):
                result[key + '_max'] = int(match.group(3) or match.group(2))
        return result or None

    def item(self, line, location):
        text = line[2:].strip()
        description = ''
        if DESCRIPTION_SEPARATOR in text:
            text, description = text.split(DESCRIPTION_SEPARATOR, 1)
        item = {'name': text.strip(), 'tags': [], 'location': location}
        match = re.match(r'^(.*\S)\s*\(([^()]*)\)$', text.strip())
        if match:
            parsed = self.item_details(match.group(2))
            if parsed is not None:  # Otherwise the parentheses are part of the name.
                item['name'] = match.group(1)
                item.update(parsed)
        item['name'] = self.item_names.get(item['name'].lower(), item['name'])
        if description.strip():
            item['description'] = description.strip()
        return item

    def item_details(self, text):
        result = {'tags': []}
        for detail in (part.strip() for part in text.split(',')):
            for field, patterns in (('uses', self.uses), ('charges', self.charges)):
                match = next((m for m in (p.match(detail) for p in patterns) if m), None)
                if match:
                    result['tags'].append(field)
                    result[field], result['max_' + field] = int(match.group(1)), int(match.group(2))
                    break
            else:
                tag = self.tags.get(detail.lower())
                if tag is None:
                    return None
                result['tags'].append(tag)
        return result

    # -- document --

    def parse(self, text):
        if len(text) > MAX_MARKDOWN:
            raise ValueError('Markdown file is too large')
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        data = {'name': '', 'background': '', 'edition': '2e', 'items': [], 'containers': [], 'pets': [],
                'custom_image': False, 'image_url': '', 'deprived': False, 'panicked': False, 'dead': False}
        for field, _label in SECTIONS:
            data[field] = ''
        for stat, _label in STATS:
            data[stat] = data[stat + '_max'] = 0
        data['gold'] = 0
        section, body = 'header', []
        chunks = []
        for line in lines:
            heading = re.match(r'^(#{1,2})\s+(.*?)\s*#*\s*$', line)
            if heading and len(heading.group(1)) == 1 and not data['name']:
                data['name'] = heading.group(2)
                continue
            key = heading and len(heading.group(1)) == 2 and _find(self.sections, heading.group(2))
            if key:
                chunks.append((section, body))
                section, body = key, []
            else:
                body.append(line)
        chunks.append((section, body))
        unknown = []
        for key, body in chunks:
            if key == 'header':
                unknown.extend(self.header(data, body))
            elif key == 'past':
                self.past(data, body)
            elif key == 'inventory':
                self.inventory(data, body)
            elif key == 'pets':
                self.pets(data, body)
            else:
                data[key] = _join(body)
        if unknown:  # Keep anything we could not place, rather than drop it.
            data['notes'] = '\n\n'.join(part for part in (data['notes'], '\n'.join(unknown).strip()) if part)
        if not data['name'].strip():
            raise ValueError('Missing character name')
        if not data['containers']:
            data['containers'] = [{'id': 0, 'name': 'Main', 'slots': 10}]
            for item in data['items']:
                item['location'] = 0
        return data

    def header(self, data, body):
        unknown = []
        for line in body:
            if not line.strip():
                continue
            key, value = self.field(line.strip())
            stats = None if key else self.stat_line(line.strip())
            if key == 'background':
                match = re.match(r'^(.*?)\s*\(([^()]*)\)$', value)
                if match and match.group(2).strip().lower() in self.barebones:
                    data['edition'], value = 'barebones', match.group(1)
                data['background'] = self.backgrounds.get(value.lower(), value)
            elif key == 'conditions':
                for name in value.split(','):
                    condition = _find(self.conditions, name)
                    if condition:
                        data[condition] = True
            elif stats:
                stats.pop('armor', None)  # Recomputed from the equipment.
                data.update(stats)
            else:
                unknown.append(line)
        return unknown

    def past(self, data, body):
        entries = []
        for line in body:
            question = re.match(r'^\*\*(.+)\*\*\s*$', line.strip())
            if question:
                entries.append([question.group(1), []])
            elif entries:
                entries[-1][1].append(line)
        for index, (question, answer) in enumerate(entries[:2], start=1):
            data[f'background_table{index}_question'] = question.strip()
            data[f'background_table{index}_answer'] = _join(answer)

    def container_heading(self, text):
        match = re.match(r'^(.*?)\s*\((\d+)\s+(.+?)\)$', text)
        if match and match.group(3).strip().lower() in self.slots:
            return match.group(1), int(match.group(2))
        return text, 10

    def inventory(self, data, body):
        location = None
        for line in body:
            heading = re.match(r'^###\s+(.*?)\s*#*\s*$', line)
            if heading:
                name, slots = self.container_heading(heading.group(1))
                location = len(data['containers'])
                data['containers'].append({'id': location, 'name': 'Main' if location == 0 and name.lower() in _labels('Main') else name,
                                           'slots': slots})
            elif re.match(r'^[-*]\s+', line):
                data['items'].append(self.item(line, location or 0))

    def pets(self, data, body):
        pet = None
        for line in body:
            heading = re.match(r'^###\s+(.*?)\s*#*\s*$', line)
            if heading:
                match = re.match(r'^(.*?)\s*\(([^()]*)\)$', heading.group(1))
                name, role = (match.group(1), match.group(2)) if match else (heading.group(1), '')
                pet = {'name': name.strip(), 'role': role.strip(), 'attack': '', 'armor': 0, 'gold': 0,
                       'items': [], 'containers': [{'id': 0, 'name': 'Main', 'slots': 10}], 'notes': []}
                for stat, _label in STATS:
                    pet[stat] = pet[stat + '_max'] = None
                data['pets'].append(pet)
                continue
            if pet is None:
                continue
            key, value = self.field(line.strip())
            stats = None if key else self.stat_line(line.strip()) if line.strip() else None
            if key == 'attack':
                pet['attack'] = value
            elif stats:  # A pet's own armor; equipment armor is added on top.
                pet.update(stats)
            elif re.match(r'^[-*]\s+', line):
                pet['items'].append(self.item(line, 0))
            else:
                pet['notes'].append(line)
        for pet in data['pets']:
            pet['notes'] = _join(pet['notes'])


def _join(lines):
    return '\n'.join(lines).strip()


def parse_character(text):
    """Read a Markdown sheet into the dictionary shape of a JSON character export."""
    return _Parser().parse(text)


def character_text(character, markdown=True):
    return render_character(character.export_data(), markdown=markdown)

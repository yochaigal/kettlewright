"""Party backgrounds: character options a campaign's modules give its parties.

Backgrounds live in the campaign's modules (Module.backgrounds, in the format of
the system's backgrounds table: name -> background); each party
says whether the official ones are offered too (set on the party page). Modules
bring them as Markdown (type: Background, see background_markdown).

Character creation for a party uses them: the creation request names the party
by its join code, use_party_backgrounds() puts the party's list on flask.g, and
load_backgrounds() returns it for the rest of the request. Characters keep a copy
of what they rolled, so later changes never alter them.
"""
from kettlewright import system
import copy
import json
import os

from flask import g, has_app_context

MAX_BACKGROUNDS = 100
MAX_NAME = 64
MAX_TEXT = 2000
MAX_LIST = 30
MAX_OPTIONS = 20
MAX_TAGS = 20

ITEM_TEXT = {'name': 100, 'description': MAX_TEXT}
ITEM_INTEGERS = ('uses', 'charges', 'max_charges')


class BackgroundError(ValueError):
    pass


def official_backgrounds():
    return system().content.load('backgrounds')


def _text(value, where, limit=MAX_TEXT, required=False):
    if value is None and not required:
        return ''
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise BackgroundError(f'{where}: expected text of at most {limit} characters.')
    return value.strip()


def _integer(value, where, low=0, high=1000):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise BackgroundError(f'{where}: expected a whole number from {low} to {high}.')
    return value


def _list(value, where, limit=MAX_LIST):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > limit:
        raise BackgroundError(f'{where}: expected a list of at most {limit} entries.')
    return value


def _item(item, where):
    if not isinstance(item, dict):
        raise BackgroundError(f'{where}: an item must be an object with a name.')
    clean = {'name': _text(item.get('name'), f'{where} name', ITEM_TEXT['name'], True),
             'tags': [_text(tag, f'{where} tag', 40, True) for tag in _list(item.get('tags'), f'{where} tags', MAX_TAGS)]}
    if 'description' in item:
        clean['description'] = _text(item['description'], f'{where} description')
    for key in ITEM_INTEGERS:
        if key in item:
            clean[key] = _integer(item[key], f'{where} {key}')
    if 'armor_active' in item:
        if not isinstance(item['armor_active'], bool):
            raise BackgroundError(f'{where} armor_active: expected true or false.')
        clean['armor_active'] = item['armor_active']
    return clean


def _container(container, where):
    if not isinstance(container, dict):
        raise BackgroundError(f'{where}: a container must be an object with a name and slots.')
    clean = {'name': _text(container.get('name'), f'{where} name', 100, True),
             'slots': _integer(container.get('slots'), f'{where} slots', 0, 100)}
    if 'carried_by' in container:
        clean['carried_by'] = _text(container['carried_by'], f'{where} carried_by', 100, True)
    if 'load' in container:
        clean['load'] = _integer(container['load'], f'{where} load', 0, 100)
    return clean


def known_pets():
    return list(system().content.load('pets'))


def _pet(name, where):
    """Pets come from the pet catalog (the system's pets table), which holds their stats."""
    name = _text(name, where, 100, True)
    pets = known_pets()
    if name not in pets:
        shown = [_shown_pet(pet) for pet in pets] if _localized() else list(pets)
        raise BackgroundError(f'{where}: unknown pet "{name}". Use one of: {", ".join(shown)}.')
    return name


def _option(option, where):
    if not isinstance(option, dict):
        raise BackgroundError(f'{where}: an option must be an object with a description.')
    clean = {'description': _text(option.get('description'), f'{where} description', required=True)}
    if option.get('items'):  # No items is the same as none listed (Markdown writes neither).
        clean['items'] = [_item(item, f'{where} item') for item in _list(option['items'], f'{where} items')]
    if 'pets' in option:
        clean['pets'] = [_pet(pet, f'{where} pet') for pet in _list(option['pets'], f'{where} pets', 5)]
    if 'containers' in option:
        clean['containers'] = [_container(c, f'{where} container') for c in _list(option['containers'], f'{where} containers', 5)]
    if 'bonus_gold' in option:
        clean['bonus_gold'] = _integer(option['bonus_gold'], f'{where} bonus_gold', 0, 10000)
    if 'gear_table' in option:
        clean['gear_table'] = _integer(option['gear_table'], f'{where} gear_table', 0, 100)
    return clean


def _table(table, where):
    if not isinstance(table, dict):
        raise BackgroundError(f'{where}: expected an object with a question and options.')
    options = _list(table.get('options'), f'{where} options', MAX_OPTIONS)
    if not options:
        raise BackgroundError(f'{where}: add at least one option.')
    return {'question': _text(table.get('question'), f'{where} question', 500, True),
            'options': [_option(option, f'{where} option {i + 1}') for i, option in enumerate(options)]}


def validate_background(name, data):
    """One background, cleaned to the keys character creation reads. Raises BackgroundError."""
    name = _text(name, 'Background name', MAX_NAME, True)
    if name == 'Custom':
        raise BackgroundError('"Custom" is reserved: choose another background name.')
    where = f'Background "{name}"'
    if not isinstance(data, dict):
        raise BackgroundError(f'{where}: expected an object.')
    names = [_text(item, f'{where} name', MAX_NAME, True) for item in _list(data.get('names'), f'{where} names')]
    if not names:
        raise BackgroundError(f'{where}: add at least one character name.')
    clean = {'background_description': _text(data.get('background_description'), f'{where} background_description',
                                             required=True),
             'names': names,
             'starting_gear': [_item(item, f'{where} starting gear')
                               for item in _list(data.get('starting_gear'), f'{where} starting_gear')]}
    for key in ('table1', 'table2'):
        if key not in data:
            raise BackgroundError(f'{where}: {key} is missing (a question and its options).')
        clean[key] = _table(data[key], f'{where} {key}')
    if 'starting_containers' in data:
        clean['starting_containers'] = [_container(c, f'{where} starting container')
                                        for c in _list(data['starting_containers'], f'{where} starting_containers', 5)]
    return name, clean


def add_backgrounds(module, backgrounds):
    """Add or replace a module's backgrounds by name. The caller commits."""
    merged = dict(module.backgrounds or {})
    merged.update(backgrounds)
    if len(merged) > MAX_BACKGROUNDS:
        raise BackgroundError(f'A module can have at most {MAX_BACKGROUNDS} backgrounds.')
    module.backgrounds = merged


def remove_background(module, name):
    remaining = {key: value for key, value in (module.backgrounds or {}).items() if key != name}
    module.backgrounds = remaining or None


def custom_backgrounds(campaign):
    """The backgrounds of the campaign's modules; a later module's background replaces an earlier one of that name."""
    custom = {}
    for module in (campaign.modules if campaign is not None else []):
        custom.update(module.backgrounds or {})
    return custom


def party_backgrounds(party):
    """What a party's characters choose from: official ones (unless the party hides them), then its campaign's
    modules' ones. A module background with an official name replaces it. Never empty: with no module
    backgrounds the official ones are offered even when hidden."""
    custom = custom_backgrounds(party.campaign)
    backgrounds = official_backgrounds() if party.official_backgrounds or not custom else {}
    backgrounds.update(copy.deepcopy(custom))
    return backgrounds


def background_panel(party):
    """The party page's Backgrounds section (Warden): the official switch, the modules' backgrounds, the result."""
    modules = [module for module in (party.campaign.modules if party.campaign else []) if module.backgrounds]
    return {'official': party.official_backgrounds, 'official_count': len(official_backgrounds()),
            'modules': [(module, sorted(module.backgrounds)) for module in modules],
            'offered': sorted(party_backgrounds(party)), 'fallback': not party.official_backgrounds and not modules,
            # Cairn Barebones: the d100 table, the same module backgrounds (name and starting gear).
            'barebones': party.official_barebones, 'barebones_count': len(official_barebones()),
            'barebones_offered': len(party_barebones_backgrounds(party)),
            'barebones_fallback': not party.official_barebones and not modules}


def official_barebones():
    """The Cairn Barebones d100 background table: a name and its items."""
    from app.lib.barebones import _data
    return list(_data()['backgrounds'])


def party_barebones_backgrounds(party):
    """What a party's Barebones characters roll on: the official d100 table (unless the party hides it), then its
    campaign's module backgrounds as a name and their starting gear (Barebones has no background tables). A module
    background with an official name replaces it. Never empty: without module backgrounds the official table stays."""
    custom = [{'name': name, 'items': copy.deepcopy(background.get('starting_gear', []))}
              for name, background in sorted(custom_backgrounds(party.campaign).items())]
    if not party.official_barebones and custom:
        return custom
    names = {row['name'] for row in custom}
    return [row for row in official_barebones() if row['name'] not in names] + custom


def use_party_barebones(party):
    """For the rest of this request, Barebones creation rolls on the party's background table."""
    if party is not None and (custom_backgrounds(party.campaign) or not party.official_barebones):
        g.barebones_backgrounds = party_barebones_backgrounds(party)


def has_custom_options(party):
    return bool(custom_backgrounds(party.campaign)) or not party.official_backgrounds


# ----- Markdown backgrounds -----
# The format modules are written in. JSON stays the exact format (and what Markdown
# cannot say falls back to it); this one is easy to write by hand:
#
#   ---
#   layout: default
#   title: Tidewatcher
#   type: Background
#   ---
#   You keep the lighthouse of a drowned town.      (description: text before the first ##)
#
#   ## Names
#   Mara, Oskel                                     (comma separated, or a list)
#
#   ## Starting gear
#   - Storm Lantern
#   - Rations [uses 3]                              (tags in [ ], with uses N, charges N/M, armor active)
#   - Warble-Whistle [charges 3/3] — Recharge: ...  (a description after " — ")
#
#   ## Starting containers                          (optional)
#   - Cart [6 slots, carried by Mule, load 2]
#
#   ## What did the sea take?                       (the first other heading is table 1, the next table 2)
#   - Your sister. Take her Locket.                 (an option; its rewards as a nested list:)
#     - Locket [petty]                              an item,
#     - 5 gold                                      bonus gold,
#     - pet: Raven Familiar                         a pet from the pet catalog,
#     - container: Donkey [4 slots]                 a container,
#     - gear table: 20

import re

# What "New background" starts from: a complete, valid example to change.
BACKGROUND_TEMPLATE = """---
layout: default
title: Tidewatcher
type: Background
---
You keep the lighthouse of a drowned town, and the lamp has never gone out.

## Names
Mara, Oskel, Brine, Ilsa, Corwen, Petra

## Starting gear
- Rations [uses 3]
- Storm Lantern
- Gaff [d6]

## What did the sea take?
- Your sister. Take her Locket.
  - Locket [petty]
- Your name. Nobody in town remembers it.
  - 5 gold

## Who still writes to you?
- A smuggler who owes you a favor.
- A raven that finds you anywhere.
  - pet: Raven Familiar
"""

SECTIONS = {'names': 'names', 'starting gear': 'starting_gear', 'starting containers': 'starting_containers'}
# The English headings of those sections and the words of the format. Files keep them in English; the editors
# and the wiki show them in the reader's language, and the parser takes either. A translation may list other
# forms after a "|" ("tirado por|tirada por"): the first is the one shown, all of them are read.
SECTION_HEADINGS = {'names': 'Names', 'starting_gear': 'Starting gear', 'starting_containers': 'Starting containers'}
KEYWORDS = ('uses', 'charges', 'armor active', 'armor inactive', 'slots', 'carried by', 'load', 'gold', 'pet',
            'container', 'gear table')
# Tags that the app knows by name, shown translated on items: written in either language, kept in English.
KNOWN_TAGS = ('petty', 'bulky', 'blast')


def _localized():
    from flask import has_request_context
    return has_request_context()


def section_headings():
    """The section headings in the reader's language (English outside a request)."""
    if not _localized():
        return dict(SECTION_HEADINGS)
    from flask_babel import pgettext
    return {key: pgettext('background section', heading) for key, heading in SECTION_HEADINGS.items()}


def _forms(word):
    """Every form of a format word that is read: the English one and the reader's ones."""
    forms = [word]
    if _localized():
        from flask_babel import pgettext
        forms += [form.strip() for form in pgettext('background keyword', word).split('|') if form.strip()]
    return list(dict.fromkeys(form.casefold() for form in forms))


def shown_words(localized):
    """The format words as they are written: in English, or in the reader's language."""
    words = {word: word for word in KEYWORDS}
    tags = {tag: tag for tag in KNOWN_TAGS}
    if localized and _localized():
        from flask_babel import gettext, pgettext
        words = {word: pgettext('background keyword', word).split('|')[0].strip() or word for word in KEYWORDS}
        tags = {tag: gettext(tag) for tag in KNOWN_TAGS}
    return {'words': words, 'tags': tags, 'headings': section_headings() if localized else dict(SECTION_HEADINGS),
            'localized': bool(localized and _localized())}


def _alternatives(word):
    return '|'.join(re.escape(form) for form in _forms(word))


def _section_key(heading):
    key = SECTIONS.get(heading.casefold())
    if key is None:
        key = {shown.casefold(): key for key, shown in section_headings().items()}.get(heading.casefold())
    return key


def _known_tag(token):
    """A known tag written in the reader's language, as its English tag (else the token as written)."""
    lower = token.casefold()
    if lower in KNOWN_TAGS:
        return lower
    if _localized():
        from flask_babel import gettext
        for tag in KNOWN_TAGS:
            if gettext(tag).casefold() == lower:
                return tag
    return token


def _pet_name(name):
    """A pet written by its name in the reader's language, as its catalog name."""
    pets = known_pets()
    if name in pets or not _localized():
        return name
    from flask_babel import gettext
    return {gettext(pet).casefold(): pet for pet in pets}.get(name.casefold(), name)


DASH = re.compile(r'\s+(?:—|--)\s+')
BRACKETS = re.compile(r'^(?P<name>.*?)\s*\[(?P<tags>[^\[\]]*)\]\s*$')


def _split(line):
    """'Name [a, b] — description' -> (name, [tokens], description or None)."""
    parts = DASH.split(line, maxsplit=1)
    head, description = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else None)
    match = BRACKETS.match(head)
    if not match:
        return head, [], description
    return match.group('name').strip(), [t.strip() for t in match.group('tags').split(',') if t.strip()], description


def _md_item(line, where):
    name, tokens, description = _split(line)
    return item_from_tokens(name, tokens, description, where)


def item_from_tokens(name, tokens, description, where):
    """An item from its name, its bracket tokens ([petty, uses 3, charges 2/3]) and description (or None)."""
    item = {'name': name, 'tags': []}
    for token in tokens:
        lower = token.casefold()
        uses = re.fullmatch(rf'(?:{_alternatives("uses")})\s+(\d+)', lower)
        charges = re.fullmatch(rf'(?:{_alternatives("charges")})\s+(\d+)(?:\s*/\s*(\d+))?', lower)
        count = re.fullmatch(r'([a-z_]+)\s*=\s*(\d+)', lower)
        if count and count.group(1) in ITEM_INTEGERS:
            item[count.group(1)] = int(count.group(2))
        elif uses:
            item['tags'].append('uses')
            item['uses'] = int(uses.group(1))
        elif charges:
            item['tags'].append('charges')
            item['charges'] = int(charges.group(1))
            if charges.group(2) is not None:
                item['max_charges'] = int(charges.group(2))
        elif lower in _forms('armor active') or lower in _forms('armor inactive'):
            item['armor_active'] = lower in _forms('armor active')
        else:
            item['tags'].append(_known_tag(token))
    if description is not None:
        item['description'] = description
    return _item(item, where)


def _md_container(line, where):
    name, tokens, _ = _split(line)
    container = {'name': name}
    for token in tokens:
        lower = token.casefold()
        slots = re.fullmatch(rf'(\d+)\s+(?:{_alternatives("slots")}|slot)', lower)
        load = re.fullmatch(rf'(?:{_alternatives("load")})\s+(\d+)', lower)
        carried = re.match(rf'(?:{_alternatives("carried by")})\s+', lower)
        if slots:
            container['slots'] = int(slots.group(1))
        elif load:
            container['load'] = int(load.group(1))
        elif carried:
            container['carried_by'] = token[carried.end():].strip()
        else:
            raise BackgroundError(f'{where}: unknown container detail "{token}". Use N slots, carried by X or load N.')
    return _container(container, where)


def _md_reward(option, line, where):
    lower = line.casefold()
    gold = re.fullmatch(rf'\+?(\d+)\s*(?:{_alternatives("gold")}|gp)', lower)
    gear = re.fullmatch(rf'(?:{_alternatives("gear table")}):?\s*(\d+)', lower)
    pet = re.match(rf'(?:{_alternatives("pet")}):', lower)
    container = re.match(rf'(?:{_alternatives("container")}):', lower)
    if gold:
        option['bonus_gold'] = int(gold.group(1))
    elif gear:
        option['gear_table'] = int(gear.group(1))
    elif pet:
        option.setdefault('pets', []).append(_pet_name(line[pet.end():].strip()))
    elif container:
        option.setdefault('containers', []).append(_md_container(line[container.end():].strip(), where))
    else:
        option.setdefault('items', []).append(_md_item(line, where))


def _list_items(lines, where):
    """Top-level '- ' entries, each with the nested '- ' lines under it."""
    entries = []
    for line in lines:
        if not line.strip():
            continue
        nested = re.match(r'^\s{2,}[-*]\s+(.*)$', line)
        top = re.match(r'^[-*]\s+(.*)$', line)
        if top:
            entries.append([top.group(1).strip(), []])
        elif nested and entries:
            entries[-1][1].append(nested.group(1).strip())
        elif entries and not nested:
            entries[-1][0] += ' ' + line.strip()  # A wrapped line.
        else:
            raise BackgroundError(f'{where}: expected a list ("- ...").')
    return entries


def background_from_markdown(title, body):
    """One background from a Markdown body (after its front matter). Raises BackgroundError."""
    where = f'Background "{title}"'
    description, sections, current = [], [], None
    for line in body.splitlines():
        heading = re.match(r'^##\s+(.+?)\s*#*\s*$', line)
        if heading:
            current = [heading.group(1).strip(), []]
            sections.append(current)
        elif current is None:
            description.append(line)
        else:
            current[1].append(line)
    data, tables = {'background_description': '\n'.join(description).strip()}, []
    for heading, lines in sections:
        key = _section_key(heading)
        if key == 'names':
            text = ' '.join(re.sub(r'^\s*[-*]\s+', '', line).strip() + (',' if re.match(r'^\s*[-*]\s+', line) else '')
                           for line in lines if line.strip())
            data['names'] = [name.strip() for name in text.split(',') if name.strip()]
        elif key == 'starting_gear':
            data['starting_gear'] = [_md_item(text, f'{where} starting gear') for text, _ in _list_items(lines, where)]
        elif key == 'starting_containers':
            data['starting_containers'] = [_md_container(text, f'{where} starting container')
                                           for text, _ in _list_items(lines, where)]
        else:
            options = []
            for text, rewards in _list_items(lines, f'{where} "{heading}"'):
                option = {'description': text}
                for reward in rewards:
                    _md_reward(option, reward, f'{where} "{heading}"')
                options.append(option)
            tables.append({'question': heading, 'options': options})
    if len(tables) != 2:
        raise BackgroundError(f'{where}: write exactly two tables, each a ## question heading with its options '
                              f'(found {len(tables)}).')
    data['table1'], data['table2'] = tables
    return validate_background(title, data)


def _item_markdown(item, shown=None):
    shown = shown or shown_words(False)
    words, tags = shown['words'], shown['tags']
    tokens = []
    for tag in item.get('tags', []):
        if tag == 'uses' and 'uses' in item:
            tokens.append(f'{words["uses"]} {item["uses"]}')
        elif tag == 'charges' and 'charges' in item:
            tokens.append(f'{words["charges"]} {item["charges"]}' + (f'/{item["max_charges"]}' if 'max_charges' in item else ''))
        else:
            tokens.append(tags.get(tag, tag))
    if 'armor_active' in item:
        tokens.append(words['armor active'] if item['armor_active'] else words['armor inactive'])
    # Counts that no tag shows (say "1 use" written as a plain tag): key=value keeps them.
    shown = {'uses'} if 'uses' in item.get('tags', []) else set()
    shown |= {'charges', 'max_charges'} if 'charges' in item.get('tags', []) else set()
    tokens += [f'{key}={item[key]}' for key in ITEM_INTEGERS if key in item and key not in shown]
    line = item['name'] + (f' [{", ".join(tokens)}]' if tokens else '')
    return line + (f' — {item["description"]}' if 'description' in item else '')


def _container_markdown(container, shown=None):
    words = (shown or shown_words(False))['words']
    tokens = [f'{container["slots"]} {words["slots"]}']
    if 'carried_by' in container:
        tokens.append(f'{words["carried by"]} {container["carried_by"]}')
    if 'load' in container:
        tokens.append(f'{words["load"]} {container["load"]}')
    return f'{container["name"]} [{", ".join(tokens)}]'


def background_markdown(name, background, localized=False):
    """The Markdown file for a background: it reads back as the same background. Files are in English;
    localized=True writes the headings and format words in the reader's language (the editor, the wiki)."""
    shown = shown_words(localized)
    words, headings = shown['words'], shown['headings']
    pet_name = _shown_pet if shown['localized'] else (lambda pet: pet)
    lines = ['---', 'layout: default', f'title: {json.dumps(name, ensure_ascii=False)}', 'type: Background', '---',
             background['background_description'], '', f'## {headings["names"]}', ', '.join(background['names']), '',
             f'## {headings["starting_gear"]}']
    lines += [f'- {_item_markdown(item, shown)}' for item in background.get('starting_gear', [])]
    if background.get('starting_containers'):
        lines += ['', f'## {headings["starting_containers"]}']
        lines += [f'- {_container_markdown(c, shown)}' for c in background['starting_containers']]
    for key in ('table1', 'table2'):
        lines += ['', f'## {background[key]["question"]}']
        for option in background[key]['options']:
            lines.append(f'- {option["description"]}')
            rewards = [_item_markdown(item, shown) for item in option.get('items', [])]
            rewards += [f'{option["bonus_gold"]} {words["gold"]}'] if 'bonus_gold' in option else []
            rewards += [f'{words["pet"]}: {pet_name(pet)}' for pet in option.get('pets', [])]
            rewards += [f'{words["container"]}: {_container_markdown(c, shown)}' for c in option.get('containers', [])]
            rewards += [f'{words["gear table"]}: {option["gear_table"]}'] if 'gear_table' in option else []
            lines += [f'  - {reward}' for reward in rewards]
    return '\n'.join(lines) + '\n'


def _shown_pet(pet):
    from flask_babel import gettext
    return gettext(pet)


def background_template():
    """What "New background" starts from, in the reader's language."""
    if not _localized():
        return BACKGROUND_TEMPLATE
    from flask_babel import gettext
    return gettext(BACKGROUND_TEMPLATE)


def parse_background_text(text, source='background'):
    """One Markdown background, as a Warden wrote or uploaded it (Markdown is the only format people write)."""
    stripped = text.lstrip('\ufeff').strip()
    if stripped.startswith('{') or stripped.startswith('['):
        raise BackgroundError(f'{source}: backgrounds are Markdown files (type: Background), not JSON.')
    from app.lib.campaign_import import parse_markdown, ImportError as ArchiveError
    try:
        row = parse_markdown(source, stripped)
    except ArchiveError as exc:
        raise BackgroundError(f'{source}: {exc}') from exc
    if row['category'] != 'background':
        raise BackgroundError(f'{source}: use type: Background in the front matter.')
    name, background = background_from_markdown(row['title'], row['body'])
    return {name: background}


def use_party_backgrounds(party):
    """For the rest of this request, character creation uses the party's backgrounds."""
    if party is not None and has_custom_options(party):
        g.campaign_backgrounds = party_backgrounds(party)


def active_backgrounds():
    """The campaign backgrounds set for this request, or None for the official ones."""
    if not has_app_context():
        return None
    backgrounds = g.get('campaign_backgrounds')
    return copy.deepcopy(backgrounds) if backgrounds is not None else None


def party_for_code(code):
    """The party with this join code, or None."""
    from app.models import Party
    code = (code or '').strip()
    if not code or len(code) > 64:
        return None
    return Party.query.filter_by(join_code=code).first()

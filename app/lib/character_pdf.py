"""Fill the Cairn character sheets without clipping character data (#142)."""
from functools import lru_cache
from html import unescape
from io import BytesIO
import json
from pathlib import Path
import re
from threading import Lock
from urllib.parse import unquote
from xml.sax.saxutils import escape

import bleach
from flask import current_app
from flask_babel import _
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from app.lib.portraits import portrait_directory


ASSETS = Path(__file__).resolve().parents[1] / 'pdf_templates'
# Coordinates use points measured from the top-left of each original A4 sheet.
LAYOUTS = {
    'landscape': dict(
        page_size=(841.89, 595.276), portrait=(252.5, 185.5, 105, 105),
        name=(48, 164, 157), background=(48, 208, 157),
        deprived=(481, 83), status=(399, 305, 95),
        attributes=[(134, 300, 134, 345), (207, 300, 207, 345), (279, 300, 279, 345), (350, 300, 350, 345)],
        armor=(481, 140), gold=(469, 337),
        inventory=(536, 166, 18.7, 169), fatigue=(726, 164),
        petty=[(399, 196 + i * 16.5, 93) for i in range(6)],
        traits=[(227 if i < 4 else 265, 410 + i * 16.5, 118 if i < 4 else 80) for i in range(10)],
        bonds=[(362, 410 + i * 17, 140) for i in range(4)],
        omens=[(362, 508 + i * 16.5, 140) for i in range(4)],
        notes=[(523, 410 + i * 16.5, 229) for i in range(10)],
    ),
    'portrait': dict(
        page_size=(595.321191, 841.921684), portrait=(87, 216, 110, 110),
        name=(65, 282, 155), background=(345, 193, 190),
        deprived=(234, 594), status=(52, 309, 180),
        attributes=[(400, 413, 456, 413), (400, 459, 456, 459), (400, 505, 456, 505), (156, 551, 207, 551)],
        armor=(234, 642), gold=(526, 790),
        inventory=(374, 580, 15.5, 151), fatigue=(538, 580),
        petty=[(366, 759 + i * 15, 107) for i in range(4)],
        traits=[(345, 244 + i * 17, 205) for i in range(4)],
        bonds=[(52, 690, 154), (52, 706, 188), (52, 722, 188)],
        omens=[(52, 755, 188), (52, 770, 188)],
        notes=[(40, 421 + i * 11, 201) for i in range(9)],
    ),
}
FONT, BOLD = 'CairnPDFSerif', 'CairnPDFSerifBold'
_font_lock = Lock()


@lru_cache(maxsize=1)
def _register_fonts():
    with _font_lock:
        pdfmetrics.registerFont(TTFont(FONT, str(ASSETS / 'fonts/DejaVuSerif.ttf')))
        pdfmetrics.registerFont(TTFont(BOLD, str(ASSETS / 'fonts/DejaVuSerif-Bold.ttf')))


def plain_text(value):
    value = str(value or '').replace('\r\n', '\n').replace('\r', '\n')
    value = re.sub(r'<\s*br\s*/?\s*>|</\s*(?:p|div|li)\s*>', '\n', value, flags=re.I)
    return unescape(bleach.clean(value, tags=[], strip=True)).strip()


def _take_line(value, width, font=FONT, size=9):
    """Wrap at a word boundary, including unbroken names and URLs."""
    value = value.lstrip(' ')
    used, space = 0, 0
    for index, char in enumerate(value):
        if char == '\n':
            return value[:index].rstrip(), value[index + 1:]
        used += pdfmetrics.stringWidth(char, font, size)
        if used > width:
            cut = space or max(index, 1)
            return value[:cut].rstrip(), value[cut:].lstrip(' ')
        if char == ' ':
            space = index
    return value, ''


def _portrait(character):
    """Read only managed uploads/built-ins; never fetch a user URL on the server."""
    value = unquote(character.image_url or '')
    if character.custom_image:
        if not re.fullmatch(r'/portraits/[0-9a-f]{64}\.webp', value):
            return None
        root = portrait_directory().resolve()
        path = root / value.rsplit('/', 1)[-1]
    else:
        root = (Path(current_app.static_folder) / 'images/portraits').resolve()
        path = (root / (value or 'default-portrait.webp')).resolve()
    if not path.resolve().is_relative_to(root) or not path.is_file():
        return None
    try:
        with Image.open(path) as image:
            if image.width > 4096 or image.height > 4096:
                return None
            image.load()
            return ImageReader(image.convert('RGBA'))
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None


def _item_title(item):
    from app.lib.translations import translate_term
    details = []
    tags = item.get('tags') or []
    for tag in tags:
        if tag in ('petty', 'bonus defense'):
            continue
        if tag == 'uses':
            details.append(_('%(count)s uses', count=item.get('uses', 0)))
        elif tag == 'charges':
            details.append(_('%(current)s/%(maximum)s charges', current=item.get('charges', 0),
                             maximum=item.get('max_charges', 0)))
        elif 'Armor' in tag and 'bonus defense' in tags:
            details.append('+' + _(tag))
        else:
            details.append(_(tag))
    name = plain_text(translate_term(item.get('name') or '', 'equipment'))
    return name + (' (' + ', '.join(details) + ')' if details else '')


def _flatten_prefilled_fields(page):
    """Stamp form fields that already hold a value onto the page, as they look.

    The Barebones sheet prints its trait labels ("Physique: ") as pre-filled
    field values; reusing each field's own appearance keeps their exact style.
    """
    from pypdf.generic import ContentStream, DictionaryObject, NameObject
    stamps = []
    for index, annotation in enumerate(page.get('/Annots') or []):
        annotation = annotation.get_object()
        value = annotation.get('/V') or annotation.get('/Parent', {}).get('/V')
        appearance = annotation.get('/AP', {}).get('/N')
        if annotation.get('/Subtype') != '/Widget' or not value or appearance is None:
            continue
        name = f'/KwField{index}'
        resources = page.setdefault(NameObject('/Resources'), DictionaryObject())
        xobjects = resources.setdefault(NameObject('/XObject'), DictionaryObject())
        xobjects[NameObject(name)] = annotation['/AP'].raw_get('/N')
        x0, y0 = (min(float(a), float(b)) for a, b in zip(annotation['/Rect'][:2], annotation['/Rect'][2:]))
        stamps.append(f'q 1 0 0 1 {x0:.3f} {y0:.3f} cm {name} Do Q')
    if stamps:
        content = ContentStream(page.get_contents(), page.pdf)
        content.set_data(b'q\n' + content.get_data() + b'\nQ\n' + '\n'.join(stamps).encode())
        page.replace_contents(content)


class CharacterSheet:
    def __init__(self, character, party=None, orientation='landscape', export_attributes=True):
        _register_fonts()
        self.orientation = orientation
        self.layout = LAYOUTS[orientation]
        self.page_size = self.layout['page_size']
        self.character = character
        self.party = party
        self.export_attributes = export_attributes
        self.sections = []
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=self.page_size)

    def text(self, value, x, top, size=9, font=FONT, centered=False):
        self.canvas.setFont(font, size)
        draw = self.canvas.drawCentredString if centered else self.canvas.drawString
        draw(x, self.page_size[1] - top, str(value if value is not None else ''))

    def section(self, title, value):
        value = plain_text(value)
        if value:
            self.sections.append((str(title), value))

    def single_line(self, value, x, top, width, size=9, font=FONT, title=None):
        value = plain_text(value).replace('\n', ' ')
        while size > 9 and pdfmetrics.stringWidth(value, font, size) > width:
            size = max(9, size - .5)
        if pdfmetrics.stringWidth(value, font, size) > width:
            if title:
                self.section(title, value)
            prefix, _rest = _take_line(value, width - pdfmetrics.stringWidth('...', font, size), font, size)
            value = prefix + '...'
        self.text(value, x, top, size, font)

    def ruled(self, title, value, lines):
        value = plain_text(value)
        rest = value
        rendered = []
        for x, top, width in lines:
            line, rest = _take_line(rest, width)
            rendered.append((line, x, top, width))
        if rest:
            self.section(title, value)
            _line, x, top, width = rendered[-1]
            rendered[-1] = (_('See extra pages.'), x, top, width)
        for line, x, top, width in rendered:
            self.single_line(line, x, top, width)

    def draw(self):
        c = self.character
        layout = self.layout
        portrait = _portrait(c)
        if portrait:
            x, bottom, width, height = layout['portrait']
            self.canvas.drawImage(portrait, x, self.page_size[1] - bottom, width=width, height=height,
                                  preserveAspectRatio=True, anchor='c', mask='auto')
        elif c.custom_image and c.image_url:
            self.section(_('Portrait URL'), c.image_url)
        self.single_line(c.name, *layout['name'], 16, BOLD, _('Name'))
        self.single_line(_(c.background), *layout['background'], 12, title=_('Background'))
        if self.orientation == 'landscape':
            for center in (134, 207, 279, 350):
                self.text(_('current'), center, 277, 7, centered=True)
                self.text(_('max'), center, 327, 7, centered=True)
        for index, attribute in enumerate(('strength', 'dexterity', 'willpower', 'hp')):
            x, current_top, maximum_x, maximum_top = layout['attributes'][index]
            self.text(getattr(c, attribute + '_max'), maximum_x, maximum_top, 14, centered=True)
            if self.export_attributes:
                value = c.hpValue()[0] if attribute == 'hp' else getattr(c, attribute)
                self.text(value, x, current_top, 14, centered=True)
        if self.export_attributes:
            self.text(c.armorValue(), *layout['armor'], 12, centered=True)
            self.text(c.gold, *layout['gold'], 10, centered=True)
        if c.deprived:
            self.text('X', *layout['deprived'], 14, centered=True)
        states = [label for condition, label in ((c.dead, _('Dead')), (c.panicked, _('PANICKED'))) if condition]
        if states:
            self.single_line(' / '.join(states), *layout['status'], title=_('Status'))

        items = json.loads(c.items or '[]')
        main = [it for it in items if it.get('location') == 0]
        petty = [it for it in main if 'petty' in it.get('tags', []) and 'bulky' not in it.get('tags', [])]
        x, top, step, width = layout['inventory']
        fatigue_x, fatigue_top = layout['fatigue']
        slot = 0
        for item in main:
            if item in petty:
                continue
            slots = 2 if 'bulky' in item.get('tags', []) else 1
            title = _item_title(item)
            if slot + slots <= 10:
                self.single_line(title, x, top + slot * step, width, title=_('Inventory details'))
                if slots == 2:
                    self.single_line(_('Occupied by bulky item above'), x, top + (slot + 1) * step, width)
                if item.get('name') == 'Fatigue':
                    self.text('X', fatigue_x, fatigue_top + slot * step, 9, centered=True)
            else:
                self.section(_('Additional inventory'), title)
            slot += slots
        self.ruled(_('Petty Items'), '\n'.join(_item_title(it) for it in petty), layout['petty'])
        self.container_sections(items)

        self.ruled(_('Traits'), c.traits, layout['traits'])
        self.ruled(_('Bonds'), c.bonds, layout['bonds'])
        self.ruled(_('Omens'), c.omens, layout['omens'])
        for index in (1, 2):
            question = getattr(c, f'background_table{index}_question', None)
            answer = getattr(c, f'background_table{index}_answer', None)
            if question or answer:
                self.section(question or _('Background answer %(number)s', number=index), answer or '')
        self.ruled(_('Notes'), c.notes, layout['notes'])
        self.section(_('Description'), c.description)
        self.section(_('Scars'), c.scars)
        self.companion_sections()
        return self.finish(ASSETS / f'cairn-2e-{self.orientation}-a4.pdf', f'{c.name} - Cairn {self.orientation} A4')

    def container_sections(self, items):
        """Other containers, odd capacities and orphaned items go to the appendix."""
        c = self.character
        for container in json.loads(c.containers or '[]'):
            contents = [_item_title(it) for it in items if it.get('location') == container['id']]
            if container['id'] != 0 and contents:
                self.section(container['name'], '\n'.join(contents))
            if container['id'] == 0 and int(container['slots']) != 10:
                self.section(_('Inventory capacity'), _('%(count)s slots', count=container['slots']))
        known_ids = {container['id'] for container in json.loads(c.containers or '[]')} | {0}
        self.section(_('Unassigned items'), '\n'.join(_item_title(it) for it in items if it.get('location') not in known_ids))

    def companion_sections(self):
        c = self.character
        for pet in c.pets:
            stats = ' · '.join(label + ' ' + (str(getattr(pet, stat)) + '/' + str(getattr(pet, stat+'_max')) if getattr(pet, stat) is not None else '—')
                               for stat, label in [('hp','HP'),('strength','STR'),('dexterity','DEX'),('willpower','WIL')])
            lines = [stats, _('Armor') + ': ' + str(pet.armorValue()), pet.attack, pet.notes]
            for container in json.loads(pet.containers):
                lines.append(container['name'] + ' (' + str(container['slots']) + ' ' + _('slots') + ')')
                lines.extend(_item_title(it) for it in json.loads(pet.items) if it['location'] == container['id'])
            self.section(_('Pet') + ': ' + pet.name, '\n'.join(lines))
        if self.party:
            self.section(_('Party'), self.party.name + '\n' + (self.party.description or ''))

    def finish(self, template_path, title):
        """Stamp the drawn page onto the sheet template and append overflow pages."""
        self.canvas.save()
        writer = PdfWriter(clone_from=PdfReader(template_path))
        _flatten_prefilled_fields(writer.pages[0])
        # Drop form widgets: the values are drawn onto the page itself.
        writer.remove_annotations(subtypes='/Widget')
        writer._root_object.pop('/AcroForm', None)
        writer.pages[0].merge_page(PdfReader(self.buffer).pages[0])
        if self.sections:
            for page in PdfReader(self.appendix()).pages:
                writer.add_page(page)
        writer.add_metadata({'/Title': title, '/Author': 'Kettlewright'})
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    def appendix(self):
        buffer = BytesIO()
        style = ParagraphStyle('body', fontName=FONT, fontSize=11, leading=16,
                               spaceAfter=12, splitLongWords=True)
        heading = ParagraphStyle('heading', fontName=BOLD, fontSize=13, leading=17,
                                 spaceBefore=10, spaceAfter=6, keepWithNext=True)
        story = []
        for title, value in self.sections:
            section = [Paragraph(escape(title), heading)]
            for paragraph in value.split('\n'):
                section.append(Paragraph(escape(paragraph), style) if paragraph else Spacer(1, 8))
            # Keep short sections (such as party name + description) on one page.
            story.extend([KeepTogether(section)] if len(value) <= 300 else section)

        def header(pdf, document):
            pdf.saveState()
            pdf.setFont(BOLD, 15)
            title = plain_text(self.character.name) + ' - ' + _('Additional notes')
            title, rest = _take_line(title, self.page_size[0] - 84, BOLD, 15)
            pdf.drawString(42, self.page_size[1] - 42, title + ('...' if rest else ''))
            pdf.setLineWidth(.6)
            pdf.line(42, self.page_size[1] - 55, self.page_size[0] - 42, self.page_size[1] - 55)
            pdf.setFont(FONT, 8)
            pdf.drawRightString(self.page_size[0] - 42, 24, str(document.page + 1))
            pdf.restoreState()

        document = SimpleDocTemplate(buffer, pagesize=self.page_size, leftMargin=42, rightMargin=42,
                                     topMargin=68, bottomMargin=42)
        document.build(story, onFirstPage=header, onLaterPages=header)
        buffer.seek(0)
        return buffer


def landscape_character_pdf(character, party=None):
    return CharacterSheet(character, party).draw()


def portrait_character_pdf(character, party=None):
    return CharacterSheet(character, party, orientation='portrait').draw()


BAREBONES_TEMPLATE = ASSETS / 'cairn-barebones-a4.pdf'
TRAIT_FIELDS = ('Physique', 'Skin', 'Hair', 'Face', 'Speech', 'Clothing', 'Virtue', 'Vice')
# On the A4 sheet the trait labels ("Physique: ") are pre-filled values of the trait
# fields; values begin where each stamped label ends (x in points, measured from the template).
TRAIT_LABEL_ENDS = {'Physique': 68.1, 'Skin': 49.1, 'Hair': 49.3, 'Face': 151.2, 'Speech': 161.9,
                    'Clothing': 168.5, 'Virtue': 249.4, 'Vice': 240.8, 'Age': 238.7}
# The template draws those labels 5.749pt above each field's bottom edge.
TRAIT_LABEL_BASELINE = 5.749


@lru_cache(maxsize=1)
def _barebones_template():
    """Page size and field name -> (x0, y0, x1, y1) in PDF points, read from the fillable sheet."""
    page = PdfReader(BAREBONES_TEMPLATE).pages[0]
    fields = {}
    for annotation in page.get('/Annots') or []:
        annotation = annotation.get_object()
        name = annotation.get('/T') or annotation.get('/Parent', {}).get('/T')
        if name and '/Rect' in annotation:
            x0, y0, x1, y1 = (float(value) for value in annotation['/Rect'])
            fields[str(name)] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    return (float(page.mediabox.width), float(page.mediabox.height)), fields


def split_traits(text):
    """Recover the eight trait words and the age from a stored trait sentence.

    Characters keep traits as one sentence, but this sheet has a line per trait.
    Traits are matched in table order so words shared by two tables (Oily hair
    and skin) land in the right place. Returns (None, age) when they can't all
    be found, for instance after the player rewrote the sentence.
    """
    from app.lib.data import load_traits
    from app.lib.translations import translate_term
    text = plain_text(text)
    lowered = text.casefold()
    ages = re.findall(r'\d+', text)
    age = ages[-1] if ages else ''
    position, found = 0, {}
    for name, values in load_traits().items():
        best = None
        for value in values:
            label = translate_term(value, 'character trait: ' + name)
            for candidate in {value, label}:
                match = re.compile(r'(?<!\w)' + re.escape(candidate.casefold()) + r'(?!\w)').search(lowered, position)
                if match and (best is None or match.start() < best[0]):
                    best = (match.start(), match.end(), label)
        if best is None:
            return None, age
        found[name] = best[2][:1].upper() + best[2][1:]
        position = best[1]
    return found, age


class BarebonesSheet(CharacterSheet):
    """Cairn Barebones Edition sheet (A4), filled at its form field positions."""

    def __init__(self, character, party=None, export_attributes=True):
        super().__init__(character, party, export_attributes=export_attributes)
        self.orientation = 'barebones'
        self.page_size, self.fields = _barebones_template()
        self.canvas = canvas.Canvas(self.buffer, pagesize=self.page_size)

    def _baseline_top(self, rect, size):
        """Top-left 'top' coordinate placing text vertically centred in a field."""
        x0, y0, x1, y1 = rect
        baseline = y0 + (y1 - y0 - size * 0.7) / 2
        return self.page_size[1] - baseline

    def field_text(self, name, value, size=11, font=FONT, title=None):
        rect = self.fields[name]
        left = max(rect[0], TRAIT_LABEL_ENDS.get(name, 0)) + 2
        if name in TRAIT_LABEL_ENDS:
            top = self.page_size[1] - rect[1] - TRAIT_LABEL_BASELINE
        else:
            top = self._baseline_top(rect, size)
        self.single_line(value, left, top, rect[2] - left - 2, size, font, title)

    def field_number(self, name, value, size=22):
        if value is None or value == '':
            return
        x0, y0, x1, y1 = self.fields[name]
        size = min(size, (y1 - y0) * 0.8)
        self.text(value, (x0 + x1) / 2, self._baseline_top((x0, y0, x1, y1), size), size, BOLD, centered=True)

    def field_lines(self, name, value, title, leading=13):
        """Wrap text into a multi-line field; the rest goes to the appendix."""
        x0, y0, x1, y1 = self.fields[name]
        count = int((y1 - y0 - 4) // leading)
        top = self.page_size[1] - y1 + leading
        self.ruled(title, value, [(x0 + 3, top + i * leading, x1 - x0 - 6) for i in range(count)])

    def draw(self):
        c = self.character
        portrait = _portrait(c)
        if portrait:
            x0, y0, x1, y1 = self.fields['Portrait_af_image']
            self.canvas.drawImage(portrait, x0 + 4, y0 + 4, width=x1 - x0 - 8, height=y1 - y0 - 8,
                                  preserveAspectRatio=True, anchor='c', mask='auto')
        elif c.custom_image and c.image_url:
            self.section(_('Portrait URL'), c.image_url)
        self.field_text('Name', c.name, 13, BOLD, _('Name'))
        self.field_text('Background', _(c.background), 12, title=_('Background'))

        for field, attribute in (('Strength', 'strength'), ('Dexterity', 'dexterity'),
                                 ('Willpower', 'willpower'), ('HitProtection', 'hp')):
            self.field_number(field + '_Maximum', getattr(c, attribute + '_max'))
            if self.export_attributes:
                value = c.hpValue()[0] if attribute == 'hp' else getattr(c, attribute)
                self.field_number(field + '_Current', value)
        if self.export_attributes:
            self.field_number('Armor', c.armorValue(), 26)
            self.field_number('Gold', c.gold, 18)
        if c.deprived:
            self.field_number('Deprived', 'X', 20)
        states = [label for condition, label in ((c.dead, _('Dead')), (c.panicked, _('PANICKED'))) if condition]
        if states:
            self.section(_('Status'), ' / '.join(states))

        traits, age = split_traits(c.traits)
        if traits:
            for name in TRAIT_FIELDS:
                self.field_text(name, traits[name], 9)
        else:
            self.section(_('Traits'), c.traits)
        self.field_text('Age', age, 9)
        self.field_lines('Notes', c.notes, _('Notes'))

        items = json.loads(c.items or '[]')
        main = [it for it in items if it.get('location') == 0]
        petty = [it for it in main if 'petty' in it.get('tags', []) and 'bulky' not in it.get('tags', [])]
        slot = 0
        for item in main:
            if item in petty:
                continue
            slots = 2 if 'bulky' in item.get('tags', []) else 1
            title = _item_title(item)
            if slot + slots <= 10:
                self.field_text(f'Inventory{slot + 1}', title, title=_('Inventory details'))
                if slots == 2:
                    self.field_text(f'Inventory{slot + 2}', _('Occupied by bulky item above'), 9)
            else:
                self.section(_('Additional inventory'), title)
            slot += slots
        petty_lines = [_item_title(it) for it in petty]
        petty_slots = sum(1 for name in self.fields if re.fullmatch(r'Petty\d+', name))
        for index, title in enumerate(petty_lines[:petty_slots], 1):
            self.field_text(f'Petty{index}', title, 10, title=_('Petty Items'))
        if len(petty_lines) > petty_slots:
            self.section(_('Petty Items'), '\n'.join(petty_lines[petty_slots:]))
        self.container_sections(items)

        self.section(_('Description'), c.description)
        self.section(_('Scars'), c.scars)
        self.companion_sections()
        return self.finish(BAREBONES_TEMPLATE, f'{c.name} - Cairn Barebones A4')


def character_sheet(character, party=None, orientation='landscape', export_attributes=True):
    """The printable sheet for a character's edition."""
    if getattr(character, 'edition', None) == 'barebones':
        return BarebonesSheet(character, party, export_attributes=export_attributes)
    return CharacterSheet(character, party, orientation, export_attributes=export_attributes)

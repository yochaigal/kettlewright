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
    name = plain_text(_(item.get('name') or ''))
    return name + (' (' + ', '.join(details) + ')' if details else '')


class CharacterSheet:
    def __init__(self, character, party=None, orientation='landscape'):
        _register_fonts()
        self.orientation = orientation
        self.layout = LAYOUTS[orientation]
        self.page_size = self.layout['page_size']
        self.character = character
        self.party = party
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
        # Mutable numbers are intentionally blank for handwritten play at the table.
        if self.orientation == 'landscape':
            for center in (134, 207, 279, 350):
                self.text(_('current'), center, 277, 7, centered=True)
                self.text(_('max'), center, 327, 7, centered=True)
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

        for container in json.loads(c.containers or '[]'):
            contents = [_item_title(it) for it in items if it.get('location') == container['id']]
            if container['id'] != 0 and contents:
                self.section(container['name'], '\n'.join(contents))
            if container['id'] == 0 and int(container['slots']) != 10:
                self.section(_('Inventory capacity'), _('%(count)s slots', count=container['slots']))
        known_ids = {container['id'] for container in json.loads(c.containers or '[]')} | {0}
        self.section(_('Unassigned items'), '\n'.join(_item_title(it) for it in items if it.get('location') not in known_ids))

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
        self.canvas.save()

        writer = PdfWriter()
        template = PdfReader(ASSETS / f'cairn-2e-{self.orientation}-a4.pdf')
        writer.add_page(template.pages[0])
        writer.pages[0].merge_page(PdfReader(self.buffer).pages[0])
        if self.sections:
            for page in PdfReader(self.appendix()).pages:
                writer.add_page(page)
        writer.add_metadata({'/Title': f'{c.name} - Cairn {self.orientation} A4', '/Author': 'Kettlewright'})
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

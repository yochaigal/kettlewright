from io import BytesIO
import json
import re

import pytest
from PIL import Image
from pypdf import PdfReader

from app.models import Character, Party, User, db


@pytest.fixture(params=['landscape', 'portrait'])
def orientation(request):
    return request.param


@pytest.fixture
def pdf_character(app_with_babel):
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='printer'))
        character = Character(owner=1, owner_username='printer', name='Лейф', url_name='hero',
                              background='Fungal Forager', image_url='default-portrait.webp',
                              strength=10, strength_max=10, dexterity=8, dexterity_max=8,
                              willpower=9, willpower_max=9, hp=3, hp_max=3, gold=11,
                              items='[]', containers='[{"id":0,"name":"Main","slots":10}]')
        db.session.add(character)
        db.session.commit()
        yield app_with_babel, character


PATH = '/users/printer/characters/hero/print/{orientation}.pdf'


def rendered(app, orientation):
    response = app.test_client().get(PATH.format(orientation=orientation))
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    return response, PdfReader(BytesIO(response.data))


def contents(reader):
    return '\n'.join(page.extract_text() for page in reader.pages)


def test_pdf_route_embeds_fonts_and_builtin_portrait_without_mutating_character(pdf_character, orientation):
    app, character = pdf_character
    original = (character.name, character.items, character.containers, character.hp)
    response, reader = rendered(app, orientation)
    assert len(reader.pages) == 1
    assert 'Лейф' in contents(reader)
    assert 'inline;' in response.headers['Content-Disposition']
    assert f'hero-{orientation}-a4.pdf' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'private, no-store'
    assert len(reader.pages[0].images) >= 2  # The artwork and portrait.
    assert (character.name, character.items, character.containers, character.hp) == original
    assert app.test_client().get(PATH.format(orientation=orientation).replace('/hero/', '/missing/')).status_code == 404


def test_pdf_leaves_current_max_gold_and_armor_blank_for_handwriting(pdf_character, orientation):
    app, character = pdf_character
    character.gold = 31415
    character.items = json.dumps([dict(name='Leather armor', tags=['2 Armor'], location=0)])
    db.session.commit()
    _, reader = rendered(app, orientation)
    text = reader.pages[0].extract_text()
    if orientation == 'landscape':
        assert text.count('current') == 4 and text.count('max') == 4
    # Template labels are raster artwork; generated standalone numeric values
    # would indicate that a stat, Gold or Armor field was accidentally filled.
    assert not re.findall(r'^\s*\d+\s*$', text, flags=re.M)
    assert '31415' not in text
    assert 'Leather armor (2 Armor)' in text
    assert character.gold == 31415 and character.strength == 10


def test_long_sections_paginate_and_keep_unicode_and_html_text(pdf_character, orientation):
    app, character = pdf_character
    character.name = 'Очень длинное имя ' * 10
    character.traits = 'Наблюдательный и осторожный. ' * 25
    character.description = '<p>Описание персонажа.</p><p>Вторая строка.</p>'
    character.notes = ('Запись о путешествии ' * 60 + '\n') * 20
    character.bonds = 'Family bond. ' * 80
    character.omens = 'An omen. ' * 90
    character.scars = 'Scar with <b>bold text</b>.'
    db.session.commit()
    _, reader = rendered(app, orientation)
    text = contents(reader)
    assert len(reader.pages) > 2
    appendix = '\n'.join(page.extract_text() for page in reader.pages[1:])
    assert appendix.count('путешествии') == character.notes.count('путешествии')
    assert 'Описание персонажа.' in text and 'Вторая строка.' in text
    assert 'Scar with bold text.' in text
    assert '<p>' not in text and '<b>' not in text
    normalize = lambda value: re.sub(r'\s+', ' ', value).strip()
    assert normalize(character.name) in normalize(text)
    assert normalize(character.traits) in normalize(text)
    size = (841.89, 595.276) if orientation == 'landscape' else (595.321191, 841.921684)
    for page in reader.pages:
        assert float(page.mediabox.width) == pytest.approx(size[0])
        assert float(page.mediabox.height) == pytest.approx(size[1])


def test_inventory_retains_overflow_petty_bulky_and_additional_containers(pdf_character, orientation):
    app, character = pdf_character
    items = [dict(name='Bulky shield', tags=['bulky'], location=0),
             dict(name='Fatigue', tags=[], location=0)]
    items += [dict(name=f'Main-item-{i}', tags=[], location=0) for i in range(12)]
    items += [dict(name=f'Petty-item-{i}', tags=['petty'], location=0) for i in range(12)]
    items += [dict(name='Remote book', tags=[], location=1),
              dict(name='Unassigned book', tags=[], location=99)]
    character.items = json.dumps(items)
    character.containers = '[{"id":0,"name":"Main","slots":10},{"id":1,"name":"Chest","slots":20}]'
    character.panicked = True
    character.dead = True
    db.session.commit()
    _, reader = rendered(app, orientation)
    text = contents(reader)
    for item in items:
        assert item['name'] in text
    first = reader.pages[0].extract_text()
    assert 'Occupied by bulky item above' in first
    assert 'Main-item-6' in first and 'Main-item-7' not in first
    assert 'PANICKED' in first and 'Dead' in first
    assert 'Chest' in text and 'Unassigned items' in text


def test_portrait_upload_is_embedded_and_external_url_is_preserved(pdf_character, tmp_path, orientation):
    app, character = pdf_character
    app.config['PORTRAIT_UPLOAD_FOLDER'] = str(tmp_path)
    filename = 'a' * 64 + '.webp'
    Image.new('RGB', (256, 256), 'red').save(tmp_path / filename, 'WEBP')
    character.custom_image = True
    character.image_url = '/portraits/' + filename
    db.session.commit()
    _, reader = rendered(app, orientation)
    assert len(reader.pages) == 1
    assert len(reader.pages[0].images) >= 2
    character.image_url = 'http://127.0.0.1:9/private-portrait.png'
    db.session.commit()
    _, reader = rendered(app, orientation)
    assert character.image_url in contents(reader)
    assert len(reader.pages[0].images) == 1


def test_missing_portrait_and_extreme_unbroken_text_do_not_break_pdf(pdf_character, orientation):
    app, character = pdf_character
    character.custom_image = True
    character.image_url = '/portraits/' + 'b' * 64 + '.webp'
    character.notes = 'Z' * 4000
    db.session.commit()
    _, reader = rendered(app, orientation)
    # The full note is kept on additional pages; first-page preview may repeat its prefix.
    appendix = ''.join(page.extract_text() for page in reader.pages[1:])
    assert appendix.count('Z') == len(character.notes)


def test_character_view_keeps_html_print_and_adds_pdf_option(pdf_character, orientation):
    app, _character = pdf_character
    response = app.test_client().get('/users/printer/characters/hero/')
    assert response.status_code == 200
    assert b'/users/printer/characters/hero/print/"' in response.data
    assert PATH.format(orientation=orientation).encode() in response.data

"""Cairn's web parts: how a Cairn character is created (2e, Barebones and the quick generator), and its PDF sheet.

Unlike the rest of system/cairn, this plug-in uses the app (Flask, the models, the forms): kettlewright.web calls
init_app(app) when the app starts, because Cairn's GameSystem names this module (web = 'system.cairn.web'). The app
reaches it only through kettlewright.web.plugin(), never by importing system.cairn, so another system can
bring its own.

    charcreo.py             2e creation: background, its tables, attributes, traits, bonds, omen, gear
    charcreo_barebones.py   Barebones creation: the d100 tables and a gear package
    barebones.py            the Barebones tables and the characters they make
    char_utils.py           the quick generator's characters (Tools, /api/v1/characters/random) and their text
    generator.py            the quick generator's pages
    character_pdf.py        the PDF sheets, drawn on Cairn's own sheets (pdf_templates/)
"""

def init_app(app):
    from system.cairn.web.char_utils import traits_sentence
    from system.cairn.web.charcreo import character_create
    from system.cairn.web.charcreo_barebones import charcreo_barebones
    from system.cairn.web.generator import generator
    for blueprint in (generator, character_create, charcreo_barebones):
        app.register_blueprint(blueprint)
    # A Cairn character's traits as a sentence, on its sheet.
    app.add_template_global(traits_sentence)


def creation_page(method='2e'):
    """The page that creates a character this way: '2e' or 'barebones'."""
    if method == 'barebones':
        from system.cairn.web.charcreo_barebones import creation_page as page
    else:
        from system.cairn.web.charcreo import creation_page as page
    return page()


def random_character(background=None):
    """A random character for the public API: (generated, JSON). background: a background's name, or 'barebones'
    / 'barebones:<package>' for a Barebones one. KeyError for an unknown background or package."""
    if background == 'barebones' or (background or '').startswith('barebones:'):
        from system.cairn.web.barebones import gear_packages, generate_character
        package = background.partition(':')[2] or None
        if package and package not in gear_packages():
            raise KeyError(package)
        return generate_character(package)
    from app.lib.data import load_backgrounds
    from system.cairn.web.char_utils import generate_character
    if background and background.casefold() not in {name.casefold() for name in load_backgrounds()}:
        raise KeyError(background)
    return generate_character(background or None)


def gear_packages():
    from system.cairn.web.barebones import gear_packages as packages
    return packages()


def barebones_data():
    """The Barebones tables, with the background table this request rolls on (a party's, or the official d100)."""
    from system.cairn.web.barebones import barebones_data as data
    return data()


def random_name(background=None):
    from system.cairn.web.char_utils import random_name as name
    return name(background)


def character_sheet(character, party, orientation, export_attributes=True):
    """The character's PDF sheet (a reportlab drawing; .draw() gives the bytes)."""
    from system.cairn.web.character_pdf import character_sheet as sheet
    return sheet(character, party, orientation, export_attributes=export_attributes)

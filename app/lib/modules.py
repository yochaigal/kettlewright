"""Modules: the content a campaign is built from.

A module is a package of parts: maps, articles and backgrounds for now (items,
missions and more later). Each part has its own section on the module page, its
own folder in a module archive and its own Markdown type (MODULE_PARTS). A Warden
creates a module in a campaign (blank or randomly generated), adds one from the
Modules Marketplace (bundled in app/modules/<slug>/), or uploads one; any module
can be edited and exported in the same all-Markdown format (docs/campaigns.md).
"""
import io
import zipfile
from functools import lru_cache
from pathlib import Path

from flask_babel import lazy_gettext as _l

from app.lib.campaign_import import import_preview, preview_archive
from app.models import db, Module

BUNDLES = Path(__file__).resolve().parent.parent / 'modules'

# The parts a module packs, in the order pages show them. To add a part (items, missions...):
# give it a folder and a Markdown type here, a section on the module page, and its import/export.
MODULE_PARTS = (
    {'key': 'maps', 'label': _l('Maps'), 'one': _l('map'), 'many': _l('maps'), 'icon': 'fa-map', 'folder': 'maps', 'type': 'Map'},
    {'key': 'backgrounds', 'label': _l('Backgrounds'), 'one': _l('background'), 'many': _l('backgrounds'),
     'icon': 'fa-user-gear', 'folder': 'backgrounds', 'type': 'Background'},
    {'key': 'articles', 'label': _l('Articles'), 'one': _l('article'), 'many': _l('articles'), 'icon': 'fa-file-lines',
     'folder': 'articles', 'type': None},
)
SOURCE = 'https://cairnrpg.com/adventures/first-party/{}/'

# The Modules Marketplace. Each title must equal the `title:` in the bundle's campaign.md (a test checks this).
MODULES = {
    'cas-1': {'title': 'CAS-1: Trouble in Twin Lakes', 'author': 'Yochai Gal · Cairn Press', 'license': 'CC-BY-SA 4.0',
              'description': _l('Two central mysteries for the party to solve, with NPCs, antagonists and '
                                'locations to explore. Suits new and veteran players.')},
    'cas-2': {'title': 'CAS-2: Rise of the Blood Olms', 'author': 'Yochai Gal · Cairn Press', 'license': 'CC-BY-SA 4.0',
              'description': _l('A deadly starting adventure for new and experienced Wardens. Critical thinking '
                                'and careful exploration keep characters alive.')},
    'cas-3': {'title': 'CAS-3: The Feast of Tegny Wood', 'author': 'Yochai Gal · Cairn Press', 'license': 'CC-BY-SA 4.0',
              'description': _l('Disease, duty and decay in a haunted corner of Vald, where an alchemist\'s '
                                'failed experiment is festering in Tegny Wood.')},
    'cas-4': {'title': 'CAS-4: The Forgetting of Lockwood Manor', 'author': 'Yochai Gal · Cairn Press', 'license': 'CC-BY-SA 4.0',
              'description': _l('A wealthy family\'s estate fell silent decades ago, and a waterborne illness '
                                'now fills victims\' lungs with moss.')},
}


def bundle_archive(path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(path.rglob('*')):
            if file.is_file() and file.suffix.lower() in ('.md', '.json', '.excalidraw'):
                archive.write(file, file.relative_to(path).as_posix())
    return stream.getvalue()


def preview_counts(payload):
    """What a staged module holds, part by part (a map that is only a map is not an article)."""
    rows = [row for row in payload['rows'] if row['category'] != 'campaign']
    return {'maps': sum(1 for row in rows if row.get('map') or row['category'] == 'map'),
            'articles': sum(1 for row in rows if row['category'] not in ('map', 'map_note')),
            'backgrounds': len(payload.get('backgrounds') or {})}


@lru_cache(maxsize=None)
def bundle_contents(slug):
    """What the Marketplace says a module holds, part by part (counted once)."""
    return preview_counts(preview_archive(bundle_archive(BUNDLES / slug), None))


@lru_cache(maxsize=None)
def bundle_cover(slug):
    """The module's cover: the first image in its bundled campaign.md (read once)."""
    from app.lib.campaign_wiki import first_image
    return first_image((BUNDLES / slug / 'campaign.md').read_text(encoding='utf-8'))


def campaign_copy(campaign, slug):
    """The campaign's copy of a bundled module (older ones: a module named after it), or None."""
    return next((module for module in campaign.modules
                 if module.slug == slug or module.title == MODULES[slug]['title']), None)


def marketplace(campaign):
    """One card per bundled module, with the campaign's copy when it already has it."""
    return [{'slug': slug, 'url': SOURCE.format(slug), 'cover': bundle_cover(slug), 'contents': bundle_contents(slug),
             'module': campaign_copy(campaign, slug), **info} for slug, info in MODULES.items()]


def create_module(campaign, title):
    """A new, empty module in the campaign. The caller commits."""
    module = Module(campaign=campaign, title=title)
    db.session.add(module)
    return module


def default_module(campaign):
    """Where an article made without choosing a module goes: the campaign's first module, or a new one."""
    return campaign.modules[0] if campaign.modules else create_module(campaign, campaign.name)


def add_module(campaign, slug):
    """Add a bundled module to the campaign. Returns the module (the existing one if it was already added).

    KeyError for an unknown slug. The caller commits, or rolls back if this raises."""
    MODULES[slug]  # KeyError for an unknown slug.
    existing = campaign_copy(campaign, slug)
    if existing is not None:
        return existing
    payload = preview_archive(bundle_archive(BUNDLES / slug), campaign.owner_id)
    if payload['errors']:
        raise ValueError('; '.join(payload['errors'][:3]))
    import_preview(payload, campaign.owner_id, into=campaign, slug=slug)
    db.session.flush()
    return next(module for module in campaign.modules if module.slug == slug)


def module_counts(module):
    """What a module holds, part by part: its maps, its articles (not the maps) and its backgrounds."""
    from app.lib.campaigns import map_only
    entries = list(module.entries)
    return {'maps': sum(1 for entry in entries if entry.pointcrawl),
            'articles': sum(1 for entry in entries if not map_only(entry) and entry.category != 'map_note'),
            'backgrounds': len(module.backgrounds or {})}


def part_badges(counts):
    """["3 maps", "12 articles"]: the parts a module holds, in MODULE_PARTS order, skipping empty ones."""
    return [f"{counts[part['key']]} {part['one'] if counts[part['key']] == 1 else part['many']}"
            for part in MODULE_PARTS if counts.get(part['key'])]

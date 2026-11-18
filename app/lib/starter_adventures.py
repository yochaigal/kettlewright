"""Offer the bundled Cairn starter adventures, imported on request through the archive importer."""
import io
import zipfile
from functools import lru_cache
from pathlib import Path

from flask_babel import lazy_gettext as _l

from app.lib.campaign_import import import_preview, preview_archive
from app.models import db, Campaign

BUNDLES = Path(__file__).resolve().parent.parent / 'starter_adventures'
SOURCE = 'https://cairnrpg.com/adventures/first-party/{}/'

# Each title must equal the `title:` in the bundle's campaign.md (a test checks this).
STARTERS = {
    'cas-1': {'title': 'CAS-1: Trouble in Twin Lakes',
              'description': _l('Two central mysteries for the party to solve, with NPCs, antagonists and '
                                'locations to explore. Suits new and veteran players.')},
    'cas-2': {'title': 'CAS-2: Rise of the Blood Olms',
              'description': _l('A deadly starting adventure for new and experienced Wardens. Critical thinking '
                                'and careful exploration keep characters alive.')},
    'cas-3': {'title': 'CAS-3: The Feast of Tegny Wood',
              'description': _l('Disease, duty and decay in a haunted corner of Vald, where an alchemist\'s '
                                'failed experiment is festering in Tegny Wood.')},
    'cas-4': {'title': 'CAS-4: The Forgetting of Lockwood Manor',
              'description': _l('A wealthy family\'s estate fell silent decades ago, and a waterborne illness '
                                'now fills victims\' lungs with moss.')},
}


def bundle_archive(path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(path.rglob('*.md')):
            archive.write(file, file.relative_to(path).as_posix())
    return stream.getvalue()


@lru_cache(maxsize=None)
def bundle_cover(slug):
    """The adventure's cover: the first image in its bundled campaign.md (read once)."""
    from app.lib.campaign_wiki import first_image
    return first_image((BUNDLES / slug / 'campaign.md').read_text(encoding='utf-8'))


def starter_cards(owned):
    """One card per bundle; campaign is the user's Campaign of that name, if they have one."""
    return [{'slug': slug, 'url': SOURCE.format(slug), 'campaign': owned.get(info['title']), 'cover': bundle_cover(slug), **info}
            for slug, info in STARTERS.items()]


def add_starter_adventure(user_id, slug):
    """Import one bundle unless the user already has a campaign of that name; KeyError for an unknown slug.

    Importing again would create a second campaign of the same name, so owned ones are skipped. The caller commits,
    or rolls back if this raises.
    """
    title = STARTERS[slug]['title']
    if db.session.query(Campaign.id).filter_by(owner_id=user_id, name=title).first():
        return
    payload = preview_archive(bundle_archive(BUNDLES / slug), user_id)
    if payload['errors']:
        raise ValueError('; '.join(payload['errors'][:3]))
    import_preview(payload, user_id)

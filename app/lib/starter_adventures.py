"""Give a user the bundled Cairn starter adventures through the archive importer."""
import io
import re
import zipfile
from pathlib import Path

from flask import current_app

from app.lib.campaign_import import import_preview, preview_archive
from app.models import db, Campaign

BUNDLES = Path(__file__).resolve().parent.parent / 'starter_adventures'


def bundle_dirs():
    return sorted(path for path in BUNDLES.glob('cas-*') if (path / 'campaign.md').is_file())


def bundle_title(path):
    text = (path / 'campaign.md').read_text(encoding='utf-8')
    return re.search(r'^title:\s*"(.*)"\s*$', text, re.M).group(1)


def bundle_archive(path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(path.rglob('*.md')):
            archive.write(file, file.relative_to(path).as_posix())
    return stream.getvalue()


def seed_starter_adventures(user_id, dry_run=False):
    """Import every starter campaign the user does not already have.

    The importer merges into a same-named campaign, so owned ones are skipped.
    A failing bundle is rolled back and logged; the caller owns the commit.
    """
    owned = {name for (name,) in db.session.query(Campaign.name).filter_by(owner_id=user_id)}
    missing = [path for path in bundle_dirs() if bundle_title(path) not in owned]
    if dry_run:
        return len(missing)
    added = 0
    for path in missing:
        try:
            with db.session.begin_nested():
                payload = preview_archive(bundle_archive(path), user_id)
                if payload['errors']:
                    raise ValueError('; '.join(payload['errors'][:3]))
                import_preview(payload, user_id)
            added += 1
        except Exception:
            current_app.logger.exception('Starter adventure %s failed for user %s', path.name, user_id)
    return added

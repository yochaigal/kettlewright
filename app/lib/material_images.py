"""Description images in persistent storage, with the same access as their text."""
import base64
import re
from pathlib import Path
from uuid import uuid4

from flask import abort, current_app
from flask_login import current_user
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import db, ContentEntry, PartyPresentation
from app.lib.portraits import portrait_directory

LOCAL_IMAGE = re.compile(r'/material-images/([1-9][0-9]*)/([0-9a-f]{32}\.webp)')


def image_directory():
    return Path(current_app.config.get('MATERIAL_IMAGE_UPLOAD_FOLDER',
                portrait_directory().parent / 'material-images'))


def image_references(body):
    return {match.group(0) for match in LOCAL_IMAGE.finditer(body or '')}


def validate_local_image(url):
    match = LOCAL_IMAGE.fullmatch(url)
    if not match or not current_user.is_authenticated or int(match[1]) != current_user.id:
        abort(400, 'Choose an image belonging to your materials.')
    if not (image_directory() / match[1] / match[2]).is_file():
        abort(400, 'This image is no longer available.')


def externalize_images(body, owner_id, candidates):
    from app.lib.rich_content import RICH_PREFIX, optimize_image
    if not body:
        return body
    replacements = {}

    def replace(match):
        data_url = match[1]
        if data_url not in replacements:
            optimized = optimize_image(data_url)
            filename = uuid4().hex + '.webp'
            url = f'/material-images/{owner_id}/{filename}'
            candidates.add(url)  # Also clean up on a failed write/transaction.
            folder = image_directory() / str(owner_id)
            folder.mkdir(parents=True, exist_ok=True)
            with (folder / filename).open('xb') as output:
                output.write(base64.b64decode(optimized.split(',', 1)[1]))
            replacements[data_url] = url
        return replacements[data_url]

    return re.sub(r'(data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+)', replace, body)


@event.listens_for(Session, 'before_flush')
def store_description_images(session, flush_context, instances):
    candidates = session.info.setdefault('material_image_candidates', set())
    for row in set(session.new) | set(session.dirty) | set(session.deleted):
        if not isinstance(row, (ContentEntry, PartyPresentation)):
            continue
        history = inspect(row).attrs.body.history
        for previous in history.deleted:
            candidates.update(image_references(previous))
        if row in session.deleted:
            candidates.update(image_references(row.body))
        elif row in session.new or history.has_changes():
            owner_id = row.owner_id if isinstance(row, ContentEntry) else row.entry.owner_id
            row.body = externalize_images(row.body, owner_id, candidates)


def cleanup_images():
    """Call after the transaction; retain files used by any original or saved version."""
    candidates = db.session.info.pop('material_image_candidates', set())
    for url in candidates:
        match = LOCAL_IMAGE.fullmatch(url)
        if not match:
            continue
        # Match filename as well as URL to retain absolute links in imported text.
        filename = match[2]
        if (ContentEntry.query.filter(ContentEntry.body.contains(filename)).first() is not None
                or PartyPresentation.query.filter(PartyPresentation.body.contains(filename)).first() is not None):
            continue
        try:
            (image_directory() / match[1] / filename).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning('Could not remove unused material image %s', url, exc_info=True)

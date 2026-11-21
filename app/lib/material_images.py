"""Description images in persistent storage, with the same access as their text."""
import base64
import re
from pathlib import Path
from uuid import uuid4

from flask import abort, current_app
from flask_login import current_user
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import db, Campaign, ContentEntry, Party, PartyPresentation
from app.lib.portraits import portrait_directory

LOCAL_IMAGE = re.compile(r'/material-images/([1-9][0-9]*)/([0-9a-f]{32}\.webp)')


def article_image(entry):
    """An article's picture for its card and cover: its own image (#476), else the first one in its text."""
    from app.lib.campaign_wiki import first_image
    return entry.image or first_image(entry.body) if entry is not None else None


def image_value(value):
    """The Image field of the article form: empty (none), an upload (a data URL, stored on save),
    an image URL, or the stored picture it already has."""
    from app.lib.rich_content import optimize_image
    value = (value or '').strip()
    if not value:
        return ''
    if len(value) > 4 * 1024 * 1024:
        abort(400, 'Optimize images before saving (maximum input: 2 MB each).')
    value = optimize_image(value)  # Rejects anything that is not an image.
    if not value.startswith('data:') and len(value) > 2000:
        abort(400, 'This image address is too long.')
    return value


def image_directory():
    return Path(current_app.config.get('MATERIAL_IMAGE_UPLOAD_FOLDER',
                portrait_directory().parent / 'material-images'))


def image_references(body):
    return {match.group(0) for match in LOCAL_IMAGE.finditer(body or '')}


def validate_local_image(url):
    from flask import g
    match = LOCAL_IMAGE.fullmatch(url)
    # A player editing a party note keeps the pictures already in it (g.kept_local_images), but adds none of the Warden's.
    kept = url in g.get('kept_local_images', ())
    if not match or not current_user.is_authenticated or (int(match[1]) != current_user.id and not kept):
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


# Fields that hold stored pictures: texts, and the own images of articles, campaigns and parties (#476).
IMAGE_FIELDS = {ContentEntry: ('body', 'image'), PartyPresentation: ('body',), Campaign: ('image',), Party: ('image',)}


def image_owner(row):
    if isinstance(row, PartyPresentation):
        return row.entry.owner_id
    return row.owner if isinstance(row, Party) else row.owner_id


@event.listens_for(Session, 'before_flush')
def store_description_images(session, flush_context, instances):
    candidates = session.info.setdefault('material_image_candidates', set())
    for row in set(session.new) | set(session.dirty) | set(session.deleted):
        fields = IMAGE_FIELDS.get(type(row))
        if fields is None:
            continue
        owner_id = None
        for field in fields:
            history = inspect(row).attrs[field].history
            for previous in history.deleted:
                candidates.update(image_references(previous))
            if row in session.deleted:
                candidates.update(image_references(getattr(row, field)))
            elif row in session.new or history.has_changes():
                owner_id = owner_id or image_owner(row)
                setattr(row, field, externalize_images(getattr(row, field), owner_id, candidates))


def image_in_use(filename):
    """Whether any text, or any article's, campaign's or party's own image (#476), still shows this stored picture."""
    return any(model.query.filter(getattr(model, field).contains(filename)).first() is not None
               for model, fields in IMAGE_FIELDS.items() for field in fields)


def cleanup_images():
    """Call after the transaction; retain files used by any original or saved version."""
    candidates = db.session.info.pop('material_image_candidates', set())
    for url in candidates:
        match = LOCAL_IMAGE.fullmatch(url)
        if not match:
            continue
        # Match filename as well as URL to retain absolute links in imported text.
        filename = match[2]
        if image_in_use(filename):
            continue
        try:
            (image_directory() / match[1] / filename).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning('Could not remove unused material image %s', url, exc_info=True)


def remove_owner_images(owner_id):
    """After an account is deleted (#455): remove its description images that nothing still shows."""
    folder = image_directory() / str(int(owner_id))
    if not folder.is_dir():
        return
    for path in folder.glob('*.webp'):
        if image_in_use(path.name):
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning('Could not remove image %s of a deleted account', path.name, exc_info=True)
    try:
        folder.rmdir()
    except OSError:
        pass  # Still holds an image that other content shows.

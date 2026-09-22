"""Validate and normalize uploaded portraits into persistent instance storage."""
import hashlib
import re
from io import BytesIO
from pathlib import Path

from flask import current_app, url_for

from app.models import Character

MAX_PORTRAIT_BYTES = 2 * 1024 * 1024


def portrait_directory():
    return Path(current_app.config.get('PORTRAIT_UPLOAD_FOLDER',
                Path(current_app.instance_path) / 'portraits'))


def save_portrait(upload):
    # Serving existing uploads and cleaning up files do not need the image codec.
    from PIL import Image, ImageOps, UnidentifiedImageError

    raw = upload.stream.read(MAX_PORTRAIT_BYTES + 1)
    if len(raw) > MAX_PORTRAIT_BYTES:
        raise ValueError('Choose an image smaller than 2 MB.')
    try:
        with Image.open(BytesIO(raw), formats=['PNG', 'JPEG', 'WEBP', 'GIF']) as image:
            if image.width > 4096 or image.height > 4096:
                raise ValueError('Image dimensions must not exceed 4096 × 4096 pixels.')
            image.load()
            image = ImageOps.exif_transpose(image).convert('RGBA')
            portrait = ImageOps.fit(image, (256, 256), method=Image.Resampling.LANCZOS)
            portrait.info.clear()
            output = BytesIO()
            # Re-encoding discards active content, metadata and animation.
            portrait.save(output, format='WEBP', quality=90)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError('Choose a valid PNG, JPEG, WebP or GIF image.') from error
    content = output.getvalue()
    filename = hashlib.sha256(content).hexdigest() + '.webp'
    folder = portrait_directory()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    # Identical portraits share an immutable filename; never trust upload names.
    try:
        with path.open('xb') as file:
            file.write(content)
    except FileExistsError:
        pass
    return url_for('character_edit.uploaded_portrait', filename=filename)


def delete_unreferenced_portrait(previous_url):
    """Remove a replaced local upload only after its last character reference is gone."""
    match = re.fullmatch(r'/portraits/([0-9a-f]{64}\.webp)', previous_url or '')
    if not match:
        return
    filename = match.group(1)
    # Also retain references written as absolute or URL-encoded links by imports.
    if Character.query.filter(Character.image_url.contains(filename)).first() is not None:
        return
    try:
        (portrait_directory() / filename).unlink(missing_ok=True)
    except OSError:
        # The new portrait is already committed; failed cleanup must not undo it.
        current_app.logger.warning('Could not remove replaced portrait %s', filename, exc_info=True)

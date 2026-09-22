"""Validate and normalize uploaded portraits into persistent instance storage."""
import hashlib
from io import BytesIO
from pathlib import Path

from flask import current_app, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PORTRAIT_BYTES = 2 * 1024 * 1024


def portrait_directory():
    return Path(current_app.config.get('PORTRAIT_UPLOAD_FOLDER',
                Path(current_app.instance_path) / 'portraits'))


def save_portrait(upload):
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

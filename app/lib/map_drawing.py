"""Validate the independent, private Excalidraw drawing (never graph cards)."""
import base64
import binascii
import copy
import io
import json
import math

from flask import abort
from PIL import Image

EMPTY_DRAWING = {'elements': [], 'files': {}}
MAX_DRAWING_BYTES = 12 * 1024 * 1024
DRAWING_TYPES = {'rectangle', 'ellipse', 'diamond', 'text', 'line', 'arrow', 'freedraw', 'image'}


def validate_drawing(value, *, allow_frames=False):
    if value is None:
        return copy.deepcopy(EMPTY_DRAWING)
    if not isinstance(value, dict):
        abort(400, 'Invalid drawing.')
    try:
        if len(json.dumps(value, allow_nan=False).encode()) > MAX_DRAWING_BYTES:
            abort(400, 'Drawing exceeds 12 MB.')
    except (ValueError, TypeError, RecursionError):
        abort(400, 'Invalid drawing.')
    elements, files = value.get('elements'), value.get('files')
    if not isinstance(elements, list) or len(elements) > 2000 or not isinstance(files, dict):
        abort(400, 'A drawing supports up to 2000 elements.')
    result, ids, used_files = [], set(), set()
    for original in elements:
        if not isinstance(original, dict) or original.get('type') not in (DRAWING_TYPES | ({'frame'} if allow_frames else set())):
            abort(400, 'Unsupported drawing element.')
        element = copy.deepcopy(original)
        key = element.get('id')
        if not isinstance(key, str) or not key or len(key) > 200 or key.startswith('kw-') or key in ids:
            abort(400, 'Invalid drawing element ID.')
        ids.add(key)
        for field in ('x', 'y', 'width', 'height', 'angle'):
            number = element.get(field, 0)
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or abs(number) > 1000000:
                abort(400, 'Invalid drawing coordinates.')
        if element.get('width', 0) < 0 or element.get('height', 0) < 0:
            abort(400, 'Invalid drawing dimensions.')
        if element['type'] == 'text':
            for field in ('text', 'originalText'):
                text = element.get(field, '')
                if not isinstance(text, str) or len(text) > 50000:
                    abort(400, 'Invalid drawing text.')
        if element['type'] in ('line', 'arrow', 'freedraw'):
            points = element.get('points')
            if not isinstance(points, list) or len(points) > 50000:
                abort(400, 'Invalid drawing points.')
            for point in points:
                # Legacy library freehand points may include a pressure value.
                # Validate it before retaining only the scene's x/y coordinates.
                if element['type'] == 'freedraw' and isinstance(point, list) and len(point) == 3:
                    pressure = point[2]
                    if (isinstance(pressure, bool) or not isinstance(pressure, (int, float))
                            or not math.isfinite(pressure) or not 0 <= pressure <= 1):
                        abort(400, 'Invalid drawing points.')
                    point.pop()
                if not isinstance(point, list) or len(point) != 2 or any(
                    isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or abs(n) > 1000000 for n in point
                ):
                    abort(400, 'Invalid drawing points.')
        # Drawings carry no card metadata, external embeds or executable links.
        element.pop('customData', None)
        element['link'] = None
        if not allow_frames:
            element['frameId'] = None
        if element.get('isDeleted'):
            continue
        if element['type'] == 'image':
            file_id = element.get('fileId')
            if not isinstance(file_id, str) or file_id not in files:
                abort(400, 'Missing drawing image.')
            used_files.add(file_id)
        result.append(element)
    retained_ids = {element['id'] for element in result}
    frame_ids = {element['id'] for element in result if element['type'] == 'frame'}
    for element in result:
        if allow_frames and element.get('frameId') not in frame_ids:
            element['frameId'] = None
        for field in ('startBinding', 'endBinding'):
            binding = element.get(field)
            if binding is not None and (not isinstance(binding, dict) or binding.get('elementId') not in retained_ids):
                element[field] = None
        bindings = element.get('boundElements')
        if bindings is not None:
            if not isinstance(bindings, list):
                abort(400, 'Invalid drawing bindings.')
            element['boundElements'] = [binding for binding in bindings if isinstance(binding, dict) and binding.get('id') in retained_ids]
        if element.get('containerId') not in retained_ids:
            element['containerId'] = None
    clean_files = {}
    for file_id in used_files:
        file = files[file_id]
        if not isinstance(file, dict):
            abort(400, 'Invalid drawing image.')
        mime = file.get('mimeType')
        formats = {'image/png': 'PNG', 'image/jpeg': 'JPEG', 'image/webp': 'WEBP', 'image/gif': 'GIF'}
        url = file.get('dataURL')
        prefix = f'data:{mime};base64,'
        if mime not in formats or not isinstance(url, str) or not url.startswith(prefix):
            abort(400, 'Use PNG, JPEG, WebP or GIF images.')
        try:
            content = base64.b64decode(url[len(prefix):], validate=True)
            with Image.open(io.BytesIO(content)) as image:
                if image.format != formats[mime] or image.width * image.height > 25000000:
                    abort(400, 'Invalid or oversized drawing image.')
                image.verify()
        except (ValueError, OSError, binascii.Error, Image.DecompressionBombError):
            abort(400, 'Invalid drawing image.')
        clean_files[file_id] = {'id': file_id, 'mimeType': mime, 'dataURL': url, 'created': 0}
    return {'elements': result, 'files': clean_files}

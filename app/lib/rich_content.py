"""Sanitized Markdown throughout the app, including legacy rich descriptions."""
from html import escape
from html.parser import HTMLParser
import base64
import binascii
import io
import re
from urllib.parse import urlsplit

import bleach
import mistune
from flask import abort
from markupsafe import Markup
from PIL import Image, ImageOps

from app.lib.material_images import LOCAL_IMAGE, validate_local_image

RICH_PREFIX = '<!--kw-rich-text:1-->'
TAGS = {'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'h2', 'h3',
        'blockquote', 'ol', 'ul', 'li', 'a', 'img', 'del', 'h1', 'h4', 'h5', 'h6',
        'pre', 'code', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'}
markdown = mistune.create_markdown(escape=False, hard_wrap=True,
    plugins=['strikethrough', 'table', 'url'])
MAX_CONTENT_BYTES = 5 * 1024 * 1024
IMAGE_URL = re.compile(r'^data:image/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$')

MAX_IMAGE_BYTES = 500 * 1024
MAX_IMAGE_SIDE = 1600


def remote_image_url(value):
    if not isinstance(value, str) or re.search(r'[\s\x00-\x1f\x7f\\]', value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme in {'http', 'https'} and bool(url.hostname)
                and url.username is None and url.password is None)
    except ValueError:
        return False


def optimize_image(url):
    """Normalize uploads; never fetch external URLs. Already compact WebP is stable."""
    if LOCAL_IMAGE.fullmatch(url):
        validate_local_image(url)
        return url
    if remote_image_url(url):
        return url
    if not IMAGE_URL.fullmatch(url):
        abort(400, 'Use an HTTP(S) image URL or a PNG, JPEG, WebP or GIF upload.')
    mime, data = url.split(';base64,', 1)
    try:
        content = base64.b64decode(data, validate=True)
        if len(content) > 2 * 1024 * 1024:
            abort(400, 'Optimize images before saving (maximum input: 2 MB each).')
        with Image.open(io.BytesIO(content)) as source:
            if source.format.lower() != mime.split('/')[-1] or source.width * source.height > 25000000:
                abort(400, 'Invalid or oversized image.')
            source.load()
            if (source.format == 'WEBP' and not getattr(source, 'is_animated', False)
                    and max(source.size) <= MAX_IMAGE_SIDE and len(content) <= MAX_IMAGE_BYTES
                    and not any(source.info.get(key) for key in ('exif', 'xmp', 'icc_profile'))):
                return url
            image = ImageOps.exif_transpose(source).convert('RGBA')
            image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
            while True:
                for quality in (82, 72, 62):
                    output = io.BytesIO()
                    image.save(output, format='WEBP', quality=quality, method=4)
                    if output.tell() <= MAX_IMAGE_BYTES:
                        return 'data:image/webp;base64,' + base64.b64encode(output.getvalue()).decode()
                image = image.resize((max(1, int(image.width * .8)), max(1, int(image.height * .8))), Image.Resampling.LANCZOS)
    except (ValueError, OSError, binascii.Error, Image.DecompressionBombError):
        abort(400, 'Invalid image.')


def safe_link(attrs, new=False):
    href = attrs.get((None, 'href'), '')
    if not href.lower().startswith(('https://', 'http://')) and not internal_article_url(href):
        return None
    attrs[(None, 'rel')] = 'nofollow noopener noreferrer'
    return attrs


def internal_article_url(value):
    return bool(re.fullmatch(r'(?:/materials/[1-9]\d*/edit|/party/[1-9]\d*/materials/[1-9]\d*)(?:#kw-h-[\w-]+)?', value))


def clean_html(html, internal_urls=()):
    def attribute(tag, name, value):
        if tag == 'a' and name == 'href':
            return value.lower().startswith(('http://', 'https://')) or internal_article_url(value) and value in internal_urls
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} and name == 'id':
            return bool(re.fullmatch(r'kw-h-[\w-]+', value))
        return tag == 'img' and (name == 'alt' or name == 'src' and (bool(IMAGE_URL.fullmatch(value)) or remote_image_url(value) or bool(LOCAL_IMAGE.fullmatch(value))))
    cleaned = bleach.clean(html, tags=TAGS, attributes=attribute,
                           protocols=['http', 'https', 'data'], strip=True)
    return cleaned


def normalize_content(text):
    if len(text.encode()) > MAX_CONTENT_BYTES:
        abort(400, 'Description exceeds 5 MB.')
    if text.startswith(RICH_PREFIX):
        html = clean_html(text[len(RICH_PREFIX):])

        replacements = {}

        class Validate(HTMLParser):
            text_length = 0

            def handle_data(self, data):
                self.text_length += len(data)

            def handle_starttag(self, tag, attrs):
                if tag == 'img':
                    url = dict(attrs).get('src', '')
                    if url not in replacements:
                        replacements[url] = optimize_image(url)
        parser = Validate()
        parser.feed(html)
        if parser.text_length > 50000:
            abort(400, 'Description text exceeds 50000 characters.')
        for url, optimized in replacements.items():
            if url != optimized:
                html = html.replace('src="' + escape(url, quote=True) + '"', 'src="' + optimized + '"')
        if len(html.encode()) + len(RICH_PREFIX) > MAX_CONTENT_BYTES:
            abort(400, 'Description exceeds 5 MB.')
        return RICH_PREFIX + html
    # Validate image destinations parsed by Markdown, including reference images.
    class Images(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                optimize_image(dict(attrs).get('src', ''))
    Images().feed(markdown(text))
    text_only = re.sub(r'data:image/[^\s)]+', '', text)
    if len(text_only) > 50000:
        abort(400, 'Description text exceeds 50000 characters.')
    return text


def render_content(text, references=None):
    text = text or ''
    from app.lib.article_references import ReferenceRenderer, wiki_plugin
    renderer = mistune.create_markdown(renderer=ReferenceRenderer(references), hard_wrap=True,
        plugins=['strikethrough', 'table', 'url', wiki_plugin])
    allowed = set((references or {}).values())
    html = clean_html(text[len(RICH_PREFIX):], allowed) if text.startswith(RICH_PREFIX) else clean_html(renderer(text), allowed)
    html = re.sub(r'<img\b(?![^>]*\bsrc=)[^>]*>', '', html)
    return Markup(bleach.linkify(html, callbacks=[safe_link], parse_email=False, skip_tags=['pre', 'code']))


def content_excerpt(text, limit=300):
    class PlainText(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, value):
            self.parts.append(value)

        def handle_starttag(self, tag, attrs):
            if tag in {'p', 'br', 'h2', 'h3', 'blockquote', 'li'}:
                self.parts.append(' ')

    parser = PlainText()
    parser.feed(str(render_content(text)))
    return ' '.join(''.join(parser.parts).split())[:limit]


def render_inline(text):
    """Formatting for names and short fields, without nested blocks or links."""
    return Markup(bleach.clean(str(render_content(text)),
        tags={'strong', 'b', 'em', 'i', 'u', 's', 'del', 'code'}, strip=True).strip())

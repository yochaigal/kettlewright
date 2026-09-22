"""Render item images without allowing active HTML in player descriptions."""
import re
from html import escape
from urllib.parse import urlsplit

import bleach
from markupsafe import Markup


def render_item_description(text):
    def image(match):
        alt, url = match.groups()
        try:
            parsed = urlsplit(url)
            valid = parsed.scheme.lower() in ('http', 'https') and bool(parsed.netloc)
        except ValueError:
            valid = False
        if not valid:
            return escape(match.group(0))
        return f'<img src="{escape(url, quote=True)}" alt="{escape(alt, quote=True)}">'

    text = re.sub(r'!\[([^\]\n]*)\]\(([^\s)]+)\)', image, text or '')
    clean = bleach.clean(text, tags=['p', 'br', 'b', 'i', 'em', 'strong', 'a', 'img'],
                         attributes={'a': ['href', 'title'], 'img': ['src', 'alt']},
                         protocols=['http', 'https'], strip=True)
    # Apply presentation/privacy attributes after sanitizing player-supplied HTML.
    clean = clean.replace('<img ', '<img class="item-description-image" loading="lazy" referrerpolicy="no-referrer" ')
    return Markup(clean.replace('\n', '<br>'))

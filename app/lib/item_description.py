"""Item descriptions share the application Markdown renderer."""
from markupsafe import Markup
from app.lib.rich_content import render_content


def render_item_description(text):
    return Markup(str(render_content(text)).replace('<img ',
        '<img class="item-description-image" loading="lazy" referrerpolicy="no-referrer" '))

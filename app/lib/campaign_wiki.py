"""A read-only, wiki-style view of a campaign for its owner (#421).

Editing stays in the article editor. Here every article is a page: links
between articles open other pages, and each page shows where it sits in the
campaign (breadcrumbs, sub-articles) and what refers to it (backlinks).
"""
import html
import re

from flask import url_for

from app.lib.article_references import bind_references, headings, reference_urls
from app.lib.campaigns import map_related_ids, material_hierarchy
from app.lib.content_types import CATEGORIES, CATEGORY_GROUPS
from app.lib.rich_content import content_excerpt
from app.models import ContentEntry


def wiki_url(entry):
    return url_for('campaigns.wiki', campaign_id=entry.campaign_id, entry_id=entry.id)


def campaign_entries(campaign):
    return ContentEntry.query.filter_by(owner_id=campaign.owner_id, campaign_id=campaign.id).order_by(ContentEntry.id).all()


def _path_to(items, entry_id, trail=()):
    """Ancestors of the first place an article appears in the tree."""
    for item in items:
        if item['entry'].id == entry_id:
            return list(trail)
        found = _path_to(item['children'], entry_id, trail + (item['entry'],))
        if found is not None:
            return found
    return None


def _ordered(entries):
    return sorted(entries, key=lambda entry: ((entry.title or '').casefold(), entry.id))


def home_groups(entries):
    """Articles grouped like the article type picker, in its order."""
    group_of = {category: group for group, categories in CATEGORY_GROUPS.items() for category in categories}
    groups = {}
    for entry in entries:
        group = group_of.get(entry.category, 'Notes')
        groups.setdefault(group, []).append(entry)
    order = list(CATEGORY_GROUPS)
    return [(group, _ordered(groups[group])) for group in sorted(groups, key=order.index)]


def page_context(campaign, entry=None):
    entries = campaign_entries(campaign)
    by_id = {item.id: item for item in entries}
    context = dict(campaign=campaign, entry=entry, hierarchy=material_hierarchy(entries),
                   article_count=len(entries), content_categories=CATEGORIES, excerpt=content_excerpt)
    if entry is None:
        # The home page: the campaign's front page if it has one (imported adventures
        # do), then its top-level articles by type. Sub-articles are a click away.
        roots = [item['entry'] for item in context['hierarchy']]
        intro = next((item for item in roots if item.category == 'overview' and item.title == campaign.name), None)
        context.update(intro=intro, groups=home_groups([item for item in roots if item is not intro]),
                       hearts=[item for item in entries if item.is_heart],
                       cover=cover_image(campaign, entries) is not None)
        if intro is not None:
            bindings = bind_references(intro, intro.body, intro.references, entries)
            context['references'] = reference_urls(intro.body, bindings, by_id, link=lambda target_id: wiki_url(by_id[target_id]))
        return context
    # Resolve links now: an article saved before its target existed has no stored binding.
    all_bindings = {item.id: bind_references(item, item.body, item.references, entries) for item in entries}
    bindings = all_bindings[entry.id]
    references = reference_urls(entry.body, bindings, by_id, link=lambda target_id: wiki_url(by_id[target_id]))
    # Related articles chosen in the editor, map structure, and [[links]] in the text.
    by_key = {item.reference_key: item.id for item in entries}
    inline = {by_key[key] for key in (bindings or {}).values() if key in by_key}
    outgoing = ({link.target_id for link in entry.links} | map_related_ids(entry) | inline) - {entry.id}
    incoming = ({link.source_id for link in entry.incoming_links}
                | {item_id for item_id, found in all_bindings.items() if entry.reference_key in found.values()}) - {entry.id}
    # Sub-articles come from the same tree as the sidebar, so maps list their points too.
    position = _find(context['hierarchy'], entry.id)
    children = [item['entry'] for item in position['children']] if position else []
    context.update(
        references=references,
        breadcrumbs=_path_to(context['hierarchy'], entry.id) or [],
        toc=headings(entry.body),
        children=children,
        links_to=_ordered(by_id[i] for i in outgoing if i in by_id and by_id[i] not in children),
        linked_from=_ordered(by_id[i] for i in incoming if i in by_id),
    )
    return context


def _find(items, entry_id):
    """The first place an article appears, depth first: where the tree expands it."""
    for item in items:
        if item['entry'].id == entry_id:
            return item
        found = _find(item['children'], entry_id)
        if found is not None:
            return found
    return None


# ----- Campaign covers -----
# The first image in the campaign's front page, else in its other articles. No
# stored column: change the cover by changing which image comes first.

IMAGE_IN_BODY = re.compile(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)|<img\b[^>]*?\bsrc="([^"]+)"', re.I)


def first_image(body):
    from app.lib.material_images import LOCAL_IMAGE
    from app.lib.rich_content import IMAGE_URL, remote_image_url
    for match in IMAGE_IN_BODY.finditer(body or ''):
        url = match.group(1) or html.unescape(match.group(2))
        # The same images an article is allowed to show.
        if IMAGE_URL.fullmatch(url) or remote_image_url(url) or LOCAL_IMAGE.fullmatch(url):
            return url
    return None


def cover_image(campaign, entries):
    front = [entry for entry in entries if entry.category == 'overview' and entry.title == campaign.name]
    for entry in front + sorted((entry for entry in entries if entry not in front), key=lambda entry: entry.id):
        url = first_image(entry.body)
        if url:
            return url
    return None


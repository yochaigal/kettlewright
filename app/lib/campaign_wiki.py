"""Wiki-style reading pages for campaign articles (#421).

Every article is a page: links between articles open other pages, and each page
shows where it sits (breadcrumbs, sub-articles) and what refers to it (backlinks).
Editing stays in the article editor.

Three sources share one template:
- a campaign, for its owner (/campaigns/<id>/wiki/),
- the owner's unfiled articles (/materials/wiki/),
- what a party has been shown, for its members (/party/<id>/wiki/ and
  /party/<id>/materials/<entry>).
  Party pages only ever see published versions (known_entries), never originals.
"""
import html
import re

from flask import url_for
from flask_babel import _

from app.lib.translations import N_

from app.lib.article_references import bind_references, headings, reference_urls
from app.lib.campaigns import article_entries, map_related_ids, material_hierarchy
from app.lib.content_types import CATEGORIES, CATEGORY_GROUPS, PARTY_NOTE
from app.models import ContentEntry


def _id(entry):
    return entry['id'] if isinstance(entry, dict) else entry.id


def _title(entry):
    return (entry['title'] if isinstance(entry, dict) else entry.title) or ''


def _ordered(entries):
    return sorted(entries, key=lambda entry: (_title(entry).casefold(), _id(entry)))


def campaign_entries(campaign):
    return ContentEntry.query.filter_by(owner_id=campaign.owner_id, campaign_id=campaign.id).order_by(ContentEntry.id).all()


def unfiled_entries(owner_id):
    return ContentEntry.query.filter_by(owner_id=owner_id, campaign_id=None).filter(
        ContentEntry.category != PARTY_NOTE).order_by(ContentEntry.id).all()


def _path_to(items, entry_id, trail=()):
    """Ancestors of the first place an article appears in the tree."""
    for item in items:
        if _id(item['entry']) == entry_id:
            return list(trail)
        found = _path_to(item['children'], entry_id, trail + (item['entry'],))
        if found is not None:
            return found
    return None


def _find(items, entry_id):
    """The first place an article appears, depth first: where the tree expands it."""
    for item in items:
        if _id(item['entry']) == entry_id:
            return item
        found = _find(item['children'], entry_id)
        if found is not None:
            return found
    return None


_MAP_KINDS = {'realm': N_('Realm'), 'dungeon': N_('Dungeon'), 'forest': N_('Forest'), 'freeform': N_('Freeform')}


def wiki_maps(entries, url):
    """The wiki's Maps section: every map (nested ones too), apart from the articles. url(map entry) opens one."""
    maps = []
    for entry in entries:
        if isinstance(entry, dict):
            if entry.get('map_id'):
                maps.append({'id': entry['id'], 'map_id': entry['map_id'], 'title': entry['title'],
                             'kind': entry.get('map_kind', 'freeform')})
        elif entry.pointcrawl is not None:
            maps.append({'id': entry.id, 'map_id': entry.pointcrawl.id, 'title': entry.title, 'kind': entry.pointcrawl.kind})
    return [dict(item, url=url(item), kind_label=_MAP_KINDS.get(item['kind'], N_('Freeform')))
            for item in sorted(maps, key=lambda item: (item['title'].casefold(), item['id']))]


def home_groups(entries):
    """Articles grouped like the article type picker, in its order (maps have their own section)."""
    group_of = {category: group for group, categories in CATEGORY_GROUPS.items() for category in categories}
    groups = {}
    for entry in entries:
        category = entry['category'] if isinstance(entry, dict) else entry.category
        groups.setdefault(group_of.get(category, 'Notes'), []).append(entry)
    order = list(CATEGORY_GROUPS)
    return [(group, _ordered(groups[group])) for group in sorted(groups, key=order.index)]


def _article_parts(hierarchy, entry_id, by_id, outgoing, incoming):
    """Breadcrumbs, sub-articles and both directions of links for one page."""
    position = _find(hierarchy, entry_id)
    # Sub-articles come from the same tree as the sidebar, so maps list their points too.
    children = [item['entry'] for item in position['children']] if position else []
    child_ids = {_id(child) for child in children}
    return dict(
        breadcrumbs=_path_to(hierarchy, entry_id) or [],
        children=children,
        links_to=_ordered(by_id[i] for i in outgoing - {entry_id} - child_ids if i in by_id),
        linked_from=_ordered(by_id[i] for i in incoming - {entry_id} if i in by_id),
    )


# ----- Owner: a campaign, or the unfiled articles -----

def page_context(campaign, entry=None, owner_id=None, module=None):
    """Owner pages: everything in a campaign, or (module) one module of it. With campaign=None, unfiled articles."""
    if module is not None:
        entries = ContentEntry.query.filter_by(owner_id=campaign.owner_id, module_id=module.id).order_by(ContentEntry.id).all()
        page_url = lambda entry_id=None: url_for('campaigns.module_wiki', campaign_id=campaign.id, module_id=module.id,
                                                 entry_id=entry_id)
        home = dict(home_title=module.title, home_edit_url=url_for('campaigns.module_view', campaign_id=campaign.id,
                                                                   module_id=module.id))
    elif campaign is not None:
        entries = campaign_entries(campaign)
        page_url = lambda entry_id=None: url_for('campaigns.wiki', campaign_id=campaign.id, entry_id=entry_id)
        home = dict(home_title=campaign.name, home_edit_url=None)
    else:
        entries = unfiled_entries(owner_id)
        page_url = lambda entry_id=None: url_for('campaigns.unfiled_wiki', entry_id=entry_id)
        home = dict(home_title=_('Unfiled articles'), home_edit_url=url_for('campaigns.library'))
    by_id = {item.id: item for item in entries}
    link = lambda target_id: page_url(target_id)
    context = dict(campaign=campaign, module=module, entry=entry, hierarchy=material_hierarchy(article_entries(entries)),
                   maps=wiki_maps(entries, lambda item: page_url(item['id'])), page_url=page_url,
                   article_count=len(entries), content_categories=CATEGORIES,
                   # Article cards show the article's first picture (served by entry_image).
                   card_images={item.id for item in entries if item.image or first_image(item.body)}, **home)
    if module is not None:
        # Listed on its home and in the sidebar of every page.
        context.update(module_backgrounds=module_backgrounds(module), module_items=module_items(module))
    if entry is None:
        # The home page: the front page if there is one (a module's description; an Overview named
        # after the module or campaign, from before), then its top-level articles by type.
        roots = [item['entry'] for item in context['hierarchy']]
        front = module.title if module is not None else campaign.name if campaign is not None else None
        intro = next((item for item in roots if item.category == 'overview' and item.title == front), None)
        if module is not None:
            description = module.description
        else:  # A campaign made by adding a module is named after it: that module's description.
            description = next((item.description for item in (campaign.modules if campaign else [])
                                if item.title == campaign.name and item.description), '')
        if description:
            intro = None
        context.update(intro=intro, intro_text=description or (intro.body if intro else ''), references={},
                       groups=home_groups([item for item in roots if item is not intro]),
                       hearts=[item for item in entries if item.is_heart])
        if module is not None:
            if module_cover(module, entries) is not None:
                context['cover_url'] = url_for('campaigns.module_cover', campaign_id=campaign.id, module_id=module.id)
        elif campaign is not None and cover_image(campaign, entries) is not None:
            context['cover_url'] = url_for('campaigns.campaign_cover', campaign_id=campaign.id)
        if intro is not None:
            bindings = bind_references(intro, intro.body, intro.references, entries)
            context['references'] = reference_urls(intro.body, bindings, by_id, link=link)
        return context
    # Resolve links now: an article saved before its target existed has no stored binding.
    all_bindings = {item.id: bind_references(item, item.body, item.references, entries) for item in entries}
    bindings = all_bindings[entry.id]
    # Related articles chosen in the editor, map structure, and [[links]] in the text.
    by_key = {item.reference_key: item.id for item in entries}
    inline = {by_key[key] for key in (bindings or {}).values() if key in by_key}
    outgoing = {link.target_id for link in entry.links} | map_related_ids(entry) | inline
    incoming = ({link.source_id for link in entry.incoming_links}
                | {item_id for item_id, found in all_bindings.items() if entry.reference_key in found.values()})
    context.update(references=reference_urls(entry.body, bindings, by_id, link=link), toc=headings(entry.body),
                   edit_url=url_for('campaigns.edit_entry', entry_id=entry.id),
                   **_article_parts(context['hierarchy'], entry.id, by_id, outgoing, incoming))
    return context


# ----- Party: only what the party has been shown -----

PARTY_LINK = re.compile(r'/party/\d+/materials/(\d+)(?:#|$)')


def party_url(party):
    """The party page."""
    return url_for('party.party_view', ownername=party.owner_username or party.party_owner.username,
                   party_url=party.party_url)


def _warden_kinds(party, entries):
    """{entry id: 'note' | 'original'} for what this party sees, for the Warden's buttons (Edit/Delete or Hide)."""
    return {entry['id']: 'note' if entry['category'] == PARTY_NOTE else 'original' for entry in entries}


def party_context(party, entry_id=None, owner_view=False, owner_id=None):
    """A party member's page for one revealed article, or (entry_id=None) the party's wiki home.

    Built from published versions only. The home is the one place for everything the party knows (#440):
    the party notes, then what was revealed by type."""
    from app.lib.campaigns import known_entries, party_knowledge_tree
    entries, hierarchy = party_knowledge_tree(party.id)
    # Maps open on the party map page (fog and pins), never as wiki articles.
    maps = wiki_maps(known_entries(party.id).values(),
                     lambda item: url_for('campaigns.party_map_view', party_id=party.id, map_id=item['map_id']))
    by_id = {entry['id']: entry for entry in entries}
    page_url = lambda target_id=None: (url_for('campaigns.party_entry', party_id=party.id, entry_id=target_id)
                                       if target_id is not None else url_for('campaigns.party_wiki', party_id=party.id))
    context = dict(party=party, campaign=None, hierarchy=hierarchy, maps=maps, page_url=page_url, back_url=party_url(party),
                   content_categories=dict(CATEGORIES, **{PARTY_NOTE: N_('Party note')}),
                   home_title=party.name, article_count=len(entries), owner_view=owner_view,
                   # The Warden's buttons per item: note (Edit, Delete), original (Hide).
                   # Members edit the party's notes too (only the Warden deletes them or hides articles).
                   warden_kinds=_warden_kinds(party, entries) if owner_view else
                   {entry['id']: 'member_note' for entry in entries if entry['category'] == PARTY_NOTE})
    if entry_id is None:
        # Like a campaign's home: top-level articles by type. No front page: that belongs to the
        # Warden's private campaign. Party notes come first, newest first.
        roots = [item['entry'] for item in hierarchy]
        notes = sorted((item for item in roots if item['category'] == PARTY_NOTE), key=lambda item: item['id'], reverse=True)
        # A cover like a campaign's, from what the party was shown: the first picture in a revealed
        # top-level article, else in any revealed article, else in a party note.
        pictured = [item for item in roots if item['category'] != PARTY_NOTE] + \
                   [item for item in entries if item['category'] != PARTY_NOTE] + notes
        cover = next((item['id'] for item in pictured if item['has_image']), None)
        context.update(entry=None, intro=None, hearts=[], cover=False, party_cover=cover, home_edit_url=None, party_notes=notes,
                       groups=home_groups([item for item in roots if item['category'] != PARTY_NOTE]))
        return context
    entry = by_id.get(entry_id)
    if entry is None:
        return None

    def linked_ids(item):
        # Published related articles, plus [[links]] that resolved to a revealed page.
        found = {link['id'] for link in item.get('links', [])}
        for url in (item.get('references') or {}).values():
            match = PARTY_LINK.search(url)
            if match:
                found.add(int(match.group(1)))
        return found

    outgoing = linked_ids(entry)
    incoming = {other['id'] for other in entries if entry_id in linked_ids(other)}
    # The Warden's buttons come from warden_kinds (see wiki.html warden_actions); originals are
    # edited in their module, notes from the party.
    context.update(entry=entry, references=entry.get('references') or {}, toc=headings(entry['body']),
                   edit_url=None, **_article_parts(hierarchy, entry_id, by_id, outgoing, incoming))
    return context


# ----- Campaign covers -----
# The first image in the campaign's front page, else in its other articles. No
# stored column: change the cover by changing which image comes first.

IMAGE_IN_BODY = re.compile(r'!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)|<img\b[^>]*?\bsrc="([^"]+)"', re.I)


def module_backgrounds(module):
    """A module's backgrounds for its wiki (#476): name, description and their Markdown (no front matter)."""
    from app.lib.campaign_backgrounds import background_markdown
    return [{'name': name, 'description': background.get('background_description', ''),
             'text': background_markdown(name, background, localized=True).split('---\n', 2)[2]}
            for name, background in sorted((module.backgrounds or {}).items(), key=lambda item: item[0].casefold())]


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
    """The campaign's picture, else the first in its modules' or its own front page, else in its other articles."""
    if campaign.image:  # Its own picture (#476).
        return campaign.image
    # Its modules' front pages: the one it is named after first (a campaign made by adding a module).
    for module in sorted(campaign.modules, key=lambda module: (module.title != campaign.name, module.id)):
        if first_image(module.description):
            return first_image(module.description)
    front = [entry for entry in entries if entry.category == 'overview' and entry.title == campaign.name]
    for entry in front + sorted((entry for entry in entries if entry not in front), key=lambda entry: entry.id):
        url = entry.image or first_image(entry.body)
        if url:
            return url
    return None



def module_cover(module, entries):
    """A module's picture: the first in its description (or an Overview named after it), else in its articles."""
    if first_image(module.description):
        return first_image(module.description)
    front = [entry for entry in entries if entry.category == 'overview' and entry.title == module.title]
    for entry in front + sorted((entry for entry in entries if entry not in front), key=lambda entry: entry.id):
        url = entry.image or first_image(entry.body)
        if url:
            return url
    return None


def module_items(module):
    """A module's items for its wiki (#476): name, badges (its tags, as written: "bulky", "charges 3/3") and
    description (Markdown)."""
    from app.lib.module_items import item_details, sorted_items
    return [{'name': name, 'badges': [tag for tag in item_details(item, localized=True).split(', ') if tag],
             'description': item.get('description', '')}
            for name, item in sorted_items(module)]

"""Campaign workspaces, party knowledge, and pointcrawl editing."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory, send_file
from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import selectinload

import json

from app.models import (db, Campaign, Module, MapPin, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap, CampaignImport)
from app.lib.campaign_import import (preview_archive, single_file_preview, import_preview, apply_overrides,
    ImportError, MAX_ARCHIVE, MAX_FILE)
from app.lib.campaign_backgrounds import BackgroundError
from app.lib.modules import MODULES, add_module
from app.lib.campaigns import (CATEGORIES, MAP_KINDS, PATH_TYPES, campaign_for, check_version,
    entry_audiences, integer, known_entries, map_projection, map_related_ids, notify_parties, owned,
    party_access, publishable_party, render_content, save_geometry, text_value, content_value,
    material_hierarchy, material_deletion_plan, delete_material_plan, save_article_children, set_article_parent, POINT_TYPES,
    PIN_SIZES, campaign_maps, reveal_with_map, set_world_map, world_map)
from app.lib.rich_content import content_excerpt
from app.lib.article_references import (private_reference_urls, bind_references, reference_urls,
    headings, tokens)
from app.lib.content_types import CATEGORY_GROUPS, CATEGORY_ROOTS, ARTICLE_MAP_KINDS, ARTICLE_PARENT_TYPES, PARTY_NOTE
from app.lib.campaigns import attach_map, map_only, article_entries, reveal_entry, ensure_article_map, ensure_article_tree_maps, populate_realm_map, article_parent_choices, place_new_realm_poi
from app.lib.material_images import LOCAL_IMAGE, image_directory, cleanup_images, image_references, image_value

campaigns = Blueprint('campaigns', __name__)


@campaigns.before_request
@login_required
def authorize():
    # Validate the whole operation before flushing partial edits or advancing versions.
    db.session.autoflush = False
    if request.endpoint in ('campaigns.new_map', 'campaigns.map_data', 'campaigns.new_entry', 'campaigns.edit_entry', 'campaigns.reveal'):
        request.max_content_length = 32 * 1024 * 1024
        request.max_form_memory_size = 32 * 1024 * 1024
    if request.endpoint == 'campaigns.import_archive':
        request.max_content_length = MAX_ARCHIVE + 1024 * 1024
    if request.method == 'POST' and not FlaskForm().validate_on_submit():
        abort(400, 'Invalid CSRF token.')


@campaigns.after_request
def private_response(response):
    if request.method == 'POST':
        if response.status_code >= 400:
            db.session.rollback()
        cleanup_images()
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@campaigns.errorhandler(StaleDataError)
@campaigns.errorhandler(IntegrityError)
def conflict(error):
    db.session.rollback()
    return _('This content changed in another tab. Reload before saving.'), 409


@campaigns.app_template_global('csrf_token')
def csrf_token():
    """A CSRF token for small forms on any page (the star button, #476)."""
    from flask_wtf.csrf import generate_csrf
    return generate_csrf()


@campaigns.context_processor
def common_context():
    return {'content_categories': CATEGORIES, 'category_groups': CATEGORY_GROUPS, 'category_roots': CATEGORY_ROOTS, 'article_map_kinds': ARTICLE_MAP_KINDS, 'article_parent_types': ARTICLE_PARENT_TYPES,
            'point_categories': {k: CATEGORIES[k] for k in CATEGORIES if k in POINT_TYPES}, 'path_types': PATH_TYPES,
            'content_form': FlaskForm(), 'render_content': render_content, 'content_excerpt': content_excerpt,
            'private_reference_urls': private_reference_urls, 'module_parts': _module_parts(),
            'part_badges': _part_badges, 'is_starred': _is_starred, 'background_anchor': _background_anchor,
            'item_anchor': _item_anchor}


def _is_starred(kind, target_id, name=''):
    """Whether this person starred it (#476); their stars are read once per request."""
    from flask import g
    from app.lib.stars import star_keys
    if 'star_keys' not in g:
        g.star_keys = star_keys(current_user.id)
    return (kind, target_id, name) in g.star_keys


def _background_anchor(name):
    from app.lib.stars import background_anchor
    return background_anchor(name)


def _item_anchor(name):
    from app.lib.module_items import item_anchor
    return item_anchor(name)


def _module_parts():
    from app.lib.modules import MODULE_PARTS
    return MODULE_PARTS


def _part_badges(counts):
    from app.lib.modules import part_badges
    return part_badges(counts)


@campaigns.route('/materials/reference-catalog')
def reference_catalog():
    campaign = campaign_for(request.args.get('campaign_id'))
    entries = ContentEntry.query.filter_by(owner_id=current_user.id,
        campaign_id=campaign.id if campaign else None).filter(ContentEntry.category != PARTY_NOTE).order_by(
        ContentEntry.title, ContentEntry.id).all()
    return jsonify(articles=[{'id': entry.id, 'title': entry.title, 'path': entry.source_path,
        'headings': headings(entry.body)} for entry in entries])


@campaigns.route('/materials/reference-preview', methods=['POST'])
def reference_preview():
    body = content_value(request.form.get('body', ''))
    campaign = campaign_for(request.form.get('campaign_id'))
    entry_id = request.form.get('entry_id')
    entry = article(integer(entry_id)) if entry_id else ContentEntry(
        owner_id=current_user.id, campaign_id=campaign.id if campaign else None)
    entries = ContentEntry.query.filter_by(owner_id=current_user.id,
        campaign_id=campaign.id if campaign else None).filter(ContentEntry.category != PARTY_NOTE).all()
    bindings = bind_references(entry, body, entry.references, entries)
    targets = {item.id: item for item in entries}
    if entry.id:
        # Self-heading links in an unsaved draft use that draft's headings.
        targets[entry.id] = {'body': body, 'reference_key': entry.reference_key}
    refs = reference_urls(body, bindings, targets)
    return jsonify(html=str(render_content(body, refs)), references=refs,
        unresolved=[token for token in tokens(body) if token not in refs])


def my_parties():
    return Party.query.filter_by(owner=current_user.id).order_by(Party.name).all()


def my_campaigns():
    return Campaign.query.filter_by(owner_id=current_user.id).options(
        selectinload(Campaign.entries)).order_by(Campaign.name).all()


def article(entry_id):
    """One of my campaign articles; party notes are only reachable from their party."""
    entry = owned(ContentEntry, entry_id)
    if entry.category == PARTY_NOTE:
        abort(404)
    return entry


def library_entries():
    return ContentEntry.query.filter_by(owner_id=current_user.id).filter(ContentEntry.category != PARTY_NOTE).options(
        selectinload(ContentEntry.pointcrawl), selectinload(ContentEntry.presentations))


def campaign_audience(campaign):
    """Parties that have been shown at least one of this campaign's articles (no stored connection)."""
    if campaign is None:
        return set()
    return {party_id for (party_id,) in db.session.query(PartyPresentation.party_id).join(ContentEntry).filter(
        ContentEntry.campaign_id == campaign.id, PartyPresentation.published.is_(True)).distinct()}


def available_parties(entry):
    """The parties an article can be revealed to: its campaign's party.

    Parties of other campaigns that were already shown it stay listed, so the Warden can still change or hide that."""
    shown = {p.party_id for p in entry.presentations}
    return sorted((party for party in my_parties() if party.campaign_id == entry.campaign_id or party.id in shown),
                  key=lambda party: (party.campaign_id != entry.campaign_id, party.name.casefold()))


def entry_redirect(entry):
    """After saving: a map goes back to its map editor, an article to the article editor."""
    if map_only(entry):
        return redirect(url_for('campaigns.map_edit', map_id=entry.pointcrawl.id))
    return redirect(url_for('campaigns.edit_entry', entry_id=entry.id))


def campaign_module(campaign_id, module_id):
    """One of my campaigns and one of its modules."""
    campaign = owned(Campaign, campaign_id)
    module = db.get_or_404(Module, module_id)
    if module.campaign_id != campaign.id:
        abort(404)
    return campaign, module


def module_page(module):
    return url_for('campaigns.module_view', campaign_id=module.campaign_id, module_id=module.id)


def new_campaign(name):
    """A campaign is created with its (empty) party; it opens on its home, ready for modules."""
    from app.lib.campaign_parties import create_campaign
    campaign = create_campaign(current_user.id, text_value(name, 200, True))
    db.session.commit()
    return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))


@campaigns.route('/campaigns/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return new_campaign(request.form.get('name'))
    from app.lib.campaign_wiki import cover_image
    from app.lib.campaign_parties import party_cards, played_parties
    from app.lib.stars import starred_cards
    campaigns_list = my_campaigns()
    entries = library_entries().order_by(ContentEntry.title).all()
    by_campaign = {campaign.id: [e for e in entries if e.campaign_id == campaign.id] for campaign in campaigns_list}
    return render_template('campaigns/index.html', campaigns=campaigns_list, articles=by_campaign,
        parties={c.id: c.parties for c in campaigns_list},
        covers={campaign.id: cover_image(campaign, by_campaign[campaign.id]) is not None for campaign in campaigns_list},
        # Players reach the parties they play in (other Wardens' campaigns) from here.
        played=party_cards(played_parties(current_user.id)),
        # Removed from their campaign (#483): a campaign's Add existing party brings one back.
        unassigned=party_cards([party for party in my_parties() if party.campaign_id is None]),
        starred=starred_cards(current_user.id))


@campaigns.route('/stars', methods=['POST'])
def star():
    """Star or unstar (#476) a party, module, article, map or background: a bookmark on the Campaigns page."""
    from app.lib.stars import toggle_star
    toggle_star(request.form.get('kind', ''), integer(request.form.get('target_id')),
                (request.form.get('name') or '')[:200], request.form.get('starred', '1') == '1')
    target = request.form.get('next', '')
    # Back where the star was pressed; only to a page of this site.
    if not target.startswith('/') or target.startswith('//') or '\\' in target:
        target = url_for('campaigns.index')
    return redirect(target)


@campaigns.route('/campaigns/<int:campaign_id>/cover')
def campaign_cover(campaign_id):
    """The campaign card's picture: the first image in its articles."""
    from app.lib.campaign_wiki import campaign_entries, cover_image
    campaign = owned(Campaign, campaign_id)
    url = cover_image(campaign, campaign_entries(campaign))
    return card_image(url, own=bool(campaign.image) and url == campaign.image)


@campaigns.route('/party/<int:party_id>/image')
def party_image(party_id):
    """A party's own picture (#476), for anyone in the party."""
    party = party_access(party_id)
    return card_image(party.image or None, own=True)


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/cover')
def module_cover(campaign_id, module_id):
    """A module's picture, for its wiki: the first image in its description, else in its articles."""
    from app.lib.campaign_wiki import module_cover as cover
    campaign, module = campaign_module(campaign_id, module_id)
    return card_image(cover(module, list(module.entries)))


def card_image(url, own=False):
    """Serve a card's picture: inline uploads as bytes (not a 500 KB page attribute), anything else by redirect."""
    import base64
    from app.lib.rich_content import IMAGE_URL
    if url is None:
        abort(404)
    if IMAGE_URL.fullmatch(url):
        kind, data = url[len('data:'):].split(';base64,', 1)
        response = current_app.response_class(base64.b64decode(data), mimetype=kind)
    elif own and LOCAL_IMAGE.fullmatch(url):
        # An article's own stored image (#476): the caller checked who may see it. It is in no text,
        # so /material-images (which checks the texts) would not serve it.
        match = LOCAL_IMAGE.fullmatch(url)
        response = send_from_directory(image_directory() / match[1], match[2], mimetype='image/webp')
    else:
        response = redirect(url)
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Caching follows the blueprint: private, no-store.
    return response


@campaigns.route('/materials/<int:entry_id>/image')
def entry_image(entry_id):
    """An article card's picture, for its owner: its own image (#476), else the first image in its text."""
    from app.lib.material_images import article_image
    entry = article(entry_id)
    url = article_image(entry)
    return card_image(url, own=url == entry.image)


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>/image')
def party_entry_image(party_id, entry_id):
    """A party card's picture: the article's own image (#476), else the first image in what this party
    was shown. Only for what it was shown."""
    from app.lib.campaign_wiki import first_image
    party_access(party_id)
    entry = known_entries(party_id).get(entry_id)
    if entry is None:
        abort(404)
    return card_image(entry['image'] or first_image(entry['body']), own=bool(entry['image']))


@campaigns.route('/campaigns/create', methods=['POST'])
def create_new():
    """The "New campaign" dialog: a name. Notes and articles are written inside a campaign's modules."""
    if request.form.get('kind', 'campaign') != 'campaign':
        abort(400)
    return new_campaign(request.form.get('name'))


# ----- Parties: created in a campaign (several at once for a West Marches game) -----

@campaigns.route('/campaigns/<int:campaign_id>/parties', methods=['POST'])
def new_party(campaign_id):
    """Another party in the campaign: same world, modules and backgrounds; its own roster, storage and board."""
    from app.lib.campaign_parties import create_party, party_page
    campaign = owned(Campaign, campaign_id)
    party = create_party(campaign, text_value(request.form.get('name'), 64, True),
                         text_value(request.form.get('description', ''), 2000))
    db.session.commit()
    return redirect(party_page(party))


@campaigns.route('/campaigns/<int:campaign_id>/parties/add', methods=['POST'])
def add_parties(campaign_id):
    """Add existing parties (#483): ones without a campaign, or moved from another of the Warden's campaigns.
    A party plays in one campaign at a time; it keeps its characters, storage and what it was shown."""
    campaign = owned(Campaign, campaign_id)
    ids = {integer(value) for value in request.form.getlist('party_id')}
    parties = Party.query.filter(Party.id.in_(ids), Party.owner == current_user.id).all() if ids else []
    if not parties or len(parties) != len(ids):
        abort(400)
    for party in parties:
        party.campaign = campaign
    db.session.commit()
    flash(_('Added %(names)s to %(campaign)s.', names=', '.join(party.name for party in parties),
            campaign=campaign.name), 'success')
    return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))


@campaigns.route('/party/<int:party_id>/campaign', methods=['POST'])
def assign_party(party_id):
    """From the Campaigns page (#483): add a party without a campaign to one of the Warden's campaigns."""
    party = db.get_or_404(Party, party_id)
    if party.owner != current_user.id:
        abort(404)
    campaign = owned(Campaign, integer(request.form.get('campaign_id')))
    party.campaign = campaign
    db.session.commit()
    flash(_('Added %(names)s to %(campaign)s.', names=party.name, campaign=campaign.name), 'success')
    return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))


@campaigns.route('/campaigns/<int:campaign_id>/parties/<int:party_id>/remove', methods=['POST'])
def remove_party(campaign_id, party_id):
    """Remove a party from the campaign (#483): it has no campaign until it is added to one again.
    It keeps its characters, storage and what it was shown."""
    campaign = owned(Campaign, campaign_id)
    party = db.get_or_404(Party, party_id)
    if party.owner != current_user.id or party.campaign_id != campaign.id:
        abort(404)
    party.campaign = None
    db.session.commit()
    flash(_('Removed %(party)s from %(campaign)s. It is listed under Parties without a campaign.',
            party=party.name, campaign=campaign.name), 'success')
    return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))


# ----- Modules: what a campaign is built from -----

@campaigns.route('/campaigns/<int:campaign_id>/marketplace/<slug>', methods=['POST'])
def add_marketplace_module(campaign_id, slug):
    """Modules Marketplace: add a bundled module (articles, maps, backgrounds) to this campaign."""
    from app.lib.modules import MODULES, add_module
    campaign = owned(Campaign, campaign_id)
    if slug not in MODULES:
        abort(404)
    title = MODULES[slug]['title']
    try:
        module = add_module(campaign, slug)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Module %s failed for user %s', slug, current_user.id)
        flash(_('Could not add %(title)s. Please try again.', title=title), 'error')
        return redirect(url_for('campaigns.lobby', campaign_id=campaign_id))
    flash(_('%(title)s was added to %(campaign)s.', title=title, campaign=campaign.name), 'success')
    return redirect(module_page(module))


@campaigns.route('/campaigns/<int:campaign_id>/modules', methods=['POST'])
def new_module(campaign_id):
    """A new module: empty, or with a random realm, dungeon or forest (generated in the browser)."""
    from app.lib.modules import create_module
    campaign = owned(Campaign, campaign_id)
    module = create_module(campaign, text_value(request.form.get('name'), 200, True))
    kind = request.form.get('kind') if request.form.get('kind') in ('realm', 'dungeon', 'forest') else 'realm'
    if request.form.get('start') != 'random':
        db.session.commit()
        return redirect(module_page(module))
    if request.form.get('draft'):
        # The browser generated the draft: save the module and its map together.
        db.session.flush()
        pointcrawl = create_map_entry(campaign, kind, request.form.get('title') or module.title,
                                      request.form.get('body', ''), request.form.get('draft'), module=module)
        if world_map(campaign) is None:  # A generated setting is the World Map of a campaign without one (#488).
            set_world_map(campaign, pointcrawl)
        db.session.commit()
        return redirect(module_page(module))
    db.session.commit()
    # Fallback when the browser could not generate: the map page, with only bounded, known options.
    def percent(name, default):
        value = request.form.get(name, '')
        return int(value) if value.isdigit() and int(value) <= 100 else default
    options = {'random': 1, 'world': 1, 'children': '1' if request.form.get('generate_children') else '0',
               'forest': percent('forest_chance', 50), 'forest_pois': percent('dungeon_chance', 25)}
    if request.form.get('poi_count', '') in ('3', '6', '8', '12', '20'):
        options['pois'] = request.form['poi_count']
    return redirect(url_for('campaigns.new_map', campaign_id=campaign.id, module_id=module.id, kind=kind, **options))


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/', methods=['GET', 'POST'])
def module_view(campaign_id, module_id):
    """A module: its articles, notes, maps, backgrounds and items. POST saves its settings (name, description)."""
    from app.lib.campaign_backgrounds import background_markdown
    campaign, module = campaign_module(campaign_id, module_id)
    if request.method == 'POST':
        check_version(module, request.form.get('version'))
        module.title = text_value(request.form.get('name'), 200, True)
        if 'description' in request.form:
            module.description = content_value(request.form['description'])
        module.version += 1
        db.session.commit()
        return redirect(module_page(module))
    entries = library_entries().filter_by(module_id=module.id).order_by(ContentEntry.id).all()
    backgrounds = module.backgrounds or {}
    from app.lib.module_items import destinations, item_details, sorted_items
    # Maps are listed on their own: region maps first, then the maps entered from their points.
    maps = sorted((entry for entry in entries if entry.pointcrawl),
                  key=lambda entry: (bool(maps_showing(entry)), entry.title.casefold(), entry.id))
    return render_template('campaigns/module.html', campaign=campaign, module=module,
                           hierarchy=material_hierarchy(article_entries(entries)), article_count=len(article_entries(entries)),
                           maps=[(entry, maps_showing(entry)) for entry in maps], backgrounds=backgrounds,
                           items=[(name, item, item_details(item)) for name, item in sorted_items(module)],
                           send_choices=destinations(campaign) if module.items else [])


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/export')
def module_export(campaign_id, module_id):
    from slugify import slugify
    from app.lib.campaign_export import export_module
    campaign, module = campaign_module(campaign_id, module_id)
    return send_file(export_module(module), mimetype='application/zip', as_attachment=True,
                     download_name=f'{slugify(module.title) or "module"}.zip')


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/delete', methods=['POST'])
def delete_module(campaign_id, module_id):
    """Delete a module with its articles, maps and backgrounds. What parties were shown goes too."""
    campaign, module = campaign_module(campaign_id, module_id)
    check_version(module, request.form.get('version'))
    title = module.title
    entries = list(module.entries)
    if entries:  # Deletes them (with their maps and what parties were shown), commits and tells the parties.
        delete_material_plan(*material_deletion_plan(entries, current_user.id, campaign.id))
    db.session.delete(module)
    db.session.commit()
    flash(_('%(title)s was removed from %(campaign)s.', title=title, campaign=campaign.name), 'success')
    return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/background', methods=['GET', 'POST'])
def module_background(campaign_id, module_id):
    """Write a background (Markdown), edit one (?name=), or remove one. Files are added with Add files (import)."""
    from app.lib.campaign_backgrounds import (BackgroundError, add_backgrounds, background_markdown,
                                              parse_background_text, remove_background, BACKGROUND_TEMPLATE)
    campaign, module = campaign_module(campaign_id, module_id)
    name = request.values.get('name', '')
    current = (module.backgrounds or {}).get(name) if name else None
    if name and current is None:
        abort(404)
    error, text = None, None
    if request.method == 'POST':
        check_version(module, request.form.get('version'))
        action = request.form.get('action')
        try:
            if action == 'remove':
                remove_background(module, name)
            elif action == 'save':
                text = text_value(request.form.get('text'), 200000, True)
                found = parse_background_text(text, name or 'background')
                if name and name not in found:
                    remove_background(module, name)  # Renamed.
                add_backgrounds(module, found)
            else:
                abort(400)
        except BackgroundError as exc:
            error = str(exc)
        if error is None:
            module.version += 1
            db.session.commit()
            return redirect(module_page(module) + '#backgrounds')
        db.session.rollback()
        if action != 'save':
            flash(error, 'error')
            return redirect(module_page(module) + '#backgrounds')
    if text is None:
        text = background_markdown(name, current) if current is not None else BACKGROUND_TEMPLATE
    return render_template('campaigns/background.html', campaign=campaign, module=module, name=name,
                           text=text, error=error)


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/item', methods=['GET', 'POST'])
def module_item(campaign_id, module_id):
    """Write an item (Markdown), edit one (?name=), or remove one (#476). Files are added with Add files (import)."""
    from app.lib.module_items import ITEM_TEMPLATE, ItemError, add_items, item_markdown, parse_item_text, remove_item
    campaign, module = campaign_module(campaign_id, module_id)
    name = request.values.get('name', '')
    current = (module.items or {}).get(name) if name else None
    # Back where it was opened: the module's page, or (next=wiki) its wiki's Items.
    back = request.values.get('next') if request.values.get('next') == 'wiki' else 'module'
    back_url = (url_for('campaigns.module_wiki', campaign_id=campaign.id, module_id=module.id) + '#wiki-home-items'
                if back == 'wiki' else module_page(module) + '#items')
    if name and current is None:
        abort(404)
    error, text = None, None
    if request.method == 'POST':
        check_version(module, request.form.get('version'))
        action = request.form.get('action')
        try:
            if action == 'remove':
                remove_item(module, name)
            elif action == 'save':
                text = text_value(request.form.get('text'), 20000, True)
                new_name, item = parse_item_text(text)
                if new_name != name and new_name in (module.items or {}):
                    raise ItemError(f'This module already has an item named "{new_name}".')
                if name and new_name != name:
                    remove_item(module, name)  # Renamed.
                add_items(module, {new_name: item})
            else:
                abort(400)
        except ItemError as exc:
            error = str(exc)
        if error is None:
            module.version += 1
            db.session.commit()
            return redirect(back_url)
        db.session.rollback()
        if action != 'save':
            flash(error, 'error')
            return redirect(back_url)
    if text is None:
        text = item_markdown(current) if current is not None else ITEM_TEMPLATE
    return render_template('campaigns/item.html', campaign=campaign, module=module, name=name, text=text, error=error,
                           back=back, back_url=back_url)


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/item/send', methods=['GET', 'POST'])
def send_module_item(campaign_id, module_id):
    """Send a copy of a module item (#476) to a party: into its storage or a character's inventory.
    The module keeps its item."""
    from app.lib.module_items import destination, destinations, item_markdown, send_item
    campaign, module = campaign_module(campaign_id, module_id)
    name = request.values.get('name', '')
    item = (module.items or {}).get(name)
    if item is None:
        abort(404)
    back = request.values.get('next') if request.values.get('next') == 'wiki' else 'module'
    if request.method == 'POST':
        target = destination(campaign, request.form.get('to'))
        if target is None:
            abort(400, 'Choose a container of one of this campaign\'s parties.')
        party, holder, container_id = target
        if party.owner != current_user.id:
            abort(403)
        if back == 'wiki':
            from app.lib.module_items import item_anchor
            back_url = (url_for('campaigns.module_wiki', campaign_id=campaign.id, module_id=module.id)
                        + '#' + item_anchor(name))
        else:
            back_url = module_page(module) + '#items'
        if send_item(item, holder, container_id) is None:
            db.session.rollback()
            flash(_('There is no room for %(item)s in %(container)s. Make room, or choose another container.',
                    item=name, container=next((c['name'] for c in json.loads(holder.containers or '[]')
                                               if c['id'] == container_id), '')), 'error')
            return redirect(back_url)
        db.session.commit()
        notify_parties([party.id])
        flash(_('A copy of %(item)s is now with %(holder)s.', item=name, holder=holder.name), 'success')
        return redirect(back_url)
    return render_template('campaigns/item_send.html', campaign=campaign, module=module, name=name,
                           text=item_markdown(item), choices=destinations(campaign), back=back)


# ----- Character options: the backgrounds a party's characters choose from (set on the party page) -----

@campaigns.route('/party/<int:party_id>/backgrounds', methods=['POST'])
def party_backgrounds(party_id):
    """The Warden offers the official backgrounds to this party, or not, for Second Edition and for Barebones
    characters (its campaign's modules' ones always)."""
    from app.lib.campaign_backgrounds import (custom_backgrounds, has_custom_options, party_backgrounds as offered,
                                              party_barebones_backgrounds)
    party = party_access(party_id, editing=True)
    party.official_backgrounds = request.form.get('official') == '1'
    party.official_barebones = request.form.get('barebones') == '1'
    db.session.commit()
    if request.accept_mimetypes.best == 'application/json':
        # Saved in place from the party page: what its players now choose from.
        none = not custom_backgrounds(party.campaign)
        return jsonify(offered=sorted(offered(party)), customized=has_custom_options(party),
                       fallback=not party.official_backgrounds and none,
                       barebones_offered=len(party_barebones_backgrounds(party)),
                       barebones_fallback=not party.official_barebones and none)
    return redirect(url_for('party.party_view', ownername=party.owner_username, party_url=party.party_url) + '#backgrounds')


def back_to_party(party):
    """Party notes live in the party wiki (#440): back there after a change."""
    return redirect(url_for('campaigns.party_wiki', party_id=party.id))


# ----- Party notes: written on the party page, for that party only -----
# Stored as an article of type PARTY_NOTE, unfiled, with one published party
# version holding the same text. Campaigns never lists them (see article()).

def party_note(party, entry_id):
    """A note of this party: written by its Warden and given to it. Members may edit it; only the Warden deletes it."""
    entry = db.get_or_404(ContentEntry, entry_id)
    presentation = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party.id).first()
    if entry.category != PARTY_NOTE or presentation is None or entry.owner_id != party.owner:
        abort(404)
    return entry, presentation


@campaigns.route('/party/<int:party_id>/notes', methods=['POST'])
def add_party_note(party_id):
    party = party_access(party_id, editing=True)
    title = text_value(request.form.get('title'), 200, True)
    body = content_value(request.form.get('body', ''))
    entry = ContentEntry(owner_id=current_user.id, category=PARTY_NOTE, title=title, body=body)
    entry.presentations.append(PartyPresentation(party=party, title=title, body=body))
    db.session.add(entry)
    db.session.commit()
    notify_parties([party.id])
    return back_to_party(party)


@campaigns.route('/party/<int:party_id>/notes/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_party_note(party_id, entry_id):
    """Party notes are the party's shared notes: every member can edit them (deleting stays with the Warden)."""
    from flask import g
    from app.lib.material_images import image_references
    party = party_access(party_id)
    entry, presentation = party_note(party, entry_id)
    if request.method == 'POST':
        check_version(entry, request.form.get('version'))
        g.kept_local_images = image_references(entry.body)
        entry.title = presentation.title = text_value(request.form.get('title'), 200, True)
        entry.body = presentation.body = content_value(request.form.get('body', ''))
        if request.form.get('drawing'):  # Sent only when the sketch changed.
            entry.drawing = note_drawing(request.form['drawing'])
        db.session.commit()
        notify_parties([party.id])
        return back_to_party(party)
    return render_template('campaigns/party_note.html', party=party, entry=entry, is_warden=party.owner == current_user.id)


def note_drawing(text):
    """A party note's sketch from the editor, validated like a map's drawing. None when it is empty."""
    import json
    from app.lib.map_drawing import validate_drawing
    try:
        drawing = validate_drawing(json.loads(text))
    except (ValueError, TypeError):
        abort(400, 'Invalid drawing.')
    return drawing if drawing.get('elements') else None


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>/version', methods=['GET', 'POST'])
def edit_party_version(party_id, entry_id):
    """There are no party versions any more: a party reads the original. Its old address opens the article."""
    party_access(party_id, editing=True)
    return redirect(url_for('campaigns.party_entry', party_id=party_id, entry_id=entry_id))


@campaigns.route('/party/<int:party_id>/notes/<int:entry_id>/delete', methods=['POST'])
def delete_party_note(party_id, entry_id):
    party = party_access(party_id, editing=True)
    entry, _presentation = party_note(party, entry_id)
    db.session.delete(entry)
    db.session.commit()
    notify_parties([party.id])
    flash(_('Party note deleted.'), 'success')
    return back_to_party(party)


@campaigns.route('/campaigns/<int:campaign_id>/', methods=['GET', 'POST'])
def lobby(campaign_id):
    """The campaign lobby, for its Warden: its name, parties and modules. POST renames it.

    No wiki here: a module's card opens it in wiki mode, and Read everything as wiki opens all of it."""
    from app.lib.campaign_wiki import campaign_entries, module_cover
    from app.lib.campaign_parties import party_cards
    from app.lib.modules import marketplace, module_counts
    campaign = owned(Campaign, campaign_id)
    if request.method == 'POST':
        check_version(campaign, request.form.get('version'))
        campaign.name = text_value(request.form.get('name'), 200, True)
        if 'image' in request.form:
            campaign.image = image_value(request.form['image'])
        campaign.version += 1
        db.session.commit()
        return redirect(url_for('campaigns.lobby', campaign_id=campaign.id))
    counts = {}
    # How much each party was shown from this campaign (parties of other campaigns are listed with it).
    for (party_id,) in db.session.query(PartyPresentation.party_id).join(ContentEntry).filter(
            ContentEntry.campaign_id == campaign.id, PartyPresentation.published.is_(True)):
        counts[party_id] = counts.get(party_id, 0) + 1
    entries = campaign_entries(campaign)
    # Add existing party (#483): the Warden's parties without a campaign first, then those of their other campaigns.
    others = {}
    for party in sorted((party for party in my_parties() if party.campaign_id != campaign.id),
                        key=lambda party: (party.campaign is not None, party.campaign.name.casefold() if party.campaign else '',
                                           party.campaign_id or 0, party.name.casefold())):
        others.setdefault(party.campaign, []).append(party)
    return render_template('campaigns/lobby.html', campaign=campaign, article_count=len(entries),
        parties=party_cards(campaign.parties), other_parties=others,
        # Parties of other campaigns that were shown something from this one (say, after they moved).
        audience=[(party, counts[party.id]) for party in my_parties()
                  if party.id in counts and party.campaign_id != campaign.id],
        modules=[(module, module_counts(module)) for module in campaign.modules],
        module_covers={module.id for module in campaign.modules if module_cover(module, list(module.entries))},
        marketplace=marketplace(campaign))


def lobby_url(campaign_id, anchor=''):
    return url_for('campaigns.lobby', campaign_id=campaign_id) + anchor


@campaigns.route('/campaigns/<int:campaign_id>/wiki/')
@campaigns.route('/campaigns/<int:campaign_id>/wiki/<int:entry_id>/')
def wiki(campaign_id, entry_id=None):
    """Read everything in the campaign (all its modules) as a wiki; the article editor stays the place to change it."""
    from app.lib.campaign_wiki import page_context
    campaign = owned(Campaign, campaign_id)
    entry = None
    if entry_id is not None:
        entry = article(entry_id)
        if entry.campaign_id != campaign.id:
            abort(404)
    return render_wiki(page_context(campaign, entry), entry)


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/wiki/')
@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/wiki/<int:entry_id>/')
def module_wiki(campaign_id, module_id, entry_id=None):
    """Read one module as a wiki: its own articles and maps."""
    from app.lib.campaign_wiki import page_context
    campaign, module = campaign_module(campaign_id, module_id)
    entry = None
    if entry_id is not None:
        entry = article(entry_id)
        if entry.module_id != module.id:
            abort(404)
    context = page_context(campaign, entry, module=module)
    context['module_parties'] = campaign.parties  # Reveal module: to one of the campaign's parties.
    if entry is None and module.items:  # Send an item (#476), in a modal on the home's item cards.
        from app.lib.module_items import destinations
        context['send_choices'] = destinations(campaign)
    return render_wiki(context, entry)


def render_wiki(context, entry):
    if entry is not None:
        context['reveal_parties'] = reveal_choices(entry)
        if entry.pointcrawl:
            # A map's page shows the map (read only); Edit opens the map editor.
            context.update(graph=map_projection(entry.pointcrawl), pointcrawl=None, editing=False, party=None,
                           embedded=True, nested_maps=[], locations=[], is_map=map_only(entry),
                           map_edit_url=url_for('campaigns.map_edit', map_id=entry.pointcrawl.id))
            if map_only(entry):
                context['edit_url'] = context['map_edit_url']
    return render_template('campaigns/wiki.html', **context)


@campaigns.route('/materials/wiki/')
@campaigns.route('/materials/wiki/<int:entry_id>/')
def unfiled_wiki(entry_id=None):
    """There are no unfiled articles any more: every article is in a module of a campaign."""
    if entry_id is not None:
        return redirect(read_url(article(entry_id)))
    return redirect(url_for('campaigns.index'))


@campaigns.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = owned(Campaign, campaign_id)
    check_version(campaign, request.form.get('version'))
    if request.form.get('confirm') != 'delete':
        return render_template('campaigns/delete_campaign.html', campaign=campaign)
    # Delete owned contents through the ORM so maps, geometry, links and party
    # presentations are removed together. Related materials outside this campaign
    # and the connected parties themselves remain independent.
    audiences = set()
    title = campaign.name
    for entry in list(campaign.entries):
        audiences.update(presentation.party_id for presentation in entry.presentations)
        db.session.delete(entry)
    # Its parties go with it; the characters are kept and leave their party.
    from app.lib.campaign_parties import delete_party
    for party in list(campaign.parties):
        audiences.discard(party.id)
        delete_party(party)
    db.session.delete(campaign)
    db.session.commit()
    notify_parties(audiences)
    flash(_('%(title)s was removed from your campaigns.', title=title), 'success')
    return redirect(url_for('campaigns.index'))


@campaigns.route('/materials/')
def library():
    return redirect(url_for('campaigns.index'))


@campaigns.route('/party/<int:party_id>/materials/')
def party_materials(party_id):
    """The party's old Wiki tab: everything it held is in the party wiki now (#440)."""
    party_access(party_id)
    return redirect(url_for('campaigns.party_wiki', party_id=party_id))


@campaigns.route('/party/<int:party_id>/wiki/')
def party_wiki(party_id):
    """Everything the party knows, read as a wiki: party notes, then revealed articles by type.
    The Warden also adds party notes here and sees the campaigns behind it."""
    from app.lib.campaign_wiki import party_context
    party = party_access(party_id)
    return render_template('campaigns/wiki.html', graph=None, pointcrawl=None, editing=False, embedded=True,
                           nested_maps=[], locations=[],
                           **party_context(party, owner_view=party.owner == current_user.id, owner_id=current_user.id))


@campaigns.route('/party/<int:party_id>/materials/data')
def party_materials_data(party_id):
    party_access(party_id)
    return jsonify(entries=[entry for entry in known_entries(party_id).values() if entry['category'] != 'path' or not db.session.get(ContentEntry, entry['id']).map_edges])


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>')
def party_entry(party_id, entry_id):
    """A revealed article, read as a wiki page built only from what the party was shown."""
    from app.lib.campaign_wiki import party_context
    party = party_access(party_id)
    shown = known_entries(party.id).get(entry_id)
    if shown is not None and shown['map_only']:
        # A map is opened on the party map page (its fog and pins), never as an article.
        return redirect(url_for('campaigns.party_map_view', party_id=party.id, map_id=shown['map_id']))
    context = party_context(party, entry_id, owner_view=party.owner == current_user.id)
    if context is None:
        abort(404)
    entry = context['entry']
    map_url = url_for('campaigns.party_map_view', party_id=party.id, map_id=entry['map_id']) if entry['map_id'] else None
    # A party note's sketch, below its text (read only here; drawn in the note's editor).
    sketch = db.session.get(ContentEntry, entry_id).drawing if entry['category'] == PARTY_NOTE else None
    return render_template('campaigns/wiki.html', graph=None, map_url=map_url, sketch=sketch, **context)


@campaigns.route('/materials/<int:entry_id>/preview')
def entry_preview(entry_id):
    entry = article(entry_id)
    return render_template('campaigns/preview.html', entry=entry,
                           graph=map_projection(entry.pointcrawl) if entry.pointcrawl else None,
                           references=private_reference_urls(entry),
                           article_url=url_for('campaigns.edit_entry', entry_id=entry.id))


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>/preview')
def party_entry_preview(party_id, entry_id):
    party_access(party_id)
    entry = known_entries(party_id).get(entry_id)
    if entry is None:
        abort(404)
    return render_template('campaigns/preview.html', entry=entry,
                           graph=map_projection(db.get_or_404(PointcrawlMap, entry['map_id']), party_id) if entry['map_id'] else None,
                           references=entry.get('references', {}),
                           article_url=url_for('campaigns.party_entry', party_id=party_id, entry_id=entry_id))


def chosen_module(values):
    """The module an article goes to: module_id ("c<id>" for a campaign without modules yet), else campaign_id's
    first module. None when neither is given."""
    from app.lib.modules import default_module
    value = values.get('module_id') or ''
    if value.startswith('c'):
        return default_module(owned(Campaign, integer(value[1:])))
    if value:
        module = db.get_or_404(Module, integer(value))
        if module.campaign.owner_id != current_user.id:
            abort(403)
        return module
    campaign = campaign_for(values.get('campaign_id'))
    return default_module(campaign) if campaign else None


def module_choices():
    """The article form's Module select: my campaigns, each with its modules."""
    return [(campaign, campaign.modules) for campaign in my_campaigns()]


@campaigns.route('/materials/new', methods=['GET', 'POST'])
def new_entry():
    """A new private article (or note) in a module. Parties see it only once it is revealed to them."""
    # What the form submits wins over the page's URL defaults.
    module = chosen_module(request.form if request.method == 'POST' else request.args)
    if request.method == 'GET' and module is None and not my_campaigns():
        flash(_('Create a campaign first: articles are written in its modules.'), 'error')
        return redirect(url_for('campaigns.index'))
    if request.method == 'GET' and module is not None and module.id is None:
        db.session.rollback()  # Don't create the campaign's first module just to show the form.
        module = None
    campaign = module.campaign if module is not None else campaign_for(request.args.get('campaign_id'))
    if request.method == 'POST':
        if module is None:
            abort(400, 'Choose a module.')
        category = request.form.get('category')
        if category == 'location':
            from app.lib.content_types import legacy_point_type
            category = legacy_point_type(request.form.get('title'))
        if category not in CATEGORIES or category in ('map', 'overview'):
            abort(400)
        title = text_value(request.form.get('title'), 200, True)
        body = content_value(request.form.get('body', ''))
        entry = ContentEntry(owner_id=current_user.id, campaign=campaign, module=module, category=category,
                             title=title, body=body, image=image_value(request.form.get('image')),
                             is_heart=category == 'settlement' and request.form.get('is_heart') == 'on',
                             path_type=request.form.get('path_type', 'standard'))
        if entry.path_type not in PATH_TYPES:
            abort(400)
        db.session.add(entry)
        set_article_parent(entry, request.form.get('parent_id'))
        import json
        try:
            children = json.loads(request.form.get('children', '[]'))
        except (ValueError, TypeError):
            abort(400, 'Invalid article draft.')
        save_article_children(entry, children, body=body)
        ensure_article_tree_maps(entry)
        place_new_realm_poi(entry)
        db.session.commit()
        return entry_redirect(entry)
    initial_category = request.args.get('category')
    if initial_category not in CATEGORIES or initial_category in ('map', 'overview'):
        initial_category = 'custom'
    return render_template('campaigns/entry.html', entry=None, campaign=campaign, module=module,
                           initial_title=request.args.get('title', '')[:200], initial_category=initial_category,
                           module_groups=module_choices(), candidates=[], selected_links=set(),
                           parent_candidates=article_parent_choices(library_entries()), selected_parent=request.args.get('parent_id', ''))


def move_to_campaign(entry, campaign):
    """File an article (with its sub-articles and map contents) under another campaign, or None for unfiled.

    What parties were shown stays as it is."""
    campaign_id = campaign.id if campaign else None
    moved = [entry]
    if entry.pointcrawl:
        moved += [n.entry for n in entry.pointcrawl.nodes] + [e.entry for e in entry.pointcrawl.edges]
    if campaign_id != entry.campaign_id:
        # Imported descendants move with their parent, just like map contents.
        pending = list(moved)
        moved_by_id = {}
        while pending:
            item = pending.pop()
            if item.id in moved_by_id:
                continue
            moved_by_id[item.id] = item
            pending.extend(item.children)
            if item.pointcrawl:
                pending.extend(n.entry for n in item.pointcrawl.nodes)
                pending.extend(e.entry for e in item.pointcrawl.edges)
                pending.extend(n.nested_map.entry for n in item.pointcrawl.nodes if n.nested_map)
        moved = list(moved_by_id.values())
        if any(item.owner_id != current_user.id for item in moved):
            abort(403)
        if any(item.campaign_id != entry.campaign_id for item in moved):
            abort(409, 'Linked content belongs to another workspace. Unlink it before moving.')
        moved_ids = {item.id for item in moved}
        if entry.parent_id and entry.parent_id not in moved_ids:
            entry.parent = None
        for item in moved:
            if any(node.map.entry_id not in moved_ids and node.map.entry.campaign_id != campaign_id for node in item.map_nodes):
                abort(400, 'Move this location together with its map.')
            if item.category == 'path' and any(edge.map.entry_id not in moved_ids for edge in item.map_edges):
                abort(400, 'Move this path together with its map.')
            if item.pointcrawl and any(n.map.entry_id not in moved_ids and n.map.entry.campaign_id != campaign_id
                                      for n in item.pointcrawl.entrances):
                abort(400, 'Unlink entrances from other maps before moving this map.')
        for item in moved:
            item.campaign = campaign


def move_to_module(entry, module):
    """Move an article, its sub-articles and its map's contents to another module (of any of my campaigns)."""
    if module.campaign_id != entry.campaign_id:
        move_to_campaign(entry, module.campaign)
    moved, pending = {}, [entry]
    while pending:
        item = pending.pop()
        if item.id in moved or (item.campaign is not module.campaign and item is not entry):
            continue
        moved[item.id] = item
        pending.extend(item.children)
        if item.pointcrawl:
            pending.extend(n.entry for n in item.pointcrawl.nodes)
            pending.extend(e.entry for e in item.pointcrawl.edges)
            pending.extend(n.nested_map.entry for n in item.pointcrawl.nodes if n.nested_map)
    for item in moved.values():
        item.module = module


def maps_showing(entry):
    """The maps this article is a point on (for a map: the maps whose points lead into it)."""
    nodes = list(entry.map_nodes) + (list(entry.pointcrawl.entrances) if entry.pointcrawl else [])
    maps = {node.map.entry_id: node.map.entry for node in nodes
            if node.map.entry_id != entry.id and node.map.entry.owner_id == entry.owner_id}
    return [maps[key] for key in sorted(maps)]


@campaigns.route('/materials/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = article(entry_id)
    if map_only(entry) and request.method == 'GET':
        return redirect(url_for('campaigns.map_edit', map_id=entry.pointcrawl.id))
    previous_category = entry.category
    previous_parent = entry.parent
    if request.method == 'POST':
        check_version(entry, request.form.get('version'))
        if 'graph' in request.form:
            import json
            try:
                graph = json.loads(request.form['graph'])
            except (ValueError, TypeError):
                abort(400, 'Invalid article drawing.')
            if not entry.pointcrawl or not isinstance(graph, dict):
                abort(400, 'Invalid article drawing.')
            with db.session.no_autoflush:
                save_geometry(entry.pointcrawl, graph)
        entry.title = text_value(request.form.get('title', ''), 200)
        entry.body = content_value(request.form.get('body', ''))
        if 'image' in request.form:
            entry.image = image_value(request.form['image'])
        if entry.category not in ('map', 'path'):
            category = request.form.get('category', entry.category)
            if entry.pointcrawl and category == 'map':
                category = entry.pointcrawl.kind
            if category == 'location':
                from app.lib.content_types import legacy_point_type
                category = legacy_point_type(entry.title)
            if category not in CATEGORIES or category == 'map':
                abort(400)
            if entry.map_nodes and category not in POINT_TYPES:
                abort(400, 'Choose a point of interest type for an article on a map.')
            if entry.pointcrawl and ARTICLE_MAP_KINDS.get(category) != entry.pointcrawl.kind:
                abort(400, 'Keep the map type for this article.')
            entry.category = category
        if 'category' in request.form:  # A map's page has no Type: it keeps its Heart.
            entry.is_heart = entry.category == 'settlement' and request.form.get('is_heart') == 'on'
        if entry.category == 'path':
            kind = request.form.get('path_type')
            if kind not in PATH_TYPES:
                abort(400)
            entry.path_type = kind
        # Module: chosen in the form; a form that only names the article's own campaign keeps its module.
        if request.form.get('module_id') or request.form.get('campaign_id') not in (None, '', str(entry.campaign_id)):
            target = chosen_module(request.form)
            if target is not None and target is not entry.module:
                move_to_module(entry, target)
        if 'parent_id' in request.form:
            set_article_parent(entry, request.form.get('parent_id'), previous_category=previous_category)
        elif entry.category != previous_category and entry.parent:
            set_article_parent(entry, entry.parent_id, previous_category=previous_category)
        targets = {integer(value) for value in request.form.getlist('links')} - map_related_ids(entry)
        if entry.id in targets:
            abort(400)
        for target_id in targets:
            article(target_id)
        old_links = {link.target_id: link for link in entry.links}
        for target_id in set(old_links) - targets:
            db.session.delete(old_links[target_id])
        for target_id in targets - set(old_links):
            entry.links.append(ContentLink(target_id=target_id))
        ensure_article_map(entry)
        if entry.parent is not previous_parent:
            place_new_realm_poi(entry)
        entry.version += 1
        audiences = entry_audiences(entry)
        db.session.commit()
        notify_parties(audiences)
        return entry_redirect(entry)
    candidates = ContentEntry.query.filter(ContentEntry.owner_id == current_user.id,
        ContentEntry.id != entry.id, ContentEntry.category.notin_(('path', PARTY_NOTE))).order_by(ContentEntry.id).all()
    automatic_links = map_related_ids(entry)
    selected_links = {link.target_id for link in entry.links}
    candidates.sort(key=lambda item: (item.id not in automatic_links | selected_links, item.id))
    return render_template('campaigns/entry.html', entry=entry, campaign=entry.campaign, party=None,
                           module=entry.module, parent_entries=[entry.parent] if entry.parent else [], on_maps=maps_showing(entry),
                           module_groups=module_choices(), candidates=candidates,
                           selected_links=selected_links, automatic_links=automatic_links,
                           parent_candidates=article_parent_choices(library_entries(), entry), selected_parent=entry.parent_id or '')


@campaigns.route('/materials/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = article(entry_id)
    check_version(entry, request.form.get('version'))
    campaign_id = entry.campaign_id
    back_url = materials_url([entry], campaign_id)
    delete_material_plan(*material_deletion_plan([entry], current_user.id, campaign_id))
    return redirect(back_url)


def materials_url(entries, campaign_id):
    """Where bulk and single article actions return: their module's page, else the campaign home."""
    modules = {entry.module_id for entry in entries}
    if len(modules) == 1 and None not in modules:
        return url_for('campaigns.module_view', campaign_id=campaign_id, module_id=modules.pop())
    return url_for('campaigns.lobby', campaign_id=campaign_id) if campaign_id else url_for('campaigns.index')


@campaigns.route('/materials/bulk-delete', methods=['POST'])
def bulk_delete():
    signer = URLSafeTimedSerializer(current_app.secret_key, salt='material-deletion')
    confirmation = request.form.get('deletion_token')
    if confirmation:
        try:
            snapshot = signer.loads(confirmation, max_age=1800)
        except BadSignature:
            abort(409, 'Deletion preview expired or changed. Select the materials again.')
        if snapshot['owner_id'] != current_user.id:
            abort(403)
        campaign_id = snapshot['campaign_id']
        selected_ids = snapshot['selected_ids']
    else:
        campaign = campaign_for(request.form.get('campaign_id'))
        campaign_id = campaign.id if campaign else None
        selected_ids = sorted({integer(value) for value in request.form.getlist('entry_ids')})
        if not selected_ids:
            abort(400, 'Select at least one material.')
    if campaign_id:
        owned(Campaign, campaign_id)
    selected = [article(entry_id) for entry_id in selected_ids]
    if not confirmation:
        for entry in selected:
            check_version(entry, request.form.get(f'version_{entry.id}'))
    entries, maps = material_deletion_plan(selected, current_user.id, campaign_id)
    state = {'owner_id': current_user.id, 'campaign_id': campaign_id,
             'selected_ids': selected_ids,
             'entries': {str(key): entry.version for key, entry in entries.items()},
             'maps': {str(key): pointcrawl.version for key, pointcrawl in maps.items()}}
    back_url = materials_url(selected, campaign_id)
    if confirmation:
        if snapshot != state:
            abort(409, 'The materials or map contents changed. Review the deletion again.')
        delete_material_plan(entries, maps)
        return redirect(back_url)
    return render_template('campaigns/delete_materials.html',
        entries=sorted(entries.values(), key=lambda entry: (entry.category, entry.id)),
        deletion_token=signer.dumps(state), back_url=back_url)


@campaigns.route('/materials/bulk-reveal', methods=['POST'])
def bulk_reveal():
    signer = URLSafeTimedSerializer(current_app.secret_key, salt='material-reveal')
    confirmation = request.form.get('reveal_token')
    if confirmation:
        try:
            snapshot = signer.loads(confirmation, max_age=1800)
        except BadSignature:
            abort(409, 'Publication preview expired. Select the articles again.')
        if snapshot['owner_id'] != current_user.id:
            abort(403)
        campaign_id = snapshot['campaign_id']
        selected_ids = snapshot['selected_ids']
    else:
        campaign = campaign_for(request.form.get('campaign_id'))
        campaign_id = campaign.id if campaign else None
        selected_ids = sorted({integer(value) for value in request.form.getlist('entry_ids')})
        if not selected_ids:
            abort(400, 'Select at least one article.')
    if campaign_id:
        owned(Campaign, campaign_id)
    entries = [article(entry_id) for entry_id in selected_ids]
    if any(entry.campaign_id != campaign_id for entry in entries):
        abort(400, 'Select articles from this workspace only.')
    if not confirmation:
        for entry in entries:
            check_version(entry, request.form.get(f'version_{entry.id}'))
    parties = available_parties(entries[0])
    presentations = {entry.id: {row.party_id: row for row in entry.presentations} for entry in entries}
    state = {'owner_id': current_user.id, 'campaign_id': campaign_id, 'selected_ids': selected_ids,
             'entries': {str(entry.id): entry.version for entry in entries},
             'maps': {str(entry.id): entry.pointcrawl.version for entry in entries if entry.pointcrawl},
             'presentations': {str(entry.id): {str(p.id): presentations[entry.id][p.id].version
                 if p.id in presentations[entry.id] else 0 for p in parties} for entry in entries}}
    back_url = materials_url(entries, campaign_id)
    if confirmation:
        if snapshot != state:
            abort(409, 'The articles or what parties see changed. Review publication again.')
        selected = {integer(value) for value in request.form.getlist('party_ids')}
        if not selected:
            abort(400, 'Choose at least one party.')
        # Several articles: each party reads the originals.
        # Validate every audience and title before creating or changing any version.
        audiences = {party_id: publishable_party(entries[0], party_id) for party_id in selected}
        versions = {entry.id: revealed_version(entry, request.form, 'everything') for entry in entries}
        for entry in entries:
            for party_id, party in audiences.items():
                row = presentations[entry.id].get(party_id)
                if row is None:
                    row = PartyPresentation(entry=entry, party=party)
                    db.session.add(row)
                row.title, row.body, row.path_type = versions[entry.id]
                row.references = dict(entry.references or {})
                row.published = True
        db.session.commit()
        notify_parties(selected)
        flash(_('Revealed %(count)s articles.', count=len(entries)), 'success')
        return redirect(back_url)
    return render_template('campaigns/reveal_materials.html', entries=entries, parties=parties,
                           reveal_token=signer.dumps(state), back_url=back_url)


@campaigns.route('/campaigns/<int:campaign_id>/modules/<int:module_id>/reveal', methods=['POST'])
def reveal_module(campaign_id, module_id):
    """Reveal a whole module to one of the campaign's parties: every titled article and map it holds.
    The party reads the originals, as with any reveal."""
    campaign, module = campaign_module(campaign_id, module_id)
    party = party_access(integer(request.form.get('party_id')), editing=True)
    if party.campaign_id != campaign.id:
        abort(403)
    entries = [entry for entry in module.entries if entry.title.strip()]
    rows = {row.entry_id: row for row in PartyPresentation.query.filter(
        PartyPresentation.party_id == party.id, PartyPresentation.entry_id.in_([e.id for e in entries]))}
    for entry in entries:
        row = rows.get(entry.id)
        if row is None:
            row = PartyPresentation(entry=entry, party=party)
            db.session.add(row)
        row.title, row.body, row.path_type = revealed_version(entry)
        row.references, row.published = dict(entry.references or {}), True
    db.session.commit()
    notify_parties([party.id])
    flash(_('Revealed %(count)s articles of %(module)s to %(party)s.', count=len(entries), module=module.title,
            party=party.name), 'success')
    return redirect(url_for('campaigns.module_wiki', campaign_id=campaign.id, module_id=module.id))


# What a party sees when an article is revealed to it:
REVEAL_MODES = ('everything', 'custom')


def revealed_version(entry, form=None, mode=None):
    """(title, body, path_type): a party sees the original. There are no party versions."""
    return text_value(entry.title, 200, True), entry.body, entry.path_type


def reveal_status(entry, row):
    """none (not revealed) or same (sees the original: a party's copy always mirrors it)."""
    return 'none' if row is None or not row.published else 'same'


def read_url(entry):
    return (url_for('campaigns.wiki', campaign_id=entry.campaign_id, entry_id=entry.id) if entry.campaign_id
            else url_for('campaigns.edit_entry', entry_id=entry.id))


def reveal_choices(entry):
    """The Reveal popup's parties: what each sees now, its version (to edit), and map progress."""
    presentations = {p.party_id: p for p in entry.presentations}
    points = [node.entry for node in entry.pointcrawl.nodes] if entry.pointcrawl else []
    paths = [edge.entry for edge in entry.pointcrawl.edges] if entry.pointcrawl else []

    def revealed(items, party_id):
        return sum(any(p.party_id == party_id and p.published for p in item.presentations) for item in items)

    choices = []
    for party in available_parties(entry):
        row = presentations.get(party.id)
        choices.append({'id': party.id, 'name': party.name, 'status': reveal_status(entry, row),
                        'version': row.version if row else 0, 'title': row.title if row else '',
                        'body': row.body if row else '', 'path_type': row.path_type if row else entry.path_type,
                        'points': revealed(points, party.id), 'paths': revealed(paths, party.id),
                        'own': entry.campaign_id is None or party.campaign_id == entry.campaign_id})
    return choices


def after_reveal(entry, party_id):
    """Back where the action started: the article (default) or the party wiki ('party' is its old name)."""
    if request.values.get('return_to') in ('wiki', 'party'):
        return redirect(url_for('campaigns.party_wiki', party_id=party_id))
    if request.values.get('return_to') == 'map':  # The party's World Map page (#482).
        return redirect(url_for('campaigns.party_maps', party_id=party_id))
    if request.values.get('return_to') == 'campaign' and entry.campaign_id:
        return redirect(url_for('campaigns.lobby', campaign_id=entry.campaign_id))
    return redirect(read_url(entry))


@campaigns.route('/materials/<int:entry_id>/reveal', methods=['GET', 'POST'])
def reveal(entry_id):
    """Reveal one article to one party: it reads the original, and later edits reach it too.

    GET shows the same form as the article page's Reveal popup, as a page (the party tree links here)."""
    entry = article(entry_id)
    if request.method == 'POST':
        party_id = integer(request.form.get('party_ids'))
        party = publishable_party(entry, party_id)
        row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party.id).first()
        check_version(row, request.form.get(f'version_{party.id}'))
        reveal_entry(entry, party)
        reveal_with_map(entry, party)  # Its pins marked Reveal with the map (#482).
        count = 0
        if entry.pointcrawl and request.form.get('with_contents') == '1':
            # The whole map at once: every pin on it (and any older path; the maps inside points stay hidden).
            for item in [node.entry for node in entry.pointcrawl.nodes] + [edge.entry for edge in entry.pointcrawl.edges]:
                reveal_entry(item, party)
                count += 1
        db.session.commit()
        notify_parties([party.id])
        if count:
            flash(_('Revealed the map and its pins to %(party)s.', party=party.name), 'success')
        else:
            flash(_('Revealed to %(party)s.', party=party.name), 'success')
        return after_reveal(entry, party.id)
    return render_template('campaigns/reveal.html', entry=entry, reveal_parties=reveal_choices(entry),
                           selected=request.args.get('party_id', ''), return_to=request.args.get('return_to', ''))


@campaigns.route('/materials/import-archive', methods=['GET', 'POST'])
def import_archive():
    preview, preview_id, message = None, None, None
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    if request.method == 'POST':
        preview_id = request.form.get('preview_id')
        if preview_id:
            batch = CampaignImport.query.filter_by(id=preview_id, owner_id=current_user.id).first_or_404()
            if batch.consumed or batch.created_at < cutoff:
                abort(409, 'This preview was already imported or expired. Upload the archive again.')
            try:
                payload = apply_overrides(deepcopy(batch.payload), request.form)
            except ImportError as exc:
                abort(400, str(exc))
            # Destination: a new module in one of my campaigns, or more files for one of my modules.
            module = chosen_module({'module_id': request.form.get('module_id')}) if request.form.get('module_id') else None
            target = module.campaign if module is not None else campaign_for(request.form.get('target_campaign'))
            if target is None:
                abort(400, 'Choose the campaign to add this module to.')
            claimed = CampaignImport.query.filter_by(id=batch.id, owner_id=current_user.id, consumed=False).filter(
                CampaignImport.created_at >= cutoff).update({'consumed': True}, synchronize_session=False)
            if not claimed:
                abort(409, 'This preview was already imported.')
            try:
                import_preview(payload, current_user.id, into=target, module=module, name=payload.get('name', ''))
            except BackgroundError as exc:
                abort(400, str(exc))
            batch.payload = {}
            db.session.commit()
            module = module or target.modules[-1]
            flash(_('%(title)s was added to %(campaign)s.', title=module.title, campaign=target.name), 'success')
            return redirect(module_page(module))
        upload = request.files.get('archive')
        if not upload:
            message = _('Choose a Markdown file or a ZIP/TAR archive.')
        elif upload.filename.lower().endswith('.md'):
            try:
                preview = single_file_preview(upload.stream.read(MAX_FILE + 1), upload.filename, owner_id=current_user.id)
            except ImportError as exc:
                message = str(exc)
        elif not upload.filename.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz')):
            message = _('Unsupported file type. Upload a .md file or put your Markdown articles in a ZIP, TAR or TAR.GZ archive.')
        else:
            try:
                preview = preview_archive(upload.stream.read(MAX_ARCHIVE + 1), owner_id=current_user.id)
            except ImportError as exc:
                message = str(exc)
        if preview is not None:
            # A module without a front page is named after its file.
            from pathlib import PurePosixPath
            stem = PurePosixPath(upload.filename or '').name
            for suffix in ('.tar.gz', '.tgz', '.zip', '.tar', '.md'):
                if stem.lower().endswith(suffix):
                    stem = stem[:-len(suffix)]
                    break
            preview['name'] = stem[:200] or 'Imported module'
        if preview and not preview['errors']:
            preview_id = uuid4().hex
            # Keep staging bounded; expired previews never contain library records.
            CampaignImport.query.filter(CampaignImport.created_at < cutoff).delete(synchronize_session=False)
            CampaignImport.query.filter_by(owner_id=current_user.id, consumed=False).delete(synchronize_session=False)
            db.session.add(CampaignImport(id=preview_id, owner_id=current_user.id, payload=preview))
            db.session.commit()
    selected = request.values.get('campaign_id', '')
    module_id = request.values.get('module_id', '')
    module = chosen_module({'module_id': module_id}) if module_id else None
    from app.lib.modules import preview_counts
    return render_template('campaigns/import_archive.html', preview=preview, preview_id=preview_id, message=message,
                           campaigns_list=my_campaigns(), module=module,
                           preview_counts=preview_counts(preview) if preview else None,
                           selected_campaign=module.campaign_id if module else int(selected) if selected.isdigit() else None)


@campaigns.route('/materials/import-example.zip')
def import_example():
    import io
    import zipfile
    from pathlib import Path

    stream = io.BytesIO()
    # An example module in the format exports use: one folder per part, all Markdown.
    examples = Path(current_app.static_folder) / 'examples' / 'module'
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(examples.rglob('*.md')):
            archive.writestr(path.relative_to(examples).as_posix(), path.read_bytes())
    stream.seek(0)
    return send_file(stream, mimetype='application/zip', as_attachment=True,
                     download_name='module-example.zip')


@campaigns.route('/materials/<int:entry_id>/revoke/<int:party_id>', methods=['POST'])
def revoke(entry_id, party_id):
    """Hide an article from one party: it no longer sees it. Revealing again shows it again."""
    entry = article(entry_id)
    party = party_access(party_id, editing=True)
    row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party_id).first_or_404()
    check_version(row, request.form.get('version'))
    db.session.delete(row)
    db.session.commit()
    notify_parties([party_id])
    flash(_('Hidden from %(party)s.', party=party.name), 'success')
    return after_reveal(entry, party_id)


@campaigns.route('/materials/<int:entry_id>/map', methods=['POST'])
def article_map(entry_id):
    """Make a point (or any article) a map of its own, from the map editor: its sub-articles become its points."""
    entry = article(entry_id)
    check_version(entry, request.form.get('version'))
    if entry.category in ('path', 'paths', PARTY_NOTE):
        abort(400, 'This article cannot be a map.')
    pointcrawl = attach_map(entry)
    entry.version += 1
    db.session.commit()
    return redirect(url_for('campaigns.map_edit', map_id=pointcrawl.id))


def create_map_entry(campaign, kind, title, body, draft, module=None):
    """Create a private spatial article and its canvas in a module, optionally from a generated draft.

    The caller validates kind and commits. Reveal it to parties afterwards, like any article.
    """
    entry = ContentEntry(owner_id=current_user.id, campaign=campaign, module=module,
                         category=kind if kind != 'freeform' else 'topography',
                         title=text_value(title, 200, True), body=content_value(body or ''))
    pointcrawl = PointcrawlMap(entry=entry, kind=kind)
    db.session.add(pointcrawl)
    db.session.flush()
    if draft:
        import json
        try:
            data = json.loads(draft)
        except (ValueError, TypeError):
            abort(400)
        if not isinstance(data, dict):
            abort(400)
        data['version'] = pointcrawl.version
        with db.session.no_autoflush:
            save_geometry(pointcrawl, data)
        save_article_children(entry, data.get('children', []))
        groups = {child.category: child for child in entry.children if child.category in ('pois', 'paths')}
        for node in pointcrawl.nodes:
            if 'pois' in groups:
                node.entry.parent = groups['pois']
        for edge in pointcrawl.edges:
            if 'paths' in groups:
                edge.entry.parent = groups['paths']
        if kind == 'realm':
            db.session.flush()
            ensure_article_tree_maps(entry)
            populate_realm_map(pointcrawl)
    return pointcrawl


@campaigns.route('/maps/new', methods=['GET', 'POST'])
@campaigns.route('/materials/generate', methods=['GET', 'POST'])
def new_map():
    if request.method == 'GET' and request.path == '/maps/new':
        return redirect(url_for('campaigns.new_map', **request.args))
    module = chosen_module(request.form if request.method == 'POST' else request.args)
    if request.method == 'POST':
        kind = request.form.get('kind')
        if kind not in MAP_KINDS:
            abort(400)
        if module is None:
            abort(400, 'Choose a module.')
        pointcrawl = create_map_entry(module.campaign, kind, request.form.get('title'), '',
                                      request.form.get('draft'), module=module)
        # A generated setting (#488), or Create World Map on a party's World Map page (#482).
        if request.form.get('world') == '1' and world_map(module.campaign) is None:
            set_world_map(module.campaign, pointcrawl)
        db.session.commit()
        return entry_redirect(pointcrawl.entry)
    if module is not None and module.id is None:
        db.session.rollback()
        module = None
    if module is None and not my_campaigns():
        flash(_('Create a campaign first: maps are made in its modules.'), 'error')
        return redirect(url_for('campaigns.index'))
    kind = request.args.get('kind', 'freeform')
    if kind not in MAP_KINDS:
        abort(400)
    # Becomes the campaign's World Map when it has none (#482, #488): a generated setting, or Create World Map.
    becomes_world = request.args.get('world') == '1' and module is not None and world_map(module.campaign) is None
    return render_template('campaigns/new_map.html', module=module, module_groups=module_choices(), kind=kind,
                           campaign=module.campaign if module else None, becomes_world=becomes_world)


@campaigns.route('/maps/<int:map_id>/edit', methods=['GET', 'POST'])
def map_edit(map_id):
    """A map's editor: its title, its drawing, its points and paths. A map has no text of its own.

    POST saves the title, the module and (when it changed) the drawing with its points and paths."""
    import json
    pointcrawl = owned(PointcrawlMap, map_id)
    entry = pointcrawl.entry
    if request.method == 'POST':
        check_version(entry, request.form.get('version'))
        if 'graph' in request.form:
            try:
                graph = json.loads(request.form['graph'])
            except (ValueError, TypeError):
                abort(400, 'Invalid map drawing.')
            if not isinstance(graph, dict):
                abort(400, 'Invalid map drawing.')
            with db.session.no_autoflush:
                save_geometry(pointcrawl, graph)
        entry.title = text_value(request.form.get('title', ''), 200, True)
        if request.form.get('module_id'):
            target = chosen_module(request.form)
            if target is not None and target is not entry.module:
                was = entry.campaign
                move_to_module(entry, target)
                if entry.campaign is not was:
                    pointcrawl.world_map = False  # The World Map of the campaign it left.
        if request.form.get('pin_size') in PIN_SIZES:
            pointcrawl.pin_size = request.form['pin_size']
        if 'world_map_field' in request.form and entry.campaign is not None:
            if request.form.get('world_map') == '1':
                set_world_map(entry.campaign, pointcrawl)
            elif pointcrawl.world_map:
                set_world_map(entry.campaign, None)
        reveal_flagged_pins(entry)
        entry.version += 1
        audiences = entry_audiences(entry)
        db.session.commit()
        notify_parties(audiences)
        return redirect(url_for('campaigns.map_edit', map_id=pointcrawl.id))
    # The players' pins of every party shown this map (#482), read only: the Warden sees them while editing.
    player_pins = [{'id': f'p{pin.id}', 'x': pin.x, 'y': pin.y, 'title': f'{pin.party.name}: {pin.entry.title}',
                    'party': pin.party.name, 'note': pin.entry.title, 'html': str(render_content(pin.entry.body)),
                    'url': url_for('campaigns.party_map_view', party_id=pin.party_id, map_id=pointcrawl.id)}
                   for pin in sorted(pointcrawl.pins, key=lambda pin: pin.id)]
    return render_template('campaigns/map.html', entry=entry, pointcrawl=pointcrawl, campaign=entry.campaign,
        player_pins=player_pins, pin_sizes=PIN_SIZES,
        module=entry.module, party=None, graph=map_projection(pointcrawl), editing=True, embedded=True,
        module_groups=module_choices(), inside=maps_showing(entry), article_url=None if map_only(entry) else
        url_for('campaigns.edit_entry', entry_id=entry.id), reveal_parties=reveal_choices(entry),
        nested_maps=PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == current_user.id,
            ContentEntry.campaign_id == entry.campaign_id, PointcrawlMap.id != pointcrawl.id).all(),
        locations=ContentEntry.query.filter_by(owner_id=current_user.id, campaign_id=entry.campaign_id)
            .filter(ContentEntry.category.in_(POINT_TYPES)).all())


@campaigns.route('/maps/<int:map_id>/geography', methods=['POST'])
def realm_geography(map_id):
    import json
    pointcrawl = owned(PointcrawlMap, map_id)
    if pointcrawl.kind != 'realm':
        abort(400)
    check_version(pointcrawl, request.form.get('version'))
    check_version(pointcrawl.entry, request.form.get('article_version'))
    try:
        children = json.loads(request.form.get('children', '[]'))
    except (ValueError, TypeError):
        abort(400)
    existing = {child.category for child in pointcrawl.entry.children}
    if not isinstance(children, list):
        abort(400)
    for child in children:
        if not isinstance(child, dict) or child.get('category') not in ('topography', 'pois', 'paths'):
            abort(400, 'Choose setting geography.')
        if child['category'] in existing:
            abort(409, 'This section already exists. Reload to use its saved articles.')
        existing.add(child['category'])
    save_article_children(pointcrawl.entry, children)
    db.session.flush()
    ensure_article_tree_maps(pointcrawl.entry)
    changed = populate_realm_map(pointcrawl)
    if changed or children:
        pointcrawl.version += 1
    db.session.commit()
    return jsonify(map_projection(pointcrawl))


@campaigns.route('/maps/<int:map_id>/data', methods=['GET', 'POST'])
def map_data(map_id):
    pointcrawl = owned(PointcrawlMap, map_id)
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.form.get('graph', ''))
        except (ValueError, TypeError):
            abort(400)
        if not isinstance(data, dict):
            abort(400)
        # Delay autoflush until every graph object has complete required fields.
        with db.session.no_autoflush:
            save_geometry(pointcrawl, data)
        reveal_flagged_pins(pointcrawl.entry)
        audiences = entry_audiences(pointcrawl.entry)
        db.session.commit()
        notify_parties(audiences)
    return jsonify(map_projection(pointcrawl))


def reveal_flagged_pins(entry):
    """Pins marked Reveal with the map reach the parties already shown it (#482). The caller commits."""
    db.session.flush()
    for row in list(entry.presentations):
        if row.published:
            reveal_with_map(entry, row.party)


@campaigns.route('/party/<int:party_id>/maps/<int:map_id>/')
def party_map(party_id, map_id):
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    map_projection(pointcrawl, party.id)  # Authorize the legacy URL before redirecting.
    return redirect(url_for('campaigns.party_entry', party_id=party.id, entry_id=pointcrawl.entry_id))


# ----- Party map: a revealed map with the party's fog and pins -----

def revealed_maps(party_id):
    """The maps a party was shown (published copies of map articles), by title."""
    rows = PartyPresentation.query.join(ContentEntry).filter(
        PartyPresentation.party_id == party_id, PartyPresentation.published.is_(True)).all()
    return sorted(((row.entry.pointcrawl, row) for row in rows if row.entry.pointcrawl),
                  key=lambda item: (item[1].title.casefold(), item[0].id))


def map_presentation(party, pointcrawl):
    """This party's copy of the map article: holds its fog. 404 when the map was not revealed to it."""
    row = PartyPresentation.query.filter_by(entry_id=pointcrawl.entry_id, party_id=party.id, published=True).first()
    if row is None:
        abort(404)
    return row


def map_state(party, pointcrawl, row):
    """Fog and pins of a party map, for its page and its refreshes."""
    from app.lib.whiteboard import empty_fog
    pins = MapPin.query.filter_by(map_id=pointcrawl.id, party_id=party.id).order_by(MapPin.id).all()
    return {'fog': row.fog or empty_fog(), 'fog_version': row.fog_version,
            'pins': [{'id': pin.id, 'x': pin.x, 'y': pin.y, 'title': pin.entry.title, 'note_id': pin.entry_id,
                      'movable': can_move_pin(party, pin),  # Its maker or the Warden drags it (#482).
                      'html': str(render_content(pin.entry.body)),
                      'edit_url': url_for('campaigns.edit_party_note', party_id=party.id, entry_id=pin.entry_id)}
                     for pin in pins]}


@campaigns.route('/party/<int:party_id>/map/')
def party_maps(party_id):
    """The party page's World Map button (#482): its campaign's World Map once revealed to it.

    Otherwise the maps it was shown; the Warden also gets to create, choose or reveal the World Map here."""
    party = party_access(party_id)
    warden = party.owner == current_user.id
    maps = revealed_maps(party.id)
    world = world_map(party.campaign)
    if world is not None and any(pointcrawl.id == world.id for pointcrawl, _ in maps):
        return redirect(url_for('campaigns.party_map_view', party_id=party.id, map_id=world.id))
    # Maps entered from a point of another revealed map open from that map: the button opens the region.
    shown = {pointcrawl.id for pointcrawl, _ in maps}
    top = [item for item in maps if not any(node.map_id in shown for node in item[0].entrances)] or maps
    if len(top) == 1:
        return redirect(url_for('campaigns.party_map_view', party_id=party.id, map_id=top[0][0].id))
    hidden = PartyPresentation.query.filter_by(entry_id=world.entry_id, party_id=party.id).first() if world else None
    return render_template('campaigns/party_maps.html', party=party, maps=maps, warden=warden, world=world,
                           world_version=hidden.version if hidden else 0,
                           choices=campaign_maps(party.campaign) if warden else [],
                           modules=party.campaign.modules if warden and party.campaign else [])


@campaigns.route('/party/<int:party_id>/world-map', methods=['POST'])
def party_world_map(party_id):
    """The Warden makes one of the campaign's maps its World Map (#482), or starts a new one (create=draw|realm)."""
    party = party_access(party_id, editing=True)
    campaign = party.campaign
    if campaign is None:
        abort(400, 'Add the party to a campaign first.')
    create = request.form.get('create')
    if create in ('draw', 'realm'):
        # A new map in a module of the campaign (its first; a new one when it has none); saving it makes it the World Map.
        from app.lib.modules import default_module
        module = db.session.get(Module, integer(request.form.get('module_id'))) if request.form.get('module_id') else None
        if module is None or module.campaign_id != campaign.id:
            module = default_module(campaign)
        db.session.commit()
        args = {'kind': 'realm', 'random': 1} if create == 'realm' else {'kind': 'freeform'}
        return redirect(url_for('campaigns.new_map', module_id=module.id, world=1, **args))
    pointcrawl = db.get_or_404(PointcrawlMap, integer(request.form.get('map_id')))
    if pointcrawl.entry.campaign_id != campaign.id:
        abort(404)
    set_world_map(campaign, pointcrawl)
    db.session.commit()
    flash(_('%(map)s is the World Map of %(campaign)s.', map=pointcrawl.entry.title, campaign=campaign.name), 'success')
    return redirect(url_for('campaigns.party_maps', party_id=party.id))


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/')
def party_map_view(party_id, map_id):
    """A revealed map for the party: what it was shown, under its fog, with its pins.
    Members add pins; the Warden also uncovers the fog."""
    from flask_wtf.csrf import generate_csrf
    from app.lib.campaign_wiki import party_context
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    row = map_presentation(party, pointcrawl)
    warden = party.owner == current_user.id
    # Inside the party wiki (#476): its sidebar lists the maps and articles, this map marked.
    context = party_context(party, owner_view=warden, owner_id=current_user.id)
    context.update(breadcrumbs=[], current_map_id=pointcrawl.id)
    return render_template('campaigns/party_map.html', pointcrawl=pointcrawl, row=row, csrf=generate_csrf(),
                           graph=map_projection(pointcrawl, party.id), state=map_state(party, pointcrawl, row),
                           warden=warden, map_only=map_only(pointcrawl.entry), **context)


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/state')
def party_map_state(party_id, map_id):
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    return jsonify(map_state(party, pointcrawl, map_presentation(party, pointcrawl)))


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/fog', methods=['POST'])
def party_map_fog(party_id, map_id):
    """The Warden uncovers (or covers) part of the map for this party: one whiteboard fog operation."""
    import json as json_module
    from app.lib.whiteboard import empty_fog, fog_operation
    party = party_access(party_id, editing=True)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    row = map_presentation(party, pointcrawl)
    try:
        data = json_module.loads(request.form.get('payload', ''))
    except ValueError:
        abort(400)
    operation = data.get('operation') if isinstance(data, dict) else None
    fog = row.fog or empty_fog()
    if isinstance(operation, dict) and operation.get('id') in fog['applied']:  # A retry: already applied.
        return jsonify(fog=fog, fog_version=row.fog_version)
    if data.get('fog_version') != row.fog_version:
        return jsonify(error='changed', fog=fog, fog_version=row.fog_version), 409
    row.fog, _changed = fog_operation(fog, operation)
    row.fog_version += 1
    db.session.commit()
    notify_parties([party.id])
    return jsonify(fog=row.fog, fog_version=row.fog_version)


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/pins', methods=['POST'])
def add_map_pin(party_id, map_id):
    """Any member places a pin: a party note (title and text) at a point of the map."""
    from app.lib.campaigns import coordinate
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    map_presentation(party, pointcrawl)
    if MapPin.query.filter_by(map_id=pointcrawl.id, party_id=party.id).count() >= 500:
        abort(400, 'This map has too many pins.')
    title = text_value(request.form.get('title'), 200, True)
    body = content_value(request.form.get('body', ''))
    note = ContentEntry(owner_id=party.owner, category=PARTY_NOTE, title=title, body=body)
    note.presentations.append(PartyPresentation(party=party, title=title, body=body))
    db.session.add(note)
    db.session.add(MapPin(map_id=pointcrawl.id, party_id=party.id, entry=note, created_by=current_user.id,
                          x=coordinate(request.form.get('x')), y=coordinate(request.form.get('y'))))
    db.session.commit()
    notify_parties([party.id])
    return jsonify(map_state(party, pointcrawl, map_presentation(party, pointcrawl)))


def can_move_pin(party, pin):
    return current_user.is_authenticated and current_user.id in (pin.created_by, party.owner)


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/pins/<int:pin_id>/move', methods=['POST'])
def move_map_pin(party_id, map_id, pin_id):
    """Move a pin (#482): the member who placed it, or the Warden."""
    from app.lib.campaigns import coordinate
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    row = map_presentation(party, pointcrawl)
    pin = db.get_or_404(MapPin, pin_id)
    if pin.map_id != pointcrawl.id or pin.party_id != party.id:
        abort(404)
    if not can_move_pin(party, pin):
        abort(403)
    pin.x, pin.y = coordinate(request.form.get('x')), coordinate(request.form.get('y'))
    db.session.commit()
    notify_parties([party.id])
    return jsonify(map_state(party, pointcrawl, row))


@campaigns.route('/party/<int:party_id>/map/<int:map_id>/pins/<int:pin_id>/delete', methods=['POST'])
def delete_map_pin(party_id, map_id, pin_id):
    """Only the Warden removes pins (with their notes), as with every party note."""
    party = party_access(party_id, editing=True)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    pin = db.get_or_404(MapPin, pin_id)
    if pin.map_id != pointcrawl.id or pin.party_id != party.id:
        abort(404)
    db.session.delete(pin.entry)
    db.session.commit()
    notify_parties([party.id])
    return jsonify(map_state(party, pointcrawl, map_presentation(party, pointcrawl)))


@campaigns.route('/party/<int:party_id>/maps/<int:map_id>/data')
def party_map_data(party_id, map_id):
    party_access(party_id)
    return jsonify(map_projection(db.get_or_404(PointcrawlMap, map_id), party_id))


@campaigns.route('/materials/import')
def import_result():
    return render_template('campaigns/import.html', campaigns=my_campaigns())


@campaigns.route('/materials/import-item', methods=['GET', 'POST'])
def import_item_result():
    """Save a Tools relic or spellbook (#476) as an item of one of my modules, ready to send to a party."""
    from app.lib.module_items import ItemError, add_items, parse_item_text
    error, text, module_id = None, '', request.values.get('module_id', '')
    if request.method == 'POST':
        module = db.get_or_404(Module, integer(module_id))
        campaign, module = campaign_module(module.campaign_id, module.id)  # One of mine.
        text = text_value(request.form.get('text'), 20000, True)
        try:
            name, item = parse_item_text(text)
            if name in (module.items or {}):
                raise ItemError(_('%(module)s already has an item named %(item)s. Rename this one, or choose '
                                  'another module.', module=module.title, item=name))
            add_items(module, {name: item})
        except ItemError as exc:
            error = str(exc)
        else:
            module.version += 1
            db.session.commit()
            flash(_('%(item)s is an item of %(module)s. Send it to a party from there.', item=name,
                    module=module.title), 'success')
            return redirect(module_page(module) + '#items')
    return render_template('campaigns/import_item.html', module_groups=module_choices(), text=text,
                           module_id=str(module_id), error=error)


@campaigns.route('/articles/tables')
@campaigns.route('/maps/tables')
def map_tables():
    from app.lib.generator_tables import generator_tables
    return jsonify(generator_tables(maps_only=request.path == '/maps/tables'))


@campaigns.get('/material-images/<int:owner_id>/<filename>')
def material_image(owner_id, filename):
    url = f'/material-images/{owner_id}/{filename}'
    if not LOCAL_IMAGE.fullmatch(url):
        abort(404)
    # Its owner sees it in a text or as an article's own image (#476), e.g. as a campaign cover.
    originals = ContentEntry.query.filter_by(owner_id=owner_id).filter(
        db.or_(ContentEntry.body.contains(url), ContentEntry.image == url)).all()
    versions = PartyPresentation.query.join(ContentEntry).filter(
        ContentEntry.owner_id == owner_id, PartyPresentation.body.contains(url)).all()
    allowed = current_user.id == owner_id and bool(originals or versions)
    if not allowed:
        from app.socket_events import party_recipient_ids
        for row in versions:
            if (row.published and current_user.id in party_recipient_ids(row.party)
                    and url in image_references(known_entries(row.party_id).get(row.entry_id, {}).get('body', ''))):
                allowed = True
                break
    if not allowed:
        abort(404)
    response = send_from_directory(image_directory() / str(owner_id), filename, mimetype='image/webp')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@campaigns.cli.command('migrate-images')
def migrate_images():
    """Move existing embedded description images to instance storage."""
    import click
    from sqlalchemy.orm.attributes import flag_modified
    count = 0
    try:
        for model in (ContentEntry, PartyPresentation):
            for row in model.query.filter(model.body.contains('data:image/')).all():
                flag_modified(row, 'body')
                count += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    finally:
        cleanup_images()
    click.echo(f'Migrated {count} descriptions.')

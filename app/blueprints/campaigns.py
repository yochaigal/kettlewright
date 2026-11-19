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

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap, CampaignImport)
from app.lib.campaign_import import (preview_archive, single_file_preview, import_preview, apply_overrides,
    ImportError, MAX_ARCHIVE, MAX_FILE)
from app.lib.campaign_export import export_campaign
from app.lib.starter_adventures import STARTERS, add_starter_adventure, starter_cards
from app.lib.campaigns import (CATEGORIES, MAP_KINDS, PATH_TYPES, campaign_for, check_version,
    entry_audiences, integer, known_entries, map_projection, map_related_ids, notify_parties, owned,
    party_access, publishable_party, render_content, save_geometry, text_value, content_value,
    material_hierarchy, material_parents, material_deletion_plan, delete_material_plan, save_article_children, set_article_parent, POINT_TYPES)
from app.lib.rich_content import content_excerpt
from app.lib.article_references import (private_reference_urls, bind_references, reference_urls,
    headings, tokens)
from app.lib.content_types import CATEGORY_GROUPS, CATEGORY_ROOTS, ARTICLE_MAP_KINDS, ARTICLE_PARENT_TYPES, PARTY_NOTE
from app.lib.campaigns import ensure_article_map, ensure_article_tree_maps, populate_realm_map, article_parent_choices, place_new_realm_poi
from app.lib.material_images import LOCAL_IMAGE, image_directory, cleanup_images, image_references

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


@campaigns.context_processor
def common_context():
    return {'content_categories': CATEGORIES, 'category_groups': CATEGORY_GROUPS, 'category_roots': CATEGORY_ROOTS, 'article_map_kinds': ARTICLE_MAP_KINDS, 'article_parent_types': ARTICLE_PARENT_TYPES,
            'point_categories': {k: CATEGORIES[k] for k in CATEGORIES if k in POINT_TYPES}, 'path_types': PATH_TYPES,
            'content_form': FlaskForm(), 'render_content': render_content, 'content_excerpt': content_excerpt,
            'private_reference_urls': private_reference_urls}


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
    """Every party I run; those already shown something from this article's campaign first."""
    audience = campaign_audience(entry.campaign)
    return sorted(my_parties(), key=lambda party: (party.id not in audience, party.name.casefold()))


def entry_redirect(entry):
    return redirect(url_for('campaigns.edit_entry', entry_id=entry.id))


def create_campaign(name):
    campaign = Campaign(owner_id=current_user.id, name=name)
    db.session.add(campaign)
    db.session.commit()
    return redirect(url_for('campaigns.new_map', campaign_id=campaign.id, kind='realm'))


def start_campaign(name, start, kind, form):
    """Create a campaign: empty, or with a random realm, dungeon or forest.

    The "Create new" dialog and the campaigns page both start campaigns here.
    """
    campaign = Campaign(owner_id=current_user.id, name=name)
    db.session.add(campaign)
    kind = kind if kind in ('realm', 'dungeon', 'forest') else 'realm'
    if start == 'random' and form.get('draft'):
        # The browser generated the draft: save the campaign and its map together,
        # so a rejected draft leaves no half-created campaign.
        db.session.flush()
        create_map_entry(campaign, kind, form.get('title') or campaign.name,
                         form.get('body', ''), form.get('draft'))
        db.session.commit()
        return redirect(url_for('campaigns.workspace', campaign_id=campaign.id))
    db.session.commit()
    if start == 'empty':
        return redirect(url_for('campaigns.workspace', campaign_id=campaign.id))
    options = {}
    if start != 'random':
        kind = 'realm'
    else:
        # Fallback when the browser could not generate: open the generator with
        # only bounded, known options.
        def percent(name, default):
            value = form.get(name, '')
            return int(value) if value.isdigit() and int(value) <= 100 else default
        pois = form.get('poi_count', '')
        options = {'random': 1, 'children': '1' if form.get('generate_children') else '0',
                   'forest': percent('forest_chance', 50), 'forest_pois': percent('dungeon_chance', 25)}
        if pois in ('3', '6', '8', '12', '20'):
            options['pois'] = pois
    return redirect(url_for('campaigns.new_map', campaign_id=campaign.id, kind=kind, **options))


@campaigns.route('/campaigns/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return start_campaign(text_value(request.form.get('name'), 200, True), request.form.get('start'),
                              request.form.get('kind'), request.form)
    from app.lib.campaign_wiki import cover_image, first_image
    campaigns_list = my_campaigns()
    entries = library_entries().order_by(ContentEntry.title).all()
    by_campaign = {campaign.id: [e for e in entries if e.campaign_id == campaign.id] for campaign in campaigns_list}
    names = {party.id: party.name for party in my_parties()}
    return render_template('campaigns/index.html', campaigns=campaigns_list,
        audiences={campaign.id: [names[i] for i in sorted(campaign_audience(campaign), key=lambda i: names.get(i, '')) if i in names]
                   for campaign in campaigns_list},
        starter=starter_cards({c.name: c for c in campaigns_list}),
        articles=by_campaign,
        covers={campaign.id: cover_image(campaign, by_campaign[campaign.id]) is not None for campaign in campaigns_list},
        unfiled=[e for e in entries if e.campaign_id is None],
        # Unfiled articles are shown one card each, with their first picture when they have one.
        unfiled_images={e.id for e in entries if e.campaign_id is None and first_image(e.body)})


@campaigns.route('/campaigns/<int:campaign_id>/cover')
def campaign_cover(campaign_id):
    """The campaign card's picture: the first image in its articles."""
    from app.lib.campaign_wiki import campaign_entries, cover_image
    campaign = owned(Campaign, campaign_id)
    return card_image(cover_image(campaign, campaign_entries(campaign)))


def card_image(url):
    """Serve a card's picture: inline uploads as bytes (not a 500 KB page attribute), anything else by redirect."""
    import base64
    from app.lib.rich_content import IMAGE_URL
    if url is None:
        abort(404)
    if IMAGE_URL.fullmatch(url):
        kind, data = url[len('data:'):].split(';base64,', 1)
        response = current_app.response_class(base64.b64decode(data), mimetype=kind)
    else:
        response = redirect(url)
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Caching follows the blueprint: private, no-store.
    return response


@campaigns.route('/materials/<int:entry_id>/image')
def entry_image(entry_id):
    """An article card's picture, for its owner: the first image in the article."""
    from app.lib.campaign_wiki import first_image
    return card_image(first_image(article(entry_id).body))


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>/image')
def party_entry_image(party_id, entry_id):
    """A party card's picture: the first image in what this party was shown, never the private original."""
    from app.lib.campaign_wiki import first_image
    party_access(party_id)
    entry = known_entries(party_id).get(entry_id)
    if entry is None:
        abort(404)
    return card_image(first_image(entry['body']))


@campaigns.route('/campaigns/create', methods=['POST'])
def create_new():
    kind = request.form.get('kind')
    if kind not in ('campaign', 'note'):
        abort(400)
    name = text_value(request.form.get('name'), 200, True)
    if kind == 'campaign':
        if request.form.get('start') in ('empty', 'random'):  # From the "Create new" dialog.
            return start_campaign(name, request.form['start'], request.form.get('map_kind'), request.form)
        return create_campaign(name)
    return redirect(url_for('campaigns.new_entry', title=name, category='note'))


@campaigns.route('/campaigns/starter/<slug>', methods=['POST'])
def add_starter(slug):
    if slug not in STARTERS:
        abort(404)
    title = STARTERS[slug]['title']
    try:
        add_starter_adventure(current_user.id, slug)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Starter adventure %s failed for user %s', slug, current_user.id)
        flash(_('Could not add %(title)s. Please try again.', title=title), 'error')
        return redirect(url_for('campaigns.index'))
    flash(_('%(title)s was added to your campaigns.', title=title), 'success')
    return redirect(url_for('campaigns.index'))


def hide_campaign_from(campaign, party_id):
    """Hide every article of this campaign from one party: its party versions are deleted. The caller commits."""
    entry_ids = [entry.id for entry in campaign.entries]
    for presentation in PartyPresentation.query.filter(
            PartyPresentation.party_id == party_id, PartyPresentation.entry_id.in_(entry_ids)).all():
        db.session.delete(presentation)


def back_to_party(party):
    """Party notes and party versions live in the party wiki (#440): back there after a change."""
    return redirect(url_for('campaigns.party_wiki', party_id=party.id))


# ----- Party notes: written on the party page, for that party only -----
# Stored as an article of type PARTY_NOTE, unfiled, with one published party
# version holding the same text. Campaigns never lists them (see article()).

def party_note(party, entry_id):
    entry = owned(ContentEntry, entry_id)
    presentation = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party.id).first()
    if entry.category != PARTY_NOTE or presentation is None:
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
    party = party_access(party_id, editing=True)
    entry, presentation = party_note(party, entry_id)
    if request.method == 'POST':
        check_version(entry, request.form.get('version'))
        entry.title = presentation.title = text_value(request.form.get('title'), 200, True)
        entry.body = presentation.body = content_value(request.form.get('body', ''))
        db.session.commit()
        notify_parties([party.id])
        return back_to_party(party)
    return render_template('campaigns/party_note.html', party=party, entry=entry)


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>/version', methods=['GET', 'POST'])
def edit_party_version(party_id, entry_id):
    """Edit what one party sees of a revealed article, from its Wiki tab: saving makes it a party version."""
    party = party_access(party_id, editing=True)
    entry = article(entry_id)
    row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party.id, published=True).first_or_404()
    if request.method == 'POST':
        check_version(row, request.form.get('version'))
        row.title, row.body, row.path_type = revealed_version(entry, request.form, 'custom')
        db.session.commit()
        notify_parties([party.id])
        flash(_('Saved what %(party)s sees.', party=party.name) if (row.title, row.body) != (entry.title, entry.body)
              else _('Saved. The text is the same as your original, so it counts as the original.'), 'success')
        return back_to_party(party)
    return render_template('campaigns/party_version.html', party=party, entry=entry, row=row)


@campaigns.route('/party/<int:party_id>/notes/<int:entry_id>/delete', methods=['POST'])
def delete_party_note(party_id, entry_id):
    party = party_access(party_id, editing=True)
    entry, _presentation = party_note(party, entry_id)
    db.session.delete(entry)
    db.session.commit()
    notify_parties([party.id])
    flash(_('Party note deleted.'), 'success')
    return back_to_party(party)


@campaigns.route('/campaigns/<int:campaign_id>/hide/<int:party_id>', methods=['POST'])
def hide_campaign(campaign_id, party_id):
    """Campaign wiki home: Hide everything from one party."""
    campaign = owned(Campaign, campaign_id)
    party = party_access(party_id, editing=True)
    hide_campaign_from(campaign, party.id)
    db.session.commit()
    notify_parties([party.id])
    flash(_('Everything from %(campaign)s is hidden from %(party)s.', campaign=campaign.name, party=party.name), 'success')
    return redirect(url_for('campaigns.wiki', campaign_id=campaign.id))


@campaigns.route('/campaigns/<int:campaign_id>/', methods=['GET', 'POST'])
def workspace(campaign_id):
    campaign = owned(Campaign, campaign_id)
    if request.method == 'POST':
        check_version(campaign, request.form.get('version'))
        campaign.name = text_value(request.form.get('name'), 200, True)
        campaign.version += 1
        db.session.commit()
        return redirect(url_for('campaigns.workspace', campaign_id=campaign.id))
    entries = library_entries().filter_by(campaign_id=campaign.id).order_by(ContentEntry.id).all()
    audience = campaign_audience(campaign)
    return render_template('campaigns/workspace.html', campaign=campaign, hierarchy=material_hierarchy(entries),
                           audience=[party for party in my_parties() if party.id in audience])


@campaigns.route('/campaigns/<int:campaign_id>/wiki/')
@campaigns.route('/campaigns/<int:campaign_id>/wiki/<int:entry_id>/')
def wiki(campaign_id, entry_id=None):
    """Read the campaign as a wiki; the article editor stays the place to change it."""
    from app.lib.campaign_wiki import page_context
    campaign = owned(Campaign, campaign_id)
    entry = None
    if entry_id is not None:
        entry = article(entry_id)
        if entry.campaign_id != campaign.id:
            abort(404)
    context = page_context(campaign, entry)
    if entry is None:
        # Who has been shown this campaign, and how much: the home page's Hide everything list.
        audience = campaign_audience(campaign)
        counts = {}
        for (party_id,) in db.session.query(PartyPresentation.party_id).join(ContentEntry).filter(
                ContentEntry.campaign_id == campaign.id, PartyPresentation.published.is_(True)):
            counts[party_id] = counts.get(party_id, 0) + 1
        context['audience'] = [(party, counts[party.id]) for party in my_parties() if party.id in audience]
    else:
        context['reveal_parties'] = reveal_choices(entry)
    if entry is not None and entry.pointcrawl:
        context.update(graph=map_projection(entry.pointcrawl), pointcrawl=None, editing=False, party=None,
                       embedded=True, nested_maps=[], locations=[])
    return render_template('campaigns/wiki.html', **context)


@campaigns.route('/materials/wiki/')
@campaigns.route('/materials/wiki/<int:entry_id>/')
def unfiled_wiki(entry_id=None):
    """Read the articles that belong to no campaign, the same way as a campaign."""
    from app.lib.campaign_wiki import page_context
    entry = None
    if entry_id is not None:
        entry = article(entry_id)
        if entry.campaign_id is not None:
            abort(404)
    context = page_context(None, entry, owner_id=current_user.id)
    context['move_campaigns'] = my_campaigns() if entry is not None else []
    if entry is not None:
        context['reveal_parties'] = reveal_choices(entry)
    if entry is not None and entry.pointcrawl:
        context.update(graph=map_projection(entry.pointcrawl), pointcrawl=None, editing=False, party=None,
                       embedded=True, nested_maps=[], locations=[])
    return render_template('campaigns/wiki.html', **context)


@campaigns.route('/campaigns/<int:campaign_id>/export')
def campaign_export(campaign_id):
    campaign = owned(Campaign, campaign_id)
    return send_file(export_campaign(campaign), mimetype='application/zip',
                     as_attachment=True, download_name=f'campaign-{campaign.id}.zip')


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
    db.session.delete(campaign)
    db.session.commit()
    notify_parties(audiences)
    flash(_('%(title)s was removed from your campaigns.', title=title), 'success')
    return redirect(url_for('campaigns.index'))


@campaigns.route('/materials/')
def library():
    entries = library_entries().filter_by(campaign_id=None).order_by(ContentEntry.id).all()
    return render_template('campaigns/workspace.html', campaign=None, hierarchy=material_hierarchy(entries), parties=[], linked=set())


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
    context = party_context(party, entry_id, owner_view=party.owner == current_user.id)
    if context is None:
        abort(404)
    entry = context['entry']
    graph = map_projection(db.get_or_404(PointcrawlMap, entry['map_id']), party.id) if entry['map_id'] else None
    return render_template('campaigns/wiki.html', graph=graph, pointcrawl=None, editing=False, embedded=True,
                           nested_maps=[], locations=[], **context)


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


@campaigns.route('/materials/new', methods=['GET', 'POST'])
def new_entry():
    """A new private article. Parties see it only once it is revealed to them."""
    campaign = campaign_for(request.values.get('campaign_id'))
    if request.method == 'POST':
        category = request.form.get('category')
        if category == 'location':
            from app.lib.content_types import legacy_point_type
            category = legacy_point_type(request.form.get('title'))
        if category not in CATEGORIES or category in ('map', 'overview'):
            abort(400)
        title = text_value(request.form.get('title'), 200, True)
        body = content_value(request.form.get('body', ''))
        entry = ContentEntry(owner_id=current_user.id, campaign=campaign, category=category,
                             title=title, body=body,
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
    return render_template('campaigns/entry.html', entry=None, campaign=campaign,
                           initial_title=request.args.get('title', '')[:200], initial_category=initial_category,
                           campaigns=my_campaigns(), candidates=[], selected_links=set(),
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


@campaigns.route('/materials/<int:entry_id>/move', methods=['POST'])
def move_entry(entry_id):
    """Move to campaign, from the article's reading page."""
    entry = article(entry_id)
    check_version(entry, request.form.get('version'))
    campaign = campaign_for(request.form.get('campaign_id'))
    move_to_campaign(entry, campaign)
    db.session.commit()
    return redirect(url_for('campaigns.wiki', campaign_id=campaign.id, entry_id=entry.id) if campaign
                    else url_for('campaigns.unfiled_wiki', entry_id=entry.id))


@campaigns.route('/materials/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = article(entry_id)
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
        entry.is_heart = entry.category == 'settlement' and request.form.get('is_heart') == 'on'
        if entry.category == 'path':
            kind = request.form.get('path_type')
            if kind not in PATH_TYPES:
                abort(400)
            entry.path_type = kind
        move_to_campaign(entry, campaign_for(request.form.get('campaign_id')))
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
    map_context = {}
    if entry.pointcrawl:
        map_context = dict(pointcrawl=entry.pointcrawl, graph=map_projection(entry.pointcrawl),
            editing=True, embedded=True,
            nested_maps=PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == current_user.id,
                ContentEntry.campaign_id == entry.campaign_id, PointcrawlMap.id != entry.pointcrawl.id).all(),
            locations=ContentEntry.query.filter_by(owner_id=current_user.id,campaign_id=entry.campaign_id)
                .filter(ContentEntry.category.in_(POINT_TYPES)).all())
    return render_template('campaigns/entry.html', **map_context, entry=entry, campaign=entry.campaign, party=None,
                           parent_entries=material_parents(entry), reveal_parties=reveal_choices(entry),
                           campaigns=my_campaigns(), candidates=candidates,
                           selected_links=selected_links, automatic_links=automatic_links,
                           parent_candidates=article_parent_choices(library_entries(), entry), selected_parent=entry.parent_id or '')


@campaigns.route('/materials/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = article(entry_id)
    check_version(entry, request.form.get('version'))
    campaign_id = entry.campaign_id
    delete_material_plan(*material_deletion_plan([entry], current_user.id, campaign_id))
    return redirect(url_for('campaigns.workspace', campaign_id=campaign_id) if campaign_id else url_for('campaigns.library'))


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
    back_url = (url_for('campaigns.workspace', campaign_id=campaign_id)
                if campaign_id else url_for('campaigns.library'))
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
    back_url = url_for('campaigns.workspace', campaign_id=campaign_id) if campaign_id else url_for('campaigns.library')
    if confirmation:
        if snapshot != state:
            abort(409, 'The articles or party versions changed. Review publication again.')
        selected = {integer(value) for value in request.form.getlist('party_ids')}
        if not selected:
            abort(400, 'Choose at least one party.')
        # Several articles: each party sees the originals (party versions are written one article at a time).
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
                row.published = True
                if entry.pointcrawl and request.form.get('publish_drawing') == '1':
                    row.drawing = deepcopy(entry.pointcrawl.drawing)
        db.session.commit()
        notify_parties(selected)
        flash(_('Revealed %(count)s articles.', count=len(entries)), 'success')
        return redirect(back_url)
    return render_template('campaigns/reveal_materials.html', entries=entries, parties=parties,
                           reveal_token=signer.dumps(state), back_url=back_url)


# What a party sees when an article is revealed to it:
#   everything - "Original": the private title and text as they are now,
#   custom     - "Party version": a title and text written for the party (form fields title, body, path_type).
REVEAL_MODES = ('everything', 'custom')


def revealed_version(entry, form, mode=None):
    """(title, body, path_type) for the chosen reveal mode; 400 on an unknown mode or empty title."""
    mode = mode or form.get('mode', 'custom')
    if mode == 'everything':
        return text_value(entry.title, 200, True), entry.body, entry.path_type
    if mode != 'custom':
        abort(400)
    # A party version never inherits the original's private path type unless the Warden picks it.
    kind = form.get('path_type', 'standard')
    if kind not in PATH_TYPES:
        abort(400)
    return text_value(form.get('title'), 200, True), content_value(form.get('body', '')), kind


def reveal_status(entry, row):
    """none (not revealed), same (sees the original as it is now) or custom (sees its own version)."""
    if row is None or not row.published:
        return 'none'
    return 'same' if (row.title, row.body) == (entry.title, entry.body) else 'custom'


def read_url(entry):
    return (url_for('campaigns.wiki', campaign_id=entry.campaign_id, entry_id=entry.id) if entry.campaign_id
            else url_for('campaigns.unfiled_wiki', entry_id=entry.id))


def reveal_choices(entry):
    """The Reveal popup's parties: what each sees now, its version (to edit), and map progress."""
    presentations = {p.party_id: p for p in entry.presentations}
    points = [node.entry for node in entry.pointcrawl.nodes] if entry.pointcrawl else []
    paths = [edge.entry for edge in entry.pointcrawl.edges] if entry.pointcrawl else []

    def revealed(items, party_id):
        return sum(any(p.party_id == party_id and p.published for p in item.presentations) for item in items)

    audience = campaign_audience(entry.campaign)
    choices = []
    for party in available_parties(entry):
        row = presentations.get(party.id)
        choices.append({'id': party.id, 'name': party.name, 'status': reveal_status(entry, row),
                        'version': row.version if row else 0, 'title': row.title if row else '',
                        'body': row.body if row else '', 'path_type': row.path_type if row else entry.path_type,
                        'points': revealed(points, party.id), 'paths': revealed(paths, party.id),
                        'seen': party.id in audience})
    return choices


def after_reveal(entry, party_id):
    """Back where the action started: the article (default) or the party wiki ('party' is its old name)."""
    if request.values.get('return_to') in ('wiki', 'party'):
        return redirect(url_for('campaigns.party_wiki', party_id=party_id))
    return redirect(read_url(entry))


@campaigns.route('/materials/<int:entry_id>/reveal', methods=['GET', 'POST'])
def reveal(entry_id):
    """Reveal one article to one party: the original, or a version written for them.

    GET shows the same form as the article page's Reveal popup, as a page (the party tree links here)."""
    entry = article(entry_id)
    if request.method == 'POST':
        party_id = integer(request.form.get('party_ids'))
        party = publishable_party(entry, party_id)
        row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party.id).first()
        check_version(row, request.form.get(f'version_{party.id}'))
        publish_drawing = entry.pointcrawl and request.form.get('publish_drawing') == '1'
        if publish_drawing:
            check_version(entry.pointcrawl, request.form.get('map_version'))
        title, body, kind = revealed_version(entry, request.form)
        if row is None:
            row = PartyPresentation(entry=entry, party=party)
            db.session.add(row)
        row.title, row.body, row.path_type, row.published = title, body, kind, True
        if publish_drawing:
            row.drawing = deepcopy(entry.pointcrawl.drawing)
        db.session.commit()
        notify_parties([party.id])
        if request.form.get('mode') == 'custom' and (title, body) == (entry.title, entry.body):
            # Party versions are told apart from the original by their text alone.
            flash(_('Revealed to %(party)s. The text is the same as your original, so it counts as the original '
                    'until you change it.', party=party.name), 'success')
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
            claimed = CampaignImport.query.filter_by(id=batch.id, owner_id=current_user.id, consumed=False).filter(
                CampaignImport.created_at >= cutoff).update({'consumed': True}, synchronize_session=False)
            if not claimed:
                abort(409, 'This preview was already imported.')
            import_preview(payload, current_user.id)
            batch.payload = {}
            db.session.commit()
            return redirect(url_for('campaigns.index'))
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
        if preview and not preview['errors']:
            preview_id = uuid4().hex
            # Keep staging bounded; expired previews never contain library records.
            CampaignImport.query.filter(CampaignImport.created_at < cutoff).delete(synchronize_session=False)
            CampaignImport.query.filter_by(owner_id=current_user.id, consumed=False).delete(synchronize_session=False)
            db.session.add(CampaignImport(id=preview_id, owner_id=current_user.id, payload=preview))
            db.session.commit()
    return render_template('campaigns/import_archive.html', preview=preview, preview_id=preview_id, message=message)


@campaigns.route('/materials/import-example.zip')
def import_example():
    import io
    import zipfile
    from pathlib import Path

    stream = io.BytesIO()
    examples = Path(current_app.static_folder) / 'examples' / 'campaign-import'
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(examples.glob('*.md')):
            archive.writestr(path.name, path.read_bytes())
    stream.seek(0)
    return send_file(stream, mimetype='application/zip', as_attachment=True,
                     download_name='campaign-example.zip')


@campaigns.route('/materials/<int:entry_id>/revoke/<int:party_id>', methods=['POST'])
def revoke(entry_id, party_id):
    """Hide (an original) or Delete (a party version) for one party: its copy is deleted either way.
    Revealing again starts from the original."""
    entry = article(entry_id)
    party = party_access(party_id, editing=True)
    row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party_id).first_or_404()
    check_version(row, request.form.get('version'))
    was_version = (row.title, row.body) != (entry.title, entry.body)
    db.session.delete(row)
    db.session.commit()
    notify_parties([party_id])
    flash(_('Deleted the party version for %(party)s.', party=party.name) if was_version
          else _('Hidden from %(party)s.', party=party.name), 'success')
    return after_reveal(entry, party_id)


@campaigns.route('/materials/<int:entry_id>/map', methods=['POST'])
def article_map(entry_id):
    entry = article(entry_id)
    check_version(entry, request.form.get('version'))
    if entry.category not in ARTICLE_MAP_KINDS and not entry.pointcrawl:
        abort(400, 'This article type does not have a map.')
    ensure_article_tree_maps(entry)
    db.session.commit()
    return entry_redirect(entry)


def create_map_entry(campaign, kind, title, body, draft):
    """Create a private spatial article and its canvas, optionally from a generated draft.

    The caller validates kind and commits. Reveal it to parties afterwards, like any article.
    """
    entry = ContentEntry(owner_id=current_user.id, campaign=campaign, category=kind if kind != 'freeform' else 'topography',
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
    campaign = campaign_for(request.form.get('campaign_id', request.args.get('campaign_id')))
    if request.method == 'POST':
        kind = request.form.get('kind')
        if kind not in MAP_KINDS:
            abort(400)
        pointcrawl = create_map_entry(campaign, kind, request.form.get('title'),
                                      request.form.get('body', ''), request.form.get('draft'))
        db.session.commit()
        return entry_redirect(pointcrawl.entry)
    kind = request.args.get('kind', 'realm')
    if kind not in MAP_KINDS:
        abort(400)
    return render_template('campaigns/new_map.html', campaign=campaign, campaigns=my_campaigns(), kind=kind)


@campaigns.route('/maps/<int:map_id>/edit')
def map_edit(map_id):
    pointcrawl = owned(PointcrawlMap, map_id)
    return entry_redirect(pointcrawl.entry)


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
        audiences = entry_audiences(pointcrawl.entry)
        db.session.commit()
        notify_parties(audiences)
    return jsonify(map_projection(pointcrawl))


@campaigns.route('/party/<int:party_id>/maps/<int:map_id>/')
def party_map(party_id, map_id):
    party = party_access(party_id)
    pointcrawl = db.get_or_404(PointcrawlMap, map_id)
    map_projection(pointcrawl, party.id)  # Authorize the legacy URL before redirecting.
    return redirect(url_for('campaigns.party_entry', party_id=party.id, entry_id=pointcrawl.entry_id))


@campaigns.route('/party/<int:party_id>/maps/<int:map_id>/data')
def party_map_data(party_id, map_id):
    party_access(party_id)
    return jsonify(map_projection(db.get_or_404(PointcrawlMap, map_id), party_id))


@campaigns.route('/materials/import')
def import_result():
    return render_template('campaigns/import.html', campaigns=my_campaigns())


@campaigns.route('/articles/tables')
@campaigns.route('/maps/tables')
def map_tables():
    import json
    from pathlib import Path
    data = {}
    folder = Path(__file__).resolve().parents[1] / 'static' / 'json' / 'generators'
    for name in ('dungeons', 'forests', 'realm', 'factions', 'npcs', 'names', 'bestiary',
                 'custom-monster', 'reliquary', 'spellbooks', 'dungeon-events', 'wilderness-events'):
        data.update(json.loads((folder / f'{name}.json').read_text()))
    data['Equipment'] = json.loads((folder.parent / 'marketplace.json').read_text())
    if request.path == '/maps/tables':
        data = {key: data[key] for key in ('Dungeon', 'Forest', 'Realm', 'NPCGenerator', 'Names')}
    from app.main import translate_events_data
    return jsonify(translate_events_data(data))


@campaigns.get('/material-images/<int:owner_id>/<filename>')
def material_image(owner_id, filename):
    url = f'/material-images/{owner_id}/{filename}'
    if not LOCAL_IMAGE.fullmatch(url):
        abort(404)
    originals = ContentEntry.query.filter_by(owner_id=owner_id).filter(ContentEntry.body.contains(url)).all()
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

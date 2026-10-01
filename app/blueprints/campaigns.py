"""Campaign workspaces, party knowledge, and pointcrawl editing."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import selectinload

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap, CampaignImport)
from app.lib.campaign_import import preview_archive, import_preview, ImportError, MAX_ARCHIVE
from app.lib.campaigns import (CATEGORIES, MAP_KINDS, PATH_TYPES, campaign_for, check_version,
    entry_audiences, integer, known_entries, map_projection, map_related_ids, notify_parties, owned,
    party_access, publishable_party, render_content, save_geometry, text_value, content_value,
    material_hierarchy, material_parents, material_deletion_plan, delete_material_plan)
from app.lib.rich_content import content_excerpt
from app.lib.material_images import LOCAL_IMAGE, image_directory, cleanup_images, image_references
from app.lib.feature_access import user_features_enabled, party_features_enabled

campaigns = Blueprint('campaigns', __name__)


@campaigns.before_request
@login_required
def authorize():
    # Party readers and images have their own audience checks below. All private
    # authoring routes require the user allowlist, including direct POST requests.
    if request.endpoint not in {
        'campaigns.party_materials', 'campaigns.party_materials_data',
        'campaigns.party_entry', 'campaigns.party_map', 'campaigns.party_map_data',
        'campaigns.material_image',
    } and not user_features_enabled():
        abort(404)
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
    return {'content_categories': CATEGORIES, 'path_types': PATH_TYPES,
            'content_form': FlaskForm(), 'render_content': render_content, 'content_excerpt': content_excerpt}


def my_parties():
    query = Party.query.filter_by(owner=current_user.id)
    if not current_app.config.get('LOCAL_FEATURE_ACCESS', False):
        query = query.filter(Party.id.in_(current_app.config.get('FEATURE_TEST_PARTY_IDS', ())))
    return query.order_by(Party.name).all()


def my_campaigns():
    return Campaign.query.filter_by(owner_id=current_user.id).options(
        selectinload(Campaign.parties).selectinload(CampaignParty.party),
        selectinload(Campaign.entries)).order_by(Campaign.name).all()


def library_entries():
    return ContentEntry.query.filter_by(owner_id=current_user.id).options(
        selectinload(ContentEntry.pointcrawl), selectinload(ContentEntry.presentations))


def available_parties(entry):
    parties = my_parties()
    if entry.campaign_id:
        ids = {p.party_id for p in entry.campaign.parties}
        parties = [p for p in parties if p.id in ids]
    return parties


def entry_redirect(entry):
    return redirect(url_for('campaigns.edit_entry', entry_id=entry.id))


@campaigns.route('/campaigns/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        campaign = Campaign(owner_id=current_user.id, name=text_value(request.form.get('name'), 200, True))
        db.session.add(campaign)
        db.session.commit()
        return redirect(url_for('campaigns.workspace', campaign_id=campaign.id))
    campaigns_list = my_campaigns()
    entries = library_entries().order_by(ContentEntry.title).all()
    return render_template('campaigns/index.html', campaigns=campaigns_list,
        trees={campaign.id: material_hierarchy([e for e in entries if e.campaign_id == campaign.id]) for campaign in campaigns_list},
        unfiled=material_hierarchy([e for e in entries if e.campaign_id is None]))


@campaigns.route('/campaigns/<int:campaign_id>/', methods=['GET', 'POST'])
def workspace(campaign_id):
    campaign = owned(Campaign, campaign_id)
    if request.method == 'POST':
        check_version(campaign, request.form.get('version'))
        campaign.name = text_value(request.form.get('name'), 200, True)
        selected = {integer(value) for value in request.form.getlist('party_ids')}
        for party_id in selected:
            party_access(party_id, editing=True)
        old = {link.party_id: link for link in campaign.parties}
        # Hidden rollout audiences are not unchecked form fields. Preserve their
        # links/publications so disabling and later re-enabling loses no data.
        selected.update(party_id for party_id in old if not party_features_enabled(party_id))
        # Unlinking a party revokes this campaign's publications, never deletes originals.
        removed = set(old) - selected
        entry_ids = [entry.id for entry in campaign.entries]
        for presentation in PartyPresentation.query.filter(
                PartyPresentation.party_id.in_(removed), PartyPresentation.entry_id.in_(entry_ids)).all():
            presentation.published = False
        for party_id in removed:
            db.session.delete(old[party_id])
        for party_id in selected - set(old):
            campaign.parties.append(CampaignParty(party_id=party_id))
        campaign.version += 1
        db.session.commit()
        notify_parties(removed)
        return redirect(url_for('campaigns.workspace', campaign_id=campaign.id))
    entries = library_entries().filter_by(campaign_id=campaign.id).order_by(ContentEntry.id).all()
    return render_template('campaigns/workspace.html', campaign=campaign, hierarchy=material_hierarchy(entries),
                           parties=my_parties(), linked={p.party_id for p in campaign.parties})


@campaigns.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = owned(Campaign, campaign_id)
    check_version(campaign, request.form.get('version'))
    # Delete owned contents through the ORM so maps, geometry, links and party
    # presentations are removed together. Related materials outside this campaign
    # and the connected parties themselves remain independent.
    audiences = {link.party_id for link in campaign.parties}
    for entry in list(campaign.entries):
        audiences.update(presentation.party_id for presentation in entry.presentations)
        db.session.delete(entry)
    db.session.delete(campaign)
    db.session.commit()
    notify_parties(audiences)
    return redirect(url_for('campaigns.index'))


@campaigns.route('/materials/')
def library():
    entries = library_entries().filter_by(campaign_id=None).order_by(ContentEntry.id).all()
    return render_template('campaigns/workspace.html', campaign=None, hierarchy=material_hierarchy(entries), parties=[], linked=set())


@campaigns.route('/party/<int:party_id>/materials/')
def party_materials(party_id):
    party = party_access(party_id)
    preview = request.args.get('preview') == '1'
    return render_template('campaigns/party.html', party=party,
        entries=[entry for entry in known_entries(party.id).values() if entry['category'] != 'path'],
        editing=party.owner == current_user.id and user_features_enabled() and not preview, preview=preview)


@campaigns.route('/party/<int:party_id>/materials/data')
def party_materials_data(party_id):
    party_access(party_id)
    return jsonify(entries=[entry for entry in known_entries(party_id).values() if entry['category'] != 'path'])


@campaigns.route('/party/<int:party_id>/materials/<int:entry_id>')
def party_entry(party_id, entry_id):
    party = party_access(party_id)
    entry = known_entries(party_id).get(entry_id)
    if entry is None:
        abort(404)
    return render_template('campaigns/known_entry.html', party=party, entry=entry)


@campaigns.route('/materials/new', methods=['GET', 'POST'])
def new_entry():
    campaign = campaign_for(request.values.get('campaign_id'))
    party_id = request.values.get('party_id')
    party = party_access(integer(party_id), editing=True) if party_id else None
    if request.method == 'POST':
        category = request.form.get('category')
        if category not in CATEGORIES or category == 'map':
            abort(400)
        title = text_value(request.form.get('title'), 200, True)
        body = content_value(request.form.get('body', ''))
        entry = ContentEntry(owner_id=current_user.id, campaign=campaign, category=category,
                             title='' if party else title, body='' if party else body)
        db.session.add(entry)
        if party:
            if campaign and not db.session.get(CampaignParty, (campaign.id, party.id)):
                abort(400)
            entry.presentations.append(PartyPresentation(party=party, title=title, body=body))
        db.session.commit()
        if party:
            notify_parties([party.id])
            return redirect(url_for('campaigns.party_materials', party_id=party.id))
        return entry_redirect(entry)
    return render_template('campaigns/entry.html', entry=None, campaign=campaign, party=party,
                           campaigns=my_campaigns(), candidates=[], selected_links=set())


@campaigns.route('/materials/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = owned(ContentEntry, entry_id)
    if request.method == 'POST':
        check_version(entry, request.form.get('version'))
        entry.title = text_value(request.form.get('title', ''), 200)
        entry.body = content_value(request.form.get('body', ''))
        if entry.category not in ('map', 'path'):
            category = request.form.get('category')
            if category not in CATEGORIES or category == 'map':
                abort(400)
            if entry.map_nodes and category != 'location':
                abort(400, 'A location used on a map must remain a location.')
            entry.category = category
        if entry.category == 'path':
            kind = request.form.get('path_type')
            if kind not in PATH_TYPES:
                abort(400)
            entry.path_type = kind
        campaign = campaign_for(request.form.get('campaign_id'))
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
                if campaign:
                    for presentation in item.presentations:
                        if presentation.party_id not in {link.party_id for link in campaign.parties}:
                            campaign.parties.append(CampaignParty(party_id=presentation.party_id))
        targets = {integer(value) for value in request.form.getlist('links')} - map_related_ids(entry)
        if entry.id in targets:
            abort(400)
        for target_id in targets:
            owned(ContentEntry, target_id)
        old_links = {link.target_id: link for link in entry.links}
        for target_id in set(old_links) - targets:
            db.session.delete(old_links[target_id])
        for target_id in targets - set(old_links):
            entry.links.append(ContentLink(target_id=target_id))
        entry.version += 1
        audiences = entry_audiences(entry)
        db.session.commit()
        notify_parties(audiences)
        return entry_redirect(entry)
    candidates = ContentEntry.query.filter(ContentEntry.owner_id == current_user.id,
        ContentEntry.id != entry.id, ContentEntry.category != 'path').order_by(ContentEntry.id).all()
    automatic_links = map_related_ids(entry)
    selected_links = {link.target_id for link in entry.links}
    candidates.sort(key=lambda item: (item.id not in automatic_links | selected_links, item.id))
    return render_template('campaigns/entry.html', entry=entry, campaign=entry.campaign, party=None,
                           parent_entries=material_parents(entry),
                           campaigns=my_campaigns(), candidates=candidates,
                           selected_links=selected_links, automatic_links=automatic_links)


@campaigns.route('/materials/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = owned(ContentEntry, entry_id)
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
    selected = [owned(ContentEntry, entry_id) for entry_id in selected_ids]
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


@campaigns.route('/materials/<int:entry_id>/reveal', methods=['GET', 'POST'])
def reveal(entry_id):
    entry = owned(ContentEntry, entry_id)
    presentations = {p.party_id: p for p in entry.presentations}
    if request.method == 'POST':
        publish_drawing = entry.pointcrawl and request.form.get('publish_drawing') == '1'
        if publish_drawing:
            check_version(entry.pointcrawl, request.form.get('map_version'))
        selected = {integer(value) for value in request.form.getlist('party_ids')}
        if not selected:
            abort(400, 'Choose at least one party.')
        for party_id in selected:
            party = publishable_party(entry, party_id)
            row = presentations.get(party_id)
            check_version(row, request.form.get(f'version_{party_id}'))
            title = text_value(request.form.get(f'title_{party_id}'), 200, True)
            body = content_value(request.form.get(f'body_{party_id}', ''))
            kind = request.form.get(f'path_type_{party_id}', 'standard')
            if kind not in PATH_TYPES:
                abort(400)
            if row is None:
                row = PartyPresentation(entry=entry, party=party)
                db.session.add(row)
            row.title, row.body, row.path_type, row.published = title, body, kind, True
            if publish_drawing:
                row.drawing = deepcopy(entry.pointcrawl.drawing)
        db.session.commit()
        notify_parties(selected)
        flash(_('Published to the selected parties. Use View as party below to see the saved version.'))
        return redirect(url_for('campaigns.reveal', entry_id=entry.id))
    return render_template('campaigns/reveal.html', entry=entry, parties=available_parties(entry),
        presentations=presentations, initial=[{'id': p.id, 'name': p.name, 'selected': False,
            'version': presentations[p.id].version if p.id in presentations else 0,
            'published': presentations[p.id].published if p.id in presentations else False,
            'title': presentations[p.id].title if p.id in presentations else entry.title,
            'body': presentations[p.id].body if p.id in presentations else '',
            'path_type': presentations[p.id].path_type if p.id in presentations else 'standard'}
            for p in available_parties(entry)])


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
            claimed = CampaignImport.query.filter_by(id=batch.id, owner_id=current_user.id, consumed=False).filter(
                CampaignImport.created_at >= cutoff).update({'consumed': True}, synchronize_session=False)
            if not claimed:
                abort(409, 'This preview was already imported.')
            import_preview(batch.payload, current_user.id)
            batch.payload = {}
            db.session.commit()
            return redirect(url_for('campaigns.index'))
        upload = request.files.get('archive')
        if not upload:
            message = _('Choose a ZIP or TAR archive.')
        else:
            try:
                preview = preview_archive(upload.stream.read(MAX_ARCHIVE + 1))
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


@campaigns.route('/materials/<int:entry_id>/revoke/<int:party_id>', methods=['POST'])
def revoke(entry_id, party_id):
    entry = owned(ContentEntry, entry_id)
    party_access(party_id, editing=True)
    row = PartyPresentation.query.filter_by(entry_id=entry.id, party_id=party_id).first_or_404()
    check_version(row, request.form.get('version'))
    row.published = False
    db.session.commit()
    notify_parties([party_id])
    return redirect(url_for('campaigns.reveal', entry_id=entry.id))


@campaigns.route('/maps/new', methods=['GET', 'POST'])
def new_map():
    campaign = campaign_for(request.form.get('campaign_id', request.args.get('campaign_id')))
    party_id = request.values.get('party_id')
    party = party_access(integer(party_id), editing=True) if party_id else None
    if party and campaign and not db.session.get(CampaignParty, (campaign.id, party.id)):
        abort(400, 'Connect this party to the campaign first.')
    if request.method == 'POST':
        kind = request.form.get('kind')
        if kind not in MAP_KINDS:
            abort(400)
        entry = ContentEntry(owner_id=current_user.id, campaign=campaign, category='map',
                             title=text_value(request.form.get('title'), 200, True),
                             body=content_value(request.form.get('body', '')))
        pointcrawl = PointcrawlMap(entry=entry, kind=kind)
        db.session.add(pointcrawl)
        db.session.flush()
        draft = request.form.get('draft')
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
        if party:
            entries = {pointcrawl.entry, *(node.entry for node in pointcrawl.nodes),
                       *(edge.entry for edge in pointcrawl.edges)}
            for entry in entries:
                entry.presentations.append(PartyPresentation(party_id=party.id,
                    title=entry.title, body=entry.body, path_type=entry.path_type,
                    drawing=deepcopy(pointcrawl.drawing) if entry == pointcrawl.entry else None))
        db.session.commit()
        if party:
            notify_parties([party.id])
            return redirect(url_for('campaigns.party_map', party_id=party.id, map_id=pointcrawl.id))
        return redirect(url_for('campaigns.map_edit', map_id=pointcrawl.id))
    kind = request.args.get('kind', 'realm')
    if kind not in MAP_KINDS:
        abort(400)
    return render_template('campaigns/new_map.html', campaign=campaign, campaigns=my_campaigns(), party=party, kind=kind)


@campaigns.route('/maps/<int:map_id>/edit')
def map_edit(map_id):
    pointcrawl = owned(PointcrawlMap, map_id)
    candidates = PointcrawlMap.query.join(ContentEntry).filter(ContentEntry.owner_id == current_user.id,
        ContentEntry.campaign_id == pointcrawl.entry.campaign_id, PointcrawlMap.id != map_id).all()
    locations = ContentEntry.query.filter_by(owner_id=current_user.id,
        campaign_id=pointcrawl.entry.campaign_id, category='location').all()
    return render_template('campaigns/map.html', pointcrawl=pointcrawl, graph=map_projection(pointcrawl),
        parent_entries=material_parents(pointcrawl.entry), campaign=pointcrawl.entry.campaign,
        editing=True, party=None, nested_maps=candidates, locations=locations)


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
    graph = map_projection(pointcrawl, party.id)
    return render_template('campaigns/map.html', graph=graph, pointcrawl=None, editing=False,
                           party=party, nested_maps=[], locations=[])


@campaigns.route('/party/<int:party_id>/maps/<int:map_id>/data')
def party_map_data(party_id, map_id):
    party_access(party_id)
    return jsonify(map_projection(db.get_or_404(PointcrawlMap, map_id), party_id))


@campaigns.route('/materials/import')
def import_result():
    return render_template('campaigns/import.html', campaigns=my_campaigns(), parties=my_parties())


@campaigns.route('/articles/tables')
@campaigns.route('/maps/tables')
def map_tables():
    import json
    from pathlib import Path
    data = {}
    folder = Path(__file__).resolve().parents[1] / 'static' / 'json' / 'generators'
    for name in ('dungeons', 'forests', 'realm', 'factions', 'npcs', 'bestiary',
                 'custom-monster', 'reliquary', 'spellbooks', 'dungeon-events', 'wilderness-events'):
        data.update(json.loads((folder / f'{name}.json').read_text()))
    data['Equipment'] = json.loads((folder.parent / 'marketplace.json').read_text())
    if request.path == '/maps/tables':
        data = {key: data[key] for key in ('Dungeon', 'Forest', 'Realm')}
    return jsonify(data)


@campaigns.get('/material-images/<int:owner_id>/<filename>')
def material_image(owner_id, filename):
    url = f'/material-images/{owner_id}/{filename}'
    if not LOCAL_IMAGE.fullmatch(url):
        abort(404)
    originals = ContentEntry.query.filter_by(owner_id=owner_id).filter(ContentEntry.body.contains(url)).all()
    versions = PartyPresentation.query.join(ContentEntry).filter(
        ContentEntry.owner_id == owner_id, PartyPresentation.body.contains(url)).all()
    allowed = user_features_enabled() and current_user.id == owner_id and bool(originals or versions)
    if not allowed:
        from app.socket_events import party_recipient_ids
        for row in versions:
            if (party_features_enabled(row.party_id) and row.published and current_user.id in party_recipient_ids(row.party)
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

"""Campaign workspaces, party knowledge, and pointcrawl editing."""
from copy import deepcopy
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, url_for, send_from_directory
from itsdangerous import BadSignature, URLSafeTimedSerializer
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap)
from app.lib.campaigns import (CATEGORIES, MAP_KINDS, PATH_TYPES, campaign_for, check_version,
    entry_audiences, integer, known_entries, map_projection, map_related_ids, notify_parties, owned,
    party_access, publishable_party, render_content, save_geometry, text_value, content_value,
    material_hierarchy, material_parents, material_deletion_plan, delete_material_plan)
from app.lib.rich_content import content_excerpt
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
    return Party.query.filter_by(owner=current_user.id).order_by(Party.name).all()


def my_campaigns():
    return Campaign.query.filter_by(owner_id=current_user.id).order_by(Campaign.name).all()


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
    return render_template('campaigns/index.html', campaigns=my_campaigns())


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
    entries = ContentEntry.query.filter_by(owner_id=current_user.id, campaign_id=campaign.id).order_by(ContentEntry.id).all()
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
    entries = ContentEntry.query.filter_by(owner_id=current_user.id, campaign_id=None).order_by(ContentEntry.id).all()
    return render_template('campaigns/workspace.html', campaign=None, hierarchy=material_hierarchy(entries), parties=[], linked=set())


@campaigns.route('/party/<int:party_id>/materials/')
def party_materials(party_id):
    party = party_access(party_id)
    preview = request.args.get('preview') == '1'
    return render_template('campaigns/party.html', party=party,
        entries=[entry for entry in known_entries(party.id).values() if entry['category'] != 'path'],
        editing=party.owner == current_user.id and not preview, preview=preview)


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
            moved_ids = {item.id for item in moved}
            for item in moved:
                if any(node.map.entry_id not in moved_ids and node.map.entry.campaign_id != campaign_id for node in item.map_nodes):
                    abort(400, 'Move this location together with its map.')
                if item.category == 'path' and any(edge.map.entry_id not in moved_ids for edge in item.map_edges):
                    abort(400, 'Move this path together with its map.')
            if entry.pointcrawl and any(n.map.entry.campaign_id != campaign_id for n in entry.pointcrawl.entrances):
                abort(400, 'Unlink entrances from other maps before moving this map.')
            if entry.pointcrawl and any(n.nested_map and n.nested_map.entry.campaign_id != campaign_id for n in entry.pointcrawl.nodes):
                abort(400, 'Unlink nested maps before moving this map to another campaign.')
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
        return redirect(url_for('campaigns.reveal', entry_id=entry.id))
    return render_template('campaigns/reveal.html', entry=entry, parties=available_parties(entry),
        presentations=presentations, initial=[{'id': p.id, 'name': p.name, 'selected': False,
            'version': presentations[p.id].version if p.id in presentations else 0,
            'published': presentations[p.id].published if p.id in presentations else False,
            'title': presentations[p.id].title if p.id in presentations else '',
            'body': presentations[p.id].body if p.id in presentations else '',
            'path_type': presentations[p.id].path_type if p.id in presentations else 'standard'}
            for p in available_parties(entry)])


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
    return render_template('campaigns/new_map.html', campaign=campaign, campaigns=my_campaigns(), party=party)


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


@campaigns.route('/maps/tables')
def map_tables():
    import json
    from pathlib import Path
    data = {}
    folder = Path(__file__).resolve().parents[1] / 'static' / 'json' / 'generators'
    for name in ('dungeons', 'forests', 'realm'):
        data.update(json.loads((folder / f'{name}.json').read_text()))
    return jsonify(data)


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

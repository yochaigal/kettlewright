"""Campaign workspaces, party knowledge, and pointcrawl editing."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from app.models import (db, Campaign, CampaignParty, ContentEntry, ContentLink,
                        Party, PartyPresentation, PointcrawlMap)
from app.lib.campaigns import (CATEGORIES, MAP_KINDS, PATH_TYPES, campaign_for, check_version,
    entry_audiences, integer, known_entries, map_projection, notify_parties, owned,
    party_access, publishable_party, render_content, save_geometry, text_value)

campaigns = Blueprint('campaigns', __name__)


@campaigns.before_request
@login_required
def authorize():
    # Validate the whole operation before flushing partial edits or advancing versions.
    db.session.autoflush = False
    if request.method == 'POST' and not FlaskForm().validate_on_submit():
        abort(400, 'Invalid CSRF token.')


@campaigns.after_request
def private_response(response):
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
            'content_form': FlaskForm(), 'render_content': render_content}


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
    return render_template('campaigns/workspace.html', campaign=campaign, entries=entries,
                           parties=my_parties(), linked={p.party_id for p in campaign.parties})


@campaigns.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = owned(Campaign, campaign_id)
    check_version(campaign, request.form.get('version'))
    # Retain materials and party knowledge as standalone content.
    db.session.delete(campaign)
    db.session.commit()
    return redirect(url_for('campaigns.index'))


@campaigns.route('/materials/')
def library():
    entries = ContentEntry.query.filter_by(owner_id=current_user.id, campaign_id=None).order_by(ContentEntry.id).all()
    return render_template('campaigns/workspace.html', campaign=None, entries=entries, parties=[], linked=set())


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
        body = text_value(request.form.get('body', ''))
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
        entry.body = text_value(request.form.get('body', ''))
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
        targets = {integer(value) for value in request.form.getlist('links')}
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
    return render_template('campaigns/entry.html', entry=entry, campaign=entry.campaign, party=None,
                           campaigns=my_campaigns(), candidates=candidates,
                           selected_links={link.target_id for link in entry.links})


@campaigns.route('/materials/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = owned(ContentEntry, entry_id)
    check_version(entry, request.form.get('version'))
    audiences = entry_audiences(entry)
    campaign_id = entry.campaign_id
    affected_maps = {node.map for node in entry.map_nodes} | {edge.map for edge in entry.map_edges}
    paths = {edge.entry for node in entry.map_nodes for edge in list(node.outgoing) + list(node.incoming)}
    if entry.pointcrawl:
        paths.update(edge.entry for edge in entry.pointcrawl.edges)
    for pointcrawl in affected_maps:
        pointcrawl.version += 1
        audiences.update(entry_audiences(pointcrawl.entry))
    for path in paths:
        db.session.delete(path)
    db.session.delete(entry)
    db.session.commit()
    notify_parties(audiences)
    return redirect(url_for('campaigns.workspace', campaign_id=campaign_id) if campaign_id else url_for('campaigns.library'))


@campaigns.route('/materials/<int:entry_id>/reveal', methods=['GET', 'POST'])
def reveal(entry_id):
    entry = owned(ContentEntry, entry_id)
    presentations = {p.party_id: p for p in entry.presentations}
    if request.method == 'POST':
        selected = {integer(value) for value in request.form.getlist('party_ids')}
        if not selected:
            abort(400, 'Choose at least one party.')
        for party_id in selected:
            party = publishable_party(entry, party_id)
            row = presentations.get(party_id)
            check_version(row, request.form.get(f'version_{party_id}'))
            title = text_value(request.form.get(f'title_{party_id}'), 200, True)
            body = text_value(request.form.get(f'body_{party_id}', ''))
            kind = request.form.get(f'path_type_{party_id}', 'standard')
            if kind not in PATH_TYPES:
                abort(400)
            if row is None:
                row = PartyPresentation(entry=entry, party=party)
                db.session.add(row)
            row.title, row.body, row.path_type, row.published = title, body, kind, True
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
    campaign = campaign_for(request.values.get('campaign_id'))
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
                             body=text_value(request.form.get('body', '')))
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
                    title=entry.title, body=entry.body, path_type=entry.path_type))
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

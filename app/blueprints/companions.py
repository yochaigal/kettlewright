"""Pets and hirelings have distinct entry points and shared small-sheet controls."""
import json
import uuid
from flask import Blueprint, abort, redirect, render_template, request, url_for, make_response
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from app.models import db, Character, Party, Companion
from app.lib.companions import STATS, can_manage, can_roll, companion_party, catalog, import_pet, new_hireling, party_member, pet_data, companion_destinations, record_transfer, finish_companion_transfers
from app.lib.inventory import Inventory
from app.lib.data import sanitize_json_content
from app.lib.quick_stats import save_current_stat

companions = Blueprint('companions', __name__)


@companions.app_context_processor
def helpers():
    return dict(can_manage_companion=can_manage, companion_form=FlaskForm, companion_stats=STATS,
                is_party_member=party_member, companion_destinations=companion_destinations)


def csrf():
    if not FlaskForm().validate_on_submit():
        abort(400)


def number(field, maximum=100000, optional=False):
    value = request.form.get(field, '').strip()
    if optional and value == '':
        return None
    try:
        result = int(value)
    except (ValueError, TypeError):
        abort(400, description='Enter a whole number.')
    if not 0 <= result <= maximum:
        abort(400, description='Number is outside the allowed range.')
    return result


def text(field, limit, required=False):
    result = request.form.get(field, '').strip()
    if len(result) > limit or (required and not result):
        abort(400, description='Missing or overly long text.')
    return result


def editable(companion_id):
    c = db.get_or_404(Companion, companion_id)
    if not can_manage(c):
        abort(403)
    return c


def parent_url(c):
    if c.character:
        return url_for('main.character', username=c.character.owner_username, url_name=c.character.url_name)
    if c.hireling:
        return url_for('companions.sheet', companion_id=c.hireling_id)
    return url_for('party.party_view', ownername=c.party.owner_username, party_url=c.party.party_url)


def inventories(c, incoming=False):
    """Only offer real party members; receiving requires control of the source."""
    result = {}
    character = c.character
    hireling = c if c.kind == 'hireling' else c.hireling
    party = hireling.party if hireling else db.session.get(Party, character.party_id) if character.party_id else None
    if character and (not incoming or character.owner == current_user.id):
        result['character:'+str(character.id)] = character
    if party and party_member(party):
        result['party:'+str(party.id)] = party
        for member in Character.query.filter(Character.party_id == party.id, Character.id.in_(json.loads(party.members or '[]'))):
            if not incoming or member.owner == current_user.id or party.owner == current_user.id:
                result['character:'+str(member.id)] = member
        for member in party.hirelings:
            if member.id != c.id and (not incoming or can_manage(member)):
                result['companion:'+str(member.id)] = member
    return result


@companions.route('/characters/<int:character_id>/pets/add', methods=['GET', 'POST'])
@login_required
def add_pet(character_id):
    parent = db.get_or_404(Character, character_id)
    if parent.owner != current_user.id:
        abort(403)
    if request.method == 'POST':
        csrf()
        key = request.form.get('template')
        template = catalog('pet').get(key) if key != 'Custom' else dict(name=text('name',100,True))
        if template is None:
            abort(400)
        pet = import_pet(pet_data(template, parent))
        if request.form.get('name', '').strip():
            pet.name = text('name',100,True)
        parent.pets.append(pet)
        db.session.commit()
        return redirect(url_for('companions.sheet', companion_id=pet.id))
    return render_template('main/companion_add.html', kind='pet', parent=parent, templates=catalog('pet'), form=FlaskForm())


@companions.route('/parties/<int:party_id>/hirelings/add', methods=['GET', 'POST'])
@login_required
def add_hireling(party_id):
    party = db.get_or_404(Party, party_id)
    if party.owner != current_user.id:
        abort(403)
    if request.method == 'POST':
        csrf()
        try:
            c = new_hireling(party, request.form.get('template'))
        except ValueError:
            abort(400)
        if request.form.get('name', '').strip():
            c.name = text('name',100,True)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('companions.sheet', companion_id=c.id))
    return render_template('main/companion_add.html', kind='hireling', parent=party, templates=catalog('hireling'), form=FlaskForm())


@companions.route('/companions/<int:companion_id>', methods=['GET', 'POST'])
@login_required
def sheet(companion_id):
    c = db.get_or_404(Companion, companion_id)
    # Pets have the same visibility as their character; party sheets require membership.
    if c.kind == 'hireling' and not party_member(c.party):
        abort(403)
    if c.hireling and not party_member(c.hireling.party):
        abort(403)
    if request.method == 'POST':
        editable(c.id)
        csrf()
        for field, limit in (('name',100),('role',100),('attack',200),('notes',10000)):
            if field == 'role' and field not in request.form:
                continue
            setattr(c, field, text(field,limit,field=='name'))
        for stat in STATS:
            value, maximum = number(stat, optional=True), number(stat+'_max', optional=True)
            if (value is None) != (maximum is None) or (value is not None and value > maximum):
                abort(400, description='Current stats cannot exceed their maximum.')
            setattr(c,stat,value)
            setattr(c,stat+'_max',maximum)
        c.armor = number('armor',3)
        c.gold = number('gold')
        if c.kind == 'hireling':
            c.daily_cost = number('daily_cost')
            if c.party.owner == current_user.id:
                c.shared = request.form.get('shared') == 'on'
        finish_companion_transfers(c)
        db.session.commit()
        return redirect(url_for('companions.sheet',companion_id=c.id))
    if request.args.get('mode') == 'edit':
        editable(c.id)
        return redirect(url_for('companions.sheet', companion_id=c.id))
    return render_template('main/companion.html', back=parent_url(c),
                           **sheet_context(c))


@companions.route('/companions/<int:companion_id>/stat', methods=['POST'])
@login_required
def stat(companion_id):
    return save_current_stat(editable(companion_id))


@companions.route('/companions/<int:companion_id>/delete', methods=['POST'])
@login_required
def delete(companion_id):
    c = editable(companion_id)
    csrf()
    back = parent_url(c)
    db.session.delete(c)
    db.session.commit()
    return redirect(back)


@companions.route('/companions/<int:companion_id>/inventory', methods=['POST'])
@login_required
def inventory_update(companion_id):
    c = editable(companion_id)
    csrf()
    items, containers = json.loads(c.items), json.loads(c.containers)
    action = request.form.get('action')
    if action in ('container', 'delete-container'):
        cid = request.form.get('container_id', '')
        container = next((v for v in containers if str(v['id']) == cid), None)
        if cid and container is None:
            abort(404)
        if action == 'delete-container':
            if container is None or container['id'] == 0 or any(it['location'] == container['id'] for it in items):
                abort(400, description='Only empty extra containers can be removed.')
            containers.remove(container)
            items = [it for it in items if it.get('carrying') != container['id']]
        else:
            name, slots = text('name',100,True), number('slots',1000)
            if container is None:
                container = dict(id=max(v['id'] for v in containers)+1)
                containers.append(container)
            container.update(name=name,slots=slots)
            if container['id'] != 0:
                load = number('load',1000,optional=True) or 0
                container.update(carried_by=0,load=load)
                items = [it for it in items if it.get('carrying') != container['id']]
                items.extend(dict(id=uuid.uuid4().hex,name='Carrying '+name,tags=[],location=0,carrying=container['id']) for _ in range(load))
    elif action in ('item', 'delete-item'):
        iid = request.form.get('item_id','')
        item = next((v for v in items if str(v['id']) == iid), None)
        if iid and item is None:
            abort(404)
        if item and 'carrying' in item:
            abort(400)
        if action == 'delete-item':
            if item is None:
                abort(404)
            items.remove(item)
        else:
            cid = number('location')
            if not any(v['id'] == cid for v in containers):
                abort(400)
            if item is None:
                item = dict(id=uuid.uuid4().hex)
                items.append(item)
            item.update(name=text('name',200,True), description=text('description',10000), location=cid,
                        tags=[t.strip() for t in text('tags',500).split(',') if t.strip()])
            for field in ('uses','charges','max_charges'):
                value = number(field,optional=True)
                if value is None:
                    item.pop(field,None)
                else:
                    item[field] = value
            item['armor_active'] = request.form.get('armor_active') == 'on'
    else:
        abort(400)
    c.items, c.containers = sanitize_json_content(json.dumps(items)), sanitize_json_content(json.dumps(containers))
    db.session.commit()
    return redirect(url_for('companions.sheet',companion_id=c.id))


@companions.route('/companions/<int:companion_id>/transfer', methods=['POST'])
@login_required
def transfer(companion_id):
    c = editable(companion_id)
    csrf()
    incoming = request.form.get('direction') == 'in'
    parts = request.form.get('source_item' if incoming else 'destination', '').split('|', 1)
    if len(parts) != 2:
        abort(400)
    other = inventories(c,incoming).get(parts[0])
    if other is None:
        abort(403)
    source, target = (other,c) if incoming else (c,other)
    try:
        location = number('location') if incoming else int(parts[1])
    except ValueError:
        abort(400)
    Inventory(source).transfer_item(parts[1] if incoming else request.form.get('item_id'),target,location)
    return redirect(url_for('companions.sheet',companion_id=c.id))


def sheet_context(c, selected=0):
    inventory = Inventory(c)
    inventory.select(selected)
    inventory.decorate()
    return dict(c=c, character=c, form=FlaskForm(), editable=can_manage(c), is_owner=can_manage(c),
                can_roll=can_roll(c), roll_party=companion_party(c), stat_form=FlaskForm(),
                companion_sheet=True, inventory=inventory, outgoing=inventories(c) if can_manage(c) else {},
                inventory_edit_base=f'/companions/{c.id}/inventory',
                inventory_select_base=f'/companions/{c.id}/containers', decode=json.loads,
                username='', url_name='', party_containers=[])


def inventory_response(c, selected=0):
    response = make_response(render_template('partial/charview/inventory_slots.html', **sheet_context(c, selected)))
    response.headers['HX-Trigger'] = 'refresh-stats'
    return response


@companions.route('/companions/<int:companion_id>/containers/<int:container_id>')
@login_required
def select_container(companion_id, container_id):
    c = db.get_or_404(Companion, companion_id)
    if (c.kind == 'hireling' and not party_member(c.party)) or (c.hireling and not party_member(c.hireling.party)):
        abort(403)
    editing = request.args.get('mode') == 'edit'
    if editing and not can_manage(c):
        abort(403)
    return inventory_response(c, container_id)


@companions.route('/companions/<int:companion_id>/inventory/<container_id>')
@login_required
def close_modal(companion_id, container_id):
    return inventory_response(editable(companion_id), int(container_id) if container_id.isdigit() else 0)


@companions.route('/companions/<int:companion_id>/inventory/item-edit/<item_id>')
@login_required
def item_modal(companion_id, item_id):
    c = editable(companion_id)
    context = sheet_context(c, request.args.get('container', 0, type=int))
    item = context['inventory'].get_item(item_id)
    mode = request.args.get('mode', 'edit')
    if mode == 'edit' and not item:
        abort(404)
    from app.lib.market import Market
    from app.lib.data import load_market
    return render_template('partial/modal/edit_item.html', item=item, mode=mode,
                           library=Market().buy([it['name'] for it in load_market()]), **context)


@companions.route('/companions/<int:companion_id>/inventory/item-edit/<item_id>/save', methods=['POST'])
@login_required
def item_save(companion_id, item_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    data = request.form
    creating = request.args.get('mode') == 'create'
    original = inventory.get_item(item_id)
    if not creating and (not original or 'carrying' in original):
        abort(400)
    destination = data['edit_item_container']
    moving = destination.startswith('recipient:')
    location = original['location'] if moving and original else destination
    values = [data['edit_item_name'], data['edit_item_tags'], data['edit_item_uses'],
              data['edit_item_charges'], data['edit_item_max_charges'], location, data['edit_item_description']]
    from werkzeug.exceptions import HTTPException
    try:
        if moving:
            if creating:
                abort(400)
            parts = destination.removeprefix('recipient:').split('|', 1)
            target = inventories(c).get(parts[0])
            if len(parts) != 2 or target is None or not parts[1].isdigit():
                abort(403)
            inventory.update_item(item_id, *values, armor_active=data.get('edit_item_armor_active') == 'on', commit=False)
            inventory.transfer_item(item_id, target, int(parts[1]))
            if data.get('inventory_context') != 'sheet':
                record_transfer(c, target, item_id)
        else:
            if not str(location).isdigit() or not inventory.get_container(location):
                abort(400)
            if creating:
                item = inventory.create_item(*values, armor_active=data.get('edit_item_armor_active') == 'on', commit=False)
                if item is None:
                    abort(400, description='The item does not fit in this container.')
                requested_slot = data.get('edit_item_slot', '')
                if requested_slot.isdigit() and str(item['location']) == data.get('slot_container'):
                    from app.lib.inventory_slots import item_size
                    if item_size(item):
                        inventory.select(int(item['location']))
                        last_slot = int(inventory.selected_container['slots']) - item_size(item)
                        inventory.place_item(item['id'], min(int(requested_slot), last_slot), commit=False)
                db.session.commit()
            else:
                inventory.update_item(item_id, *values, armor_active=data.get('edit_item_armor_active') == 'on')
    except HTTPException as error:
        db.session.rollback()
        response = make_response(render_template('partial/inventory_error.html', message=error.description))
        response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
        return response
    return inventory_response(c, int(location))


@companions.route('/companions/<int:companion_id>/inventory/container-edit/<container_id>', methods=['GET', 'POST'])
@login_required
def container_modal(companion_id, container_id):
    c = editable(companion_id)
    context = sheet_context(c)
    mode = request.args.get('mode', 'edit')
    container = context['inventory'].get_container(container_id) if mode == 'edit' else None
    if mode == 'edit' and not container:
        abort(404)
    return render_template('partial/modal/edit_container.html', container=container, mode=mode, **context)


@companions.route('/companions/<int:companion_id>/inventory/container-edit/<container_id>/save', methods=['POST'])
@login_required
def container_save(companion_id, container_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    values = (text('name',100,True), number('slots',1000), request.form.get('carried_by',''), number('load',1000,True) or 0)
    if request.form.get('mode') == 'edit':
        if not inventory.get_container(container_id):
            abort(404)
        inventory.update_container(container_id, *values)
        selected = int(container_id)
    else:
        selected = inventory.add_container(*values)
    return inventory_response(c, selected)


@companions.route('/companions/<int:companion_id>/inventory/container-edit/<container_id>/delete', methods=['POST'])
@login_required
def container_delete(companion_id, container_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    if container_id == '0' or not inventory.get_container(container_id):
        abort(400)
    inventory.delete_container(container_id, request.form.get('delete-items',''))
    return inventory_response(c)


@companions.route('/companions/<int:companion_id>/inventory/<container_id>/item-delete/<item_id>', methods=['POST'])
@login_required
def item_delete(companion_id, container_id, item_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    item = inventory.get_item(item_id)
    if not item or 'carrying' in item:
        abort(400)
    inventory.delete_item(container_id, item_id)
    return inventory_response(c, int(container_id))


@companions.route('/companions/<int:companion_id>/inventory/item-edit/<item_id>/amount', methods=['POST'])
@login_required
def item_amount(companion_id, item_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    item = inventory.get_item(item_id)
    if not item or request.args.get('property') not in ('uses','charges') or request.args.get('action') not in ('plus','minus'):
        abort(400)
    inventory.change_amount(item_id, request.args['action'], request.args['property'])
    return inventory_response(c, item['location'])


@companions.route('/companions/<int:companion_id>/inventory/<int:container_id>/fatigue', methods=['POST'])
@login_required
def fatigue(companion_id, container_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    if not inventory.get_container(container_id):
        abort(404)
    inventory.add_fatigue(container_id)
    return inventory_response(c, container_id)


@companions.route('/companions/<int:companion_id>/cancel', methods=['POST'])
@login_required
def cancel_edit(companion_id):
    c = editable(companion_id)
    csrf()
    from app.lib.character_json import normalize_inventory
    try:
        items, containers = normalize_inventory(request.form['old_items'], request.form['old_containers'])
    except (ValueError, TypeError, KeyError):
        abort(400)
    finish_companion_transfers(c, items)
    c.items = sanitize_json_content(json.dumps(items))
    c.containers = sanitize_json_content(json.dumps(containers))
    db.session.commit()
    return redirect(url_for('companions.sheet', companion_id=c.id))


@companions.get('/companions/<int:companion_id>/portrait')
@login_required
def portrait(companion_id):
    c = editable(companion_id)
    return portrait_picker(c)


def portrait_picker(c, error=None):
    from app.lib.data import load_images
    return render_template('partial/charedit/portrait.html', images=load_images(),
                           portrait_form=FlaskForm(), error=error,
                           portrait_cancel_url=url_for('companions.portrait_cancel', companion_id=c.id),
                           portrait_save_url=url_for('companions.portrait_save', companion_id=c.id))


@companions.get('/companions/<int:companion_id>/portrait/cancel')
@login_required
def portrait_cancel(companion_id):
    return render_template('partial/companions/portrait.html', c=editable(companion_id), editable=True)


@companions.post('/companions/<int:companion_id>/portrait')
@login_required
def portrait_save(companion_id):
    from flask_babel import _
    from app.lib.portraits import save_portrait, delete_unreferenced_portrait, validate_portrait_reference
    c = editable(companion_id)
    csrf()
    upload = request.files.get('portrait-file')
    previous = c.image_url
    try:
        if upload and upload.filename:
            image_url, custom_image = save_portrait(upload), True
        else:
            custom_url = request.form.get('custom-url', '').strip()
            selected = request.form.get('selected-portrait', '')
            image_url, custom_image = (custom_url, True) if custom_url else (selected, False)
            validate_portrait_reference(image_url, custom_image)
            if not image_url:
                return portrait_cancel(c.id)
    except ValueError as error:
        return portrait_picker(c, _(str(error)))
    c.image_url, c.custom_image = image_url, custom_image
    db.session.commit()
    delete_unreferenced_portrait(previous)
    return render_template('partial/companions/portrait.html', c=c, editable=True)


@companions.get('/companions/<int:companion_id>/export')
@login_required
def export(companion_id):
    from io import BytesIO
    from flask import send_file
    from slugify import slugify
    c = editable(companion_id)
    data = c.export()
    data['kind'] = c.kind
    if c.kind == 'hireling':
        data['daily_cost'] = c.daily_cost
        data['pets'] = [pet.export() for pet in c.pets]
    # Uploaded portraits are links, just as in character exports. Make them usable
    # outside this host's URL context without embedding private ownership data.
    for creature in [data, *data.get('pets', [])]:
        if creature.get('custom_image') and (creature.get('image_url') or '').startswith('/portraits/'):
            creature['image_url'] = url_for('character_edit.uploaded_portrait',
                                           filename=creature['image_url'].rsplit('/', 1)[1], _external=True)
    response = send_file(BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')),
                         mimetype='application/json', as_attachment=True,
                         download_name=(slugify(c.name) or c.kind) + '.json')
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@companions.route('/companions/<int:companion_id>/convert', methods=['GET', 'POST'])
@login_required
def convert(companion_id):
    from flask_babel import _
    from app.lib.companions import conversion_owners, convert_hireling
    c = db.get_or_404(Companion, companion_id)
    if c.kind != 'hireling':
        abort(400)
    if c.party.owner != current_user.id:
        abort(403)
    if request.method == 'POST':
        csrf()
        # Serialize membership updates and prevent two conversions of one hireling.
        db.session.execute(db.select(Party).where(Party.id == c.party_id).with_for_update()
                           .execution_options(populate_existing=True)).scalar_one()
        c = db.session.execute(db.select(Companion).where(Companion.id == companion_id)
                               .with_for_update().execution_options(populate_existing=True)).scalar_one_or_none()
        if c is None:
            abort(404)
    owners = conversion_owners(c.party)
    error = None
    if request.method == 'POST':
        owner = next((owner for owner in owners if str(owner.id) == request.form.get('owner_id')), None)
        if owner is None:
            abort(400, description='Choose a current party member.')
        try:
            character = convert_hireling(c, owner)
        except ValueError as problem:
            error = _(str(problem))
        else:
            db.session.commit()
            return redirect(url_for('main.character', username=character.owner_username, url_name=character.url_name))
    return render_template('main/companion_convert.html', c=c, owners=owners, error=error,
                           form=FlaskForm()), 400 if error else 200


@companions.route('/companions/import/<kind>', methods=['POST'])
@login_required
def import_sheet(kind):
    from flask_babel import _
    from app.lib.translations import N_
    from app.lib.companions import import_companion, import_destinations, render_import_page
    if kind not in ('pet', 'hireling'):
        abort(404)
    destinations = import_destinations(kind)
    selected = request.form.get('parent', '')
    error = None
    csrf()
    parent = dict(destinations).get(selected)
    if parent is None:
        abort(403)
    upload = request.files.get('json_file')
    try:
        if not upload or not upload.filename:
            raise ValueError(N_('Choose a JSON file to import.'))
        raw = upload.stream.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError(N_('Choose a JSON file smaller than 2 MB.'))
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError, RecursionError):
            raise ValueError(N_('Choose a valid JSON file.'))
        try:
            c = import_companion(data, kind)
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            raise ValueError(N_('The JSON file does not contain a valid %(kind)s export with valid stats, inventory and pets.'))
    except ValueError as problem:
        error = _(str(problem), kind=_('pet') if kind == 'pet' else _('hireling'))
    else:
        # Never take parent IDs, the row ID or shared access from the file.
        if kind == 'hireling':
            c.party = parent
            c.shared = request.form.get('shared') == 'on'
        elif selected.startswith('character:'):
            c.character = parent
        else:
            c.hireling = parent
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('companions.sheet', companion_id=c.id))
    return render_import_page(error=error, selected=selected, kind=kind), 400


@companions.route('/companions/<int:companion_id>/section/<section>', methods=['GET', 'POST'])
@login_required
def section(companion_id, section):
    from werkzeug.exceptions import HTTPException
    c = editable(companion_id)
    limits = {'name': 100, 'role': 100, 'attack': 200, 'notes': 10000}
    if section not in (*limits, 'daily_cost', 'access') or (section in ('daily_cost', 'access') and c.kind != 'hireling'):
        abort(404)
    if section == 'access' and c.party.owner != current_user.id:
        abort(403)
    editing, error = request.args.get('view') != '1', None
    if request.method == 'POST':
        csrf()
        editing = True
        try:
            value = (number('daily_cost') if section == 'daily_cost' else
                     request.form.get('shared') == 'on' if section == 'access' else
                     text(section, limits[section], section == 'name'))
        except HTTPException as problem:
            error = problem.description
        else:
            setattr(c, 'shared' if section == 'access' else section, value)
            db.session.commit()
            editing = False
    response = make_response(render_template('partial/companions/inline_section.html',
        c=c, editable=True, section=section, editing=editing, error=error, form=FlaskForm()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@companions.get('/companions/<int:companion_id>/stats')
@login_required
def stats(companion_id):
    c = db.get_or_404(Companion, companion_id)
    if (c.kind == 'hireling' and not party_member(c.party)) or (c.hireling and not party_member(c.hireling.party)):
        abort(403)
    response = make_response(render_template('partial/companions/stats.html', **sheet_context(c)))
    response.headers['Cache-Control'] = 'no-store'
    return response


@companions.post('/companions/<int:companion_id>/sheet-stat')
@login_required
def sheet_stat(companion_id):
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    c = editable(companion_id)
    csrf()
    field = request.form.get('stat', '')
    maxima = tuple(stat + '_max' for stat in STATS)
    if field not in (*STATS, *maxima, 'gold', 'armor'):
        abort(400)
    try:
        value = number('value', 3 if field == 'armor' else 100000, optional=field in (*STATS, *maxima))
        if field in STATS and value is not None and getattr(c, field + '_max') is not None and value > getattr(c, field + '_max'):
            abort(400, description='Current stats cannot exceed their maximum.')
    except HTTPException as problem:
        return jsonify(error=problem.description), 400
    if field in STATS or field in maxima:
        stat = field.removesuffix('_max')
        if value is None:
            setattr(c, stat, None)
            setattr(c, stat + '_max', None)
        elif field in maxima:
            setattr(c, stat, min(getattr(c, stat) or 0, value))
        elif getattr(c, stat + '_max') is None:
            setattr(c, stat + '_max', value)
    setattr(c, field, value)
    db.session.commit()
    return '', 204


@companions.post('/companions/<int:companion_id>/inventory/move')
@login_required
def item_move(companion_id):
    c = editable(companion_id)
    csrf()
    inventory = Inventory(c)
    item = inventory.get_item(request.form.get('item_id'))
    if item is None:
        abort(404)
    inventory.place_item(item['id'], number('slot'))
    return inventory_response(c, item['location'])


@companions.post('/companions/<int:companion_id>/inventory/item-edit/<item_id>/uses')
@login_required
def item_uses(companion_id, item_id):
    c = editable(companion_id)
    csrf()
    items = json.loads(c.items)
    item = next((item for item in items if str(item['id']) == item_id), None)
    if item is None:
        abort(404)
    if 'uses' not in item.get('tags', []):
        abort(400)
    maximum = max(1, item.get('max_uses', item.get('uses', 0)), item.get('uses', 0))
    item['uses'], item['max_uses'] = number('uses', maximum), maximum
    c.items = json.dumps(items)
    db.session.commit()
    return inventory_response(c, item['location'])

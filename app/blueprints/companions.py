"""Pets and hirelings have distinct entry points and shared small-sheet controls."""
import json
import uuid
from flask import Blueprint, abort, redirect, render_template, request, url_for, make_response
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from app.models import db, Character, Party, Companion
from app.lib.companions import STATS, can_manage, catalog, import_pet, new_hireling, party_member, pet_data, companion_destinations, record_transfer, finish_companion_transfers
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
    editing = request.args.get('mode') == 'edit'
    if editing and not can_manage(c):
        abort(403)
    return render_template('main/companion.html', editing=editing, back=parent_url(c),
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
                companion_sheet=True, inventory=inventory, outgoing=inventories(c) if can_manage(c) else {},
                inventory_edit_base=f'/companions/{c.id}/inventory',
                inventory_select_base=f'/companions/{c.id}/containers', decode=json.loads,
                username='', url_name='', party_containers=[])


def inventory_response(c, selected=0, editing=True):
    return render_template('partial/charedit/inventory.html' if editing else 'partial/charview/inventory.html',
                           **sheet_context(c, selected))


@companions.route('/companions/<int:companion_id>/containers/<int:container_id>')
@login_required
def select_container(companion_id, container_id):
    c = db.get_or_404(Companion, companion_id)
    if c.kind == 'hireling' and not party_member(c.party):
        abort(403)
    editing = request.args.get('mode') == 'edit'
    if editing and not can_manage(c):
        abort(403)
    return inventory_response(c, container_id, editing)


@companions.route('/companions/<int:companion_id>/inventory/<container_id>')
@login_required
def close_modal(companion_id, container_id):
    return inventory_response(editable(companion_id), int(container_id) if container_id.isdigit() else 0)


@companions.route('/companions/<int:companion_id>/inventory/item-edit/<item_id>')
@login_required
def item_modal(companion_id, item_id):
    c = editable(companion_id)
    context = sheet_context(c)
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
            record_transfer(c, target, item_id)
        else:
            if not str(location).isdigit() or not inventory.get_container(location):
                abort(400)
            if creating:
                inventory.create_item(*values, armor_active=data.get('edit_item_armor_active') == 'on')
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

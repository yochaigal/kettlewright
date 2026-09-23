from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response, abort
from flask_login import login_required, current_user
from app.lib import *
from app.models import db, User, Character, Party, PartyRoll
from app.socket_events import party_recipient_ids, notify_roll_history_changed
from app.lib.quick_stats import save_current_stat
from app.lib.companions import save_item_to_companion, finish_companion_transfers, can_transfer_from
from flask_wtf import FlaskForm
from app.forms import *
import json
from flask_babel import _

party = Blueprint('party', __name__)


def party_characters(target_party):
    members = json.loads(target_party.members) if target_party.members and target_party.members.strip() else []
    by_id = {character.id: character for character in Character.query.filter(
        Character.id.in_(members), Character.party_id == target_party.id
    ).all()}
    return [by_id[member_id] for member_id in members if member_id in by_id]


@party.route('/party/<int:party_id>/members', methods=['GET'])
@login_required
def members(party_id):
    target_party = db.get_or_404(Party, party_id)
    response = make_response(render_template(
        'partial/partyview/members.html', party=target_party,
        characters=party_characters(target_party), stat_form=FlaskForm()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.route('/party/<int:party_id>/members/<int:character_id>/stat', methods=['POST'])
@login_required
def update_member_stat(party_id, character_id):
    target_party = db.get_or_404(Party, party_id)
    character = db.get_or_404(Character, character_id)
    if character.party_id != target_party.id or character.id not in json.loads(target_party.members or '[]'):
        abort(404)
    if current_user.id not in (target_party.owner, character.owner):
        abort(403)
    return save_current_stat(character)


def get_party_data(ownername, party_url):
    owner = User.query.filter_by(username=ownername).first_or_404()
    party = Party.query.filter_by(
        owner=owner.id, party_url=party_url).first_or_404()
    join_code = None
    is_owner = False
    is_subowner = False
    if current_user.is_authenticated:
        if party.owner == current_user.id:
            join_code = party.join_code
            is_owner = True
    subowners_list = json.loads(
        party.subowners) if party.subowners and party.subowners.strip() else []

    if current_user.is_authenticated:
        is_subowner = current_user.id in subowners_list
    characters = party_characters(party)
    for character in characters:
        character.portrait_src = character.image_url if character.custom_image else url_for(
            'static', filename='images/portraits/' + (character.image_url or 'default-portrait.webp'))
    
    inventory = Inventory(party)
    inventory.select(0)
    inventory.setItemsWithRolls(False)
    inventory.decorate()

    return party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party


# Route: view party page
@party.route('/users/<ownername>/parties/<party_url>/', methods=['GET'])
def party_view(ownername, party_url):
    if not current_user.is_authenticated:
        return redirect(url_for('main.index'))
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    can_view_rolls = current_user.id in party_recipient_ids(party)
    return render_template('main/party_view.html', party_url=party_url, characters=characters, join_code=join_code, is_owner=is_owner,
                           is_subowner=is_subowner, party_id=party.id, ownername=ownername, inventory=inventory, party=party,
                           can_view_rolls=can_view_rolls, roll_form=FlaskForm(), stat_form=FlaskForm(),
                           rolls=PartyRoll.latest(party.id) if can_view_rolls else [],
                           wilderness_mounts=wilderness_mounts(party, characters))


@party.route('/party/<int:party_id>/roll-history', methods=['GET'])
@login_required
def roll_history(party_id):
    target_party = db.get_or_404(Party, party_id)
    if current_user.id not in party_recipient_ids(target_party):
        abort(403)
    response = make_response(render_template('partial/partyview/roll_history_entries.html',
                                            rolls=PartyRoll.latest(party_id)))
    response.headers['Cache-Control'] = 'no-store'
    return response


@party.route('/party/<int:party_id>/roll-history/clear', methods=['POST'])
@login_required
def clear_roll_history(party_id):
    target_party = db.get_or_404(Party, party_id)
    if target_party.owner != current_user.id:
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    PartyRoll.query.filter_by(party_id=party_id).delete(synchronize_session=False)
    db.session.commit()
    notify_roll_history_changed(target_party)
    return '', 204


# Route: redirect to character view
@party.route('/party/show-user/<username>/<url_name>', methods=['GET'])
def party_show_user(username, url_name):
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name+"/"
    return response


# Route: edit party
@party.route('/party/edit/<ownername>/<party_url>', methods=['GET'])
def party_edit(ownername, party_url):
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    form = PartyEditForm(obj=party) 
    render =  render_template('main/party_edit.html', party_url=party_url, characters = characters, join_code = join_code, is_owner=is_owner, is_subowner=is_subowner,ownername=ownername, inventory=inventory, party=party, form=form)
    response = make_response(render)
    response.headers["HX-Trigger-After-Settle"] = "party-edit"
    return response
    

# Route: edit party cancel
@party.route('/party/edit/<ownername>/<party_url>/cancel', methods=['GET','POST'])
def party_edit_cancel(ownername, party_url):
    party_url, characters, join_code, is_owner, is_subowner,ownername, inventory, party = get_party_data(ownername, party_url)
    if not can_transfer_from(party):
        abort(403)
    data = request.form
    changed = False
    # restore some data
    if data['old_items'] != None:
        restored_items = json.loads(data['old_items'])
        finish_companion_transfers(party, restored_items)
        party.items = json.dumps(restored_items)
        changed = True
    if data['old_containers'] != None:
        party.containers = data['old_containers']
        changed = True
    if changed:
        db.session.commit()
    inventory.remove_items_from_characters(json.loads(party.items))
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+ownername+"/parties/"+party_url+"/"
    return response


# Route: edit party save
@party.route('/party/edit/<ownername>/<party_url>/save', methods=['POST'])
def party_edit_save(ownername, party_url):
    fields_to_update = ['name','description']
    party = get_party_by_owner(ownername, party_url)
    form = PartyEditForm(obj=party) 
    for field in fields_to_update:
        setattr(party, field, sanitize_data(getattr(form, field).data))
    # Backward compatibility: update item ids
    items = json.loads(party.items)
    result = []
    for it in items:
        if isinstance(it["id"], int):
            it["id"] = uuid.uuid4().hex
        result.append(it)
    party.items = json.dumps(result)
    finish_companion_transfers(party)
    db.session.commit()
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+ownername+"/parties/"+party_url+"/"
    return response

# Route: remove character from party
@party.route('/party/remove-char/<character_id>/<ownername>/<party_url>', methods=['POST'])
@login_required
def party_remove_char(character_id, ownername, party_url):
    target_party = get_party_by_owner(ownername, party_url)
    if target_party is None:
        abort(404)
    if target_party.owner != current_user.id:
        abort(403)
    character = get_character(character_id)
    if character is None or character.party_id != target_party.id:
        abort(404)
    remove_character_from_party(character)
    db.session.commit()
    response = make_response("")
    response.headers["HX-Redirect"] = "/party/edit/"+ownername+"/"+party_url
    return response

# Route: delete party
@party.route('/party/delete/<party_id>', methods=['POST'])
@login_required
def party_delete(party_id):
    party = get_party_by_id(party_id)
    if party is None:
        abort(404)
    if party.owner != current_user.id:
        abort(403)

    # remove party from all characters in the party
    characters = Character.query.filter_by(party_id=party.id).all()
    for character in characters:
        character.party_id = None
        character.party_code = None

    PartyRoll.query.filter_by(party_id=party.id).delete(synchronize_session=False)
    db.session.delete(party)
    db.session.commit()
    
    response = make_response("redirect")
    response.headers["HX-Redirect"] = "/users/"+current_user.username+"/parties/"
    return response


# --- PARTY INVENTORY ---

# Route: edit inventory
@party.route('/party/inventory/<party_id>/<container_id>', methods=['GET'])
def party_inventory_edit(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    if container_id != "None":
        inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)        
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)

# Route: edit container dialog
@party.route('/party/inventory/<party_id>/container-edit/<container_id>', methods=['GET'])
def party_inventory_container_edit(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        container = inventory.get_container(container_id)
    else:
        container = None
    render =  render_template('partial/modal/edit_container_party.html', party=party, inventory=inventory, container=container, mode=mode)
    response = make_response(render)
    response.headers['HX-Trigger-After-Settle'] = "container-edit"
    return response

# Route: edit container dialog save
@party.route('/party/inventory/<party_id>/container-edit/<container_id>/save', methods=['POST'])
def party_inventory_container_edit_save(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    data = request.form
    slots = 1
    if "slots" in data and data["slots"] != "":
        slots = data["slots"]
    if data["mode"] == "edit":
        inventory.update_container(container_id,data["name"],slots,data["carried_by"],data["load"])
        inventory.select(int(container_id))
        container = inventory.get_container(container_id)
    else:
        id = inventory.add_container(data["name"],slots,data["carried_by"],data["load"])
        inventory.select(id)
        container = inventory.get_container(id)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)


# Route: select inventory container
@party.route('/party/inventory-select-container/<party_id>/<container_id>', methods=['GET'])
def party_inventory_select_container(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    tpl = 'partial/partyview/inventory.html'
    mode = request.args.get('mode')
    if mode != None and mode == "edit":
        tpl = 'partial/partyedit/inventory.html'
    return render_template(tpl, party=party, inventory=inventory)

# Route: delete container
@party.route('/party/inventory/<party_id>/container-edit/<container_id>/delete', methods=['POST'])
def party_inventory_container_delete(party_id, container_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    data = request.form
    inventory.delete_container(container_id, data["delete-items"])
    inventory.select(0)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)

# Route: edit item dialog
@party.route('/party/inventory/<party_id>/item-edit/<item_id>', methods=['GET'])
def party_inventory_item_edit(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    characters = []
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        item = inventory.get_item(item_id)
        members_list = json.loads(
        party.members) if party.members and party.members.strip() else []
        for member_id in members_list:
            character = Character.query.filter_by(id=member_id).first()
            if character:
                characters.append(character)
    else:
        item = None
    render = render_template('partial/modal/edit_item_party.html', characters=characters, party=party, inventory=inventory, item=item, mode=mode, library=Market().buy([it["name"] for it in load_market()]))
    response = make_response(render)
    response.headers['HX-Trigger-After-Settle'] = "item-edit"
    return response

# Route: edit item save
@party.route('/party/inventory/<party_id>/item-edit/<item_id>/save', methods=['POST'])
def party_inventory_item_edit_save(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    data = request.form
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if data["edit_item_container"].startswith('companion:'):
        if mode != 'edit':
            abort(400)
        from werkzeug.exceptions import HTTPException
        try:
            save_item_to_companion(inventory, item_id, data["edit_item_container"])
        except HTTPException as error:
            db.session.rollback()
            response = make_response(render_template('partial/inventory_error.html', message=error.description))
            response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
            return response
    elif mode == "edit":
        item = inventory.update_item(item_id,data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on")
        inventory.select(int(item["location"]))
    else:
        item = inventory.create_item(data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on")
        inventory.select(int(item["location"]))
    inventory.decorate()
    render = render_template('partial/partyedit/inventory.html', party=party,inventory=inventory)    
    response = make_response(render)
    return response



# Route: remove inventory item
@party.route('/party/inventory/<party_id>/<container_id>/item-delete/<item_id>', methods=['GET'])
def party_inventory_delete_item(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.delete_item(container_id, item_id)
    inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    render =  render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)
    response = make_response(render)
    return response

# Route: change some amount property in item
@party.route('/party/inventory/<party_id>/item-edit/<item_id>/amount', methods=['GET'])
def party_inventory_item_edit_amount(party_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    prop = request.args.get('property')
    action = request.args.get('action')
    item = inventory.change_amount(item_id, action, prop)
    inventory.select(item["location"])
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)  


# Route: transfer item dialog
@party.route('/party/inventory/<party_id>/item-transfer/<container_id>/<item_id>', methods=['GET'])
def party_inventory_item_transfer(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    inventory = Inventory(party)
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    item = inventory.get_item(item_id)
    members_list = json.loads(
        party.members) if party.members and party.members.strip() else []
    characters = []
    for member_id in members_list:
        character = Character.query.filter_by(id=member_id).first()
        if character:
            characters.append(character)
    return render_template('partial/modal/transfer_item.html', characters=characters,party=party, inventory=inventory, item=item, container_id=container_id)

# Route: transfer item dialog accept
@party.route('/party/inventory/<party_id>/item-transfer/<container_id>/<item_id>/transfer', methods=['POST'])
def party_inventory_item_transfer_accept(party_id, container_id, item_id):
    party = get_party_by_id(party_id)
    data = request.form
    inventory = Inventory(party)
    if data['member'] and data['member'] != "":
        item = inventory.move_item_to_user(item_id, int(data['member']))
        inventory.select(int(container_id))
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)  

      
    


def wilderness_mounts(target_party, characters):
    return [pet for parent in [*characters, *target_party.hirelings] for pet in parent.pets
            if any(int(c.get('slots', 0)) > 0 for c in json.loads(pet.containers or '[]'))]


@party.post('/party/<int:party_id>/wilderness')
@login_required
def wilderness_action(party_id):
    from app.lib.wilderness import supply, make_camp
    target = db.get_or_404(Party, party_id)
    if target.owner != current_user.id:
        abort(403)
    if not FlaskForm().validate_on_submit():
        abort(400)
    characters = party_characters(target)
    selected = request.form.getlist('participants')
    by_id = {str(c.id): c for c in characters if not c.dead}
    if not selected or len(set(selected)) != len(selected) or any(i not in by_id for i in selected):
        abort(400)
    participants = [by_id[i] for i in selected]
    action = request.form.get('action')
    try:
        # Compare-and-swap prevents a second submission from spending or awarding twice.
        version = int(request.form.get('version', ''))
    except ValueError:
        abort(400)
    changed = Party.query.filter_by(id=target.id, version=version).update(
        {Party.version: Party.version + 1}, synchronize_session=False)
    if not changed:
        db.session.rollback()
        flash(_('The party changed. Review its current resources and try again.'), 'wilderness')
        return redirect(url_for('party.party_view', ownername=target.owner_username, party_url=target.party_url))
    try:
        if action == 'supply':
            try:
                bonus = int(request.form.get('bonus', '0'))
            except ValueError:
                abort(400)
            if not 0 <= bonus <= 4:
                abort(400)
            sides, amount = supply(target, participants, bonus)
            result = _('Supply: d%(sides)s → %(amount)s Rations (3 uses each), added to party storage.', sides=sides, amount=amount)
            db.session.add(PartyRoll(party_id=target.id, character_name=current_user.username, result=result))
        elif action == 'camp':
            allowed_mounts = {str(c.id): c for c in wilderness_mounts(target, characters)}
            mount_ids = request.form.getlist('mounts')
            if len(set(mount_ids)) != len(mount_ids) or any(i not in allowed_mounts for i in mount_ids):
                abort(400)
            make_camp(target, participants, [allowed_mounts[i] for i in mount_ids],
                      resolve_deprivation=request.form.get('resolve_deprivation') == 'on')
            result = _('Camp complete: one Ration use consumed per selected character or mount; Fatigue removed where recovery is possible.')
        else:
            abort(400)
        db.session.commit()
        if action == 'supply':
            notify_roll_history_changed(target)
        flash(result, 'wilderness')
    except ValueError as error:
        db.session.rollback()
        flash(_(str(error)), 'wilderness')
    return redirect(url_for('party.party_view', ownername=target.owner_username, party_url=target.party_url))

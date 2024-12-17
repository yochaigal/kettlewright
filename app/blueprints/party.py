from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.lib import *
from app.models import db, User, Character, Party
from app.forms import *
import json

party = Blueprint('party', __name__)


def get_party_data(ownername, party_url):
    owner = User.query.filter_by(username=ownername).first()
    party = Party.query.filter_by(
        owner=owner.id, party_url=party_url).first()
    join_code = None
    is_owner = False
    is_subowner = False
    if current_user.is_authenticated:
        if party.owner == current_user.id:
            join_code = party.join_code
            is_owner = True
    members_list = json.loads(
        party.members) if party.members and party.members.strip() else []
    subowners_list = json.loads(
        party.subowners) if party.subowners and party.subowners.strip() else []

    if current_user.is_authenticated:
        is_subowner = current_user.id in subowners_list
    characters = []

    for member_id in members_list:
        character = Character.query.filter_by(id=member_id).first()
        if character:
            characters.append(character)
            # Update character portrait source
            if not character.custom_image:
                character.portrait_src = url_for(
                    'static', filename='images/portraits/' + character.image_url)
            else:
                character.portrait_src = character.image_url
    
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
    return render_template('main/party_view.html', party_url=party_url, characters=characters, join_code=join_code, is_owner=is_owner,
                           is_subowner=is_subowner, party_id=party.id, ownername=ownername, inventory=inventory, party=party)


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
    data = request.form
    changed = False
    # restore some data
    if data['old_items'] != None:
        party.items = data['old_items']
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
    # TODO: save party
    fields_to_update = ['name','description']
    party = get_party_by_owner(ownername, party_url)
    form = PartyEditForm(obj=party) 
    for field in fields_to_update:
        setattr(party, field, sanitize_data(getattr(form, field).data))
    db.session.commit()
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+ownername+"/parties/"+party_url+"/"
    return response

# Route: remove character from party
@party.route('/party/remove-char/<character_id>/<ownername>/<party_url>', methods=['GET'])
def party_remove_char(character_id, ownername, party_url):
    character = get_character(character_id)
    if not character:
        flash("Character with id "+character_id+" not found")
    remove_character_from_party(character)
    db.session.commit()
    response = make_response("")
    response.headers["HX-Redirect"] = "/party/edit/"+ownername+"/"+party_url
    return response

# Route: delete party
@party.route('/party/delete/<party_id>', methods=['GET'])
def party_delete(party_id):
    party = get_party_by_id(party_id)
    if party.owner != current_user.id:
        return redirect(url_for('main.parties', username=current_user.username))

    # remove party from all characters in the party
    characters = Character.query.filter_by(party_id=party.id).all()
    for character in characters:
        character.party_id = None
        character.party_code = None

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
    render = render_template('partial/modal/edit_item_party.html', characters=characters, party=party, inventory=inventory, item=item, mode=mode)
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
    if mode == "edit":
        item = inventory.update_item(item_id,data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"])
        inventory.select(int(item["location"]))
    else:
        item = inventory.create_item(data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"])
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
        inventory.select(item["location"])
    inventory.setItemsWithRolls(False)
    inventory.decorate()
    return render_template('partial/partyedit/inventory.html', party=party, inventory=inventory)  

      
    

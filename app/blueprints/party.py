from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from app.lib import get_char_data, load_market, Market, Inventory
from app.models import db, User, Character, Party
import json

party = Blueprint('party', __name__)

# --- INVENTORY ---

# Route: select inventory container
@party.route('/party/inventory-select-container/<username>/<party_id>/<container_id>', methods=['GET'])
def party_inventory_select_container(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.select(int(container_id))
    inventory.decorate()
    tpl = 'partial/charview/inventory.html'
    mode = request.args.get('mode')
    if mode != None and mode == "edit":
        tpl = 'partial/charedit/inventory.html'
    return render_template(tpl, user=user, character=character, username=username, party_id=party_id, inventory=inventory)

# Route: edit inventory
@party.route('/party/inventory/<username>/<party_id>/<container_id>', methods=['GET'])
def party_inventory(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    if container_id != "None":
        inventory.select(int(container_id))
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)

# Route: close inventory editor
@party.route('/party/inventory/<username>/<party_id>/<container_id>/close', methods=['GET'])
def party_inventory_close(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.select(int(container_id))
    inventory.decorate()
    return render_template('partial/charview/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)

# Route: remove inventory item
@party.route('/party/inventory/<username>/<party_id>/<container_id>/item-delete/<item_id>', methods=['GET'])
def party_inventory_delete_item(username, party_id, container_id, item_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.delete_item(container_id, item_id)
    inventory.select(int(container_id))
    inventory.decorate()
    render =  render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response

# Route: add fatigue inventory item
@party.route('/party/inventory/<username>/<party_id>/<container_id>/fatigue', methods=['GET'])
def party_inventory_add_fatigue(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.add_fatigue(container_id)
    inventory.select(int(container_id))
    inventory.decorate()
    render = render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response

# Route: edit container dialog
@party.route('/party/inventory/<username>/<party_id>/container-edit/<container_id>', methods=['GET'])
def party_container_edit(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        container = inventory.get_container(container_id)
    else:
        container = None
    return render_template('partial/modal/edit_container.html', user=user, character=character, username=username, party_id=party_id, 
                           inventory=inventory, container=container, mode=mode)

# Route: edit container dialog save
@party.route('/party/inventory/<username>/<party_id>/container-edit/<container_id>/save', methods=['POST'])
def party_inventory_container_edit_save(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    data = request.form
    if data["mode"] == "edit":
        inventory.update_container(container_id,data["name"],data["slots"],data["carried_by"],data["load"])
        inventory.select(int(container_id))
        container = inventory.get_container(container_id)
    else:
        id = inventory.add_container(data["name"],data["slots"],data["carried_by"],data["load"])
        inventory.select(id)
        container = inventory.get_container(id)
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)

# Route: delete container
@party.route('/party/inventory/<username>/<party_id>/container-edit/<container_id>/delete', methods=['POST'])
def party_inventory_container_delete(username, party_id, container_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    data = request.form
    inventory.delete_container(container_id, data["delete-items"])
    inventory.select(0)
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)

# Route: edit item dialog
@party.route('/party/inventory/<username>/<party_id>/item-edit/<item_id>', methods=['GET'])
def party_inventory_item_edit(username, party_id, item_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        item = inventory.get_item(item_id)
    else:
        item = None
    return render_template('partial/modal/edit_item.html', user=user, character=character, username=username, party_id=party_id, 
                           inventory=inventory, item=item, mode=mode)

# Route: edit item save
@party.route('/party/inventory/<username>/<party_id>/item-edit/<item_id>/save', methods=['POST'])
def party_inventory_item_edit_save(username, party_id, item_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
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
    render = render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id,inventory=inventory)    
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response
    
    
# Route: change some amount property in item
@party.route('/party/inventory/<username>/<party_id>/item-edit/<item_id>/amount', methods=['GET'])
def charedit_inplace_inventory_item_edit_amount(username, party_id, item_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    prop = request.args.get('property')
    action = request.args.get('action')
    item = inventory.change_amount(item_id, action, prop)
    inventory.select(item["location"])
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory)    

# Route: move item to party storage
@party.route('/party/inventory/<username>/<party_id>/item-edit/<item_id>/party', methods=['GET'])
def party_inventory_item_edit_party(username, party_id, item_id):
    user, character = get_char_data(username, party_id)
    inventory = Inventory(character)
    item = inventory.move_item_to_party(item_id)
    inventory.select(item["location"])
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, party_id=party_id, inventory=inventory) 
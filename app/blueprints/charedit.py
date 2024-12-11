# Character inline editor blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import load_scars, load_images, character_portrait_link, is_url_image, load_omens, roll_list, Inventory, get_char_data, sanitize_data, sanitize_json_content
from unidecode import unidecode


character_edit = Blueprint('character_edit', __name__)
bool_fields = ['deprived']




# Route: enter character stats editing
# @character_edit.route('/charedit/inplace-stats/<username>/<url_name>')
# def charedit_inplace_stats(username, url_name):
#     user, character = get_char_data(username, url_name)
#     form = CharacterEditForm(obj=character)
#     return render_template('partial/charedit/stats.html', user=user, character=character, form=form, username=username, url_name=url_name)

# Route: save edited character stats
# @character_edit.route('/charedit/inplace-stats/<username>/<url_name>/save', methods=['POST'])
# def charedit_inplace_stats_save(username, url_name):
#     user, character = get_char_data(username, url_name)
#     data = request.form
#     for field in data:
#         value = data[field]
#         if field in bool_fields:
#             if value == 'y':
#                 value = True
#         setattr(character, field, value) # TODO: sanitize data
#     # bool field disappears when unchecked
#     for bf in bool_fields:
#         if not bf in data:
#             setattr(character, bf, False)
#     db.session.commit()
#     return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name)

    
# Route: cancel character stats editing    
# @character_edit.route('/charedit/inplace-stats/<username>/<url_name>/cancel')
# def charedit_inplace_stats_cancel(username, url_name):
#     user, character = get_char_data(username, url_name)
#     return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name)


# Prepare some party data for template
def prepare_party_data(party_id):
    party = Party.query.filter_by(id=party_id).first()
    if party:
        owner_username = User.query.filter_by(id=party.owner).first().username
        party_url = 'users/' + owner_username + '/parties/' + party.party_url + '/'
    else:
        party_url = None
    return party, party_url


# Party utils
def load_party_members(party):
    return json.loads(party.members) if party.members else []
def save_party_members(party, party_members):
    party.members = json.dumps(party_members)
def load_party_subowners(party):
    return json.loads(party.subowners) if party.subowners else []
def save_party_subowners(party, party_subowners):
    party.subowners = json.dumps(party_subowners)
def get_user_characters_in_party(party_members, user_id):
    return [member for member in party_members if Character.query.get(member).owner == user_id]

# Add character to party (assuming party_id in charater is already set)
def add_character_to_party(character):
    if character == None or character.party_id == None:
        return
    party = Party.query.filter_by(id=character.party_id).first()
    if party == None:
        print("party with the id ", character.party_id, "not found")
        return 
    party_members = load_party_members(party)
    if character.id not in party_members:
        party_members.append(character.id)
        save_party_members(party, party_members)
    # Add user to subowners
    party_subowners = load_party_subowners(party)
    if character.owner not in party_subowners:
        party_subowners.append(character.owner)
        save_party_subowners(party, party_subowners)
    
# Remove character from current party        
def remove_character_from_party(character):
    if character.party_id == None:
        return
    party = Party.query.filter_by(id=character.party_id).first()
    if party == None:
        print("party with the id ", character.party_id, "not found")
        return
    party_members = load_party_members(party)
    party_subowners = load_party_subowners(party)
    if character.id in party_members:
        party_members.remove(character.id)
        save_party_members(party, party_members)
    # Check if the user has other characters in the party before removing from subowners
    user_characters = get_user_characters_in_party(party_members, character.owner)
    if not user_characters and character.owner in party_subowners:
        party_subowners.remove(character.owner)
        save_party_subowners(party, party_subowners)
    character.party_id = None

# Route: edit character page
@character_edit.route('/charedit/<username>/<url_name>')
def charedit_show(username, url_name):
    user, character = get_char_data(username, url_name)
    scarlist = load_scars()
    inventory = Inventory(character)
    inventory.select(0)
    inventory.decorate()
    portrait_src = character_portrait_link(character)
    is_owner = False
    if current_user.is_authenticated:
        is_owner = current_user.id == user.id
    form = CharacterEditForm(obj=character)
    render =  render_template('main/character_edit.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist, inventory=inventory, portrait_src=portrait_src, is_owner=is_owner, form=form,old_items = character.items)
    response = make_response(render)
    
    response.headers['HX-Trigger-After-Settle'] = "charedit_loaded"
    return response

# Route: character page save
@character_edit.route('/charedit/<username>/<url_name>/save', methods=['POST'])
def charedit_save(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditForm(obj=character)
    fields_to_update = ['strength_max', 'strength','dexterity_max', 'dexterity', 'willpower_max', 'willpower','hp_max', 'hp', 'deprived', 'gold']
    #'image_url', 'armor', 'party_code','name', 'description', 'notes', 'bonds', 'omens', 'scars', 'traits']
    for field in fields_to_update:
        setattr(character, field, sanitize_data(getattr(form, field).data))
    db.session.commit()
    # TODO: update character
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name
    return response

# Route: character page cancel
@character_edit.route('/charedit/<username>/<url_name>/cancel', methods=['POST'])
def charedit_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    # restore some data
    if data['old_items'] != None:
        character.items = data['old_items']
        db.session.commit()
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name
    return response













# # Route: enter character text field editing
# @character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>', methods=['GET'])
# def charedit_inplace_text(username, url_name, field_name):
#     user, character = get_char_data(username, url_name)
#     party, party_url = prepare_party_data(character.party_id)
#     if field_name == "traits":
#         form = CharacterEditFormTraits(obj=character)
#         template = 'partial/charedit/traits.html'
#     elif field_name == "description":
#         form = CharacterEditFormDescription(obj=character)
#         template = 'partial/charedit/description.html'
#     elif field_name == "bonds":
#         form = CharacterEditFormBonds(obj=character)
#         template = 'partial/charedit/bonds.html'        
#     elif field_name == "omens":
#         form = CharacterEditFormOmens(obj=character)
#         template = 'partial/charedit/omens.html'                
#     elif field_name == "notes":
#         form = CharacterEditFormNotes(obj=character)
#         template = 'partial/charedit/notes.html'                
#     elif field_name == "party_code":
#         form = CharacterEditFormParty(obj=character)
#         template = 'partial/charedit/party.html'                        
#     return render_template(template, user=user, character=character, form=form, username=username, url_name=url_name, party=party, party_url=party_url)
    
# # Route: save edited character text fields    
# @character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/save', methods=['POST'])
# def charedit_inplace_text_save(username, url_name, field_name):
#     err = None
#     user, character = get_char_data(username, url_name)
#     data = request.form
#     if field_name == "party_code":
#         party = Party.query.filter_by(join_code=data[field_name].strip()).first()
#         if party:
#             character.party_id = party.id
#             add_character_to_party(character)
#             owner_username = User.query.filter_by(id=party.owner).first().username
#             party_url = 'users/' + owner_username + '/parties/' + party.party_url + '/'
#         else:
#             err = "Invalid party join code ("+data[field_name]+")"
#             party_url = None
#     else: 
#         setattr(character, field_name, sanitize_data(data[field_name]))
#         party, party_url = prepare_party_data(character.party_id)
#     db.session.commit()
    
#     if field_name == "traits":
#         template = 'partial/charview/traits.html'
#     elif field_name == "description":
#         template = 'partial/charview/description.html'
#     elif field_name == "bonds":
#         template = 'partial/charview/bonds.html'
#     elif field_name == "omens":
#         template = 'partial/charview/omens.html'        
#     elif field_name == "notes":
#         template = 'partial/charview/notes.html'        
#     elif field_name == "party_code":
#         template = 'partial/charview/party.html'                
#     return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url, err=err)

# # Route: cancel character text field editing
# @character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/cancel', methods=['GET'])
# def charedit_inplace_text_cancel(username, url_name, field_name):
#     user, character = get_char_data(username, url_name)
#     party, party_url = prepare_party_data(character.party_id)   
#     if field_name == "traits":
#         template = 'partial/charview/traits.html'
#     elif field_name == "description":
#         template = 'partial/charview/description.html'
#     elif field_name == "bonds":
#         template = 'partial/charview/bonds.html'        
#     elif field_name == "omens":
#         template = 'partial/charview/omens.html'                
#     elif field_name == "notes":
#         template = 'partial/charview/notes.html'                
#     elif field_name == "party_code":
#         template = 'partial/charview/party.html'                        
#     return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url)

# Route: leave current character party
@character_edit.route('/charedit/leave-party/<username>/<url_name>', methods=['GET'])
def charedit_leave_party(username, url_name):
    user, character = get_char_data(username, url_name)
    remove_character_from_party(character)
    db.session.commit()
    return render_template('partial/charview/party.html', user=user, character=character, username=username, url_name=url_name, party=None, party_url="")
    None
    
# ----- SCARS ----    

# Route: character scars editing
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>', methods=['GET'])
def charedit_inplace_scars(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditFormScars(obj=character)
    scarlist = load_scars()
    return render_template('partial/charedit/scars.html', user=user, character=character, username=username, url_name=url_name, form=form, scarlist=scarlist)

# Route: character scars add new scar
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/add', methods=['POST'])
def charedit_inplace_scars_add(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    scarlist = load_scars()
    selected_scar = data['scars-select']
    if selected_scar != None:
        character.scars = character.scars + "\n"+selected_scar+":"+scarlist[selected_scar]
        db.session.commit()
    return render_template('partial/charview/scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)
    
# Route: character scars editing save
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_scars_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    setattr(character, "scars",data["scars"])
    db.session.commit()
    scarlist = load_scars()
    return render_template('partial/charview/scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)

# Route: character scars editing cancel
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_scars_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    scarlist = load_scars()
    return render_template('partial/charview/scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)

# # Route: edit character name
# @character_edit.route('/charedit/inplace-name/<username>/<url_name>', methods=['GET'])
# def charedit_inplace_name(username, url_name):
#     user, character = get_char_data(username, url_name)
#     form = CharacterEditFormName(obj=character)
#     return render_template('partial/charedit/name.html', user=user, character=character, username=username, url_name=url_name, form=form)

# # Route: edit character name save
# @character_edit.route('/charedit/inplace-name/<username>/<url_name>/save', methods=['POST'])
# def charedit_inplace_name_save(username, url_name):
#     user, character = get_char_data(username, url_name)
#     data = request.form
#     setattr(character,"name",data["name"])
#     db.session.commit()
#     return render_template('partial/charview/name.html', user=user, character=character, username=username, url_name=url_name)    

# # Route: edit character name cancel
# @character_edit.route('/charedit/inplace-name/<username>/<url_name>/cancel', methods=['GET'])
# def charedit_inplace_name_cancel(username, url_name):
#     user, character = get_char_data(username, url_name)
#     return render_template('partial/charview/name.html', user=user, character=character, username=username, url_name=url_name)    

# ----- PORTRAIT -----

# Route: edit character portrait
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>', methods=['GET'])
def charedit_inplace_portrait(username, url_name):
    user, character = get_char_data(username, url_name)
    images = load_images()
    return render_template('partial/charedit/portrait.html', user=user, character=character, username=username, url_name=url_name, images=images)

# Route: edit character portrait - cancel
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_portrait_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    portrait_src = character_portrait_link(character)
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/charedit/"+username+"/"+url_name
    return response

# Route: edit character portrait - save
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_portrait_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    custom_url = data['custom-url']
    selected_portrait = data['selected-portrait']
    if custom_url != None and custom_url != "" and is_url_image(custom_url):
        setattr(character,"image_url", custom_url)
        setattr(character,"custom_image",True)
        db.session.commit()    
    elif selected_portrait != "" and selected_portrait != None:
        setattr(character,"image_url", selected_portrait)
        setattr(character,"custom_image",False)
        db.session.commit()    
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/charedit/"+username+"/"+url_name
    return response

# ----- JSON EXPORT -----

# Route: export character to JSON
@character_edit.route('/charedit/export/<username>/<url_name>', methods=['GET'])
def charedit_export(username, url_name):
    user, character = get_char_data(username, url_name)
    response_bytes = character.toJSON()
    response = make_response(response_bytes)
    response.headers.set('Content-Type', 'application/json')
    response.headers.set(
        'Content-Disposition', 'attachment', filename=unidecode(user.username) + '_'+unidecode(character.name) + '.json' )
    return response
    
# Route: rest
@character_edit.route('/charedit/rest/<username>/<url_name>', methods=['GET'])
def charedit_rest(username, url_name):
    user, character = get_char_data(username, url_name)
    setattr(character,"hp",character.hp_max)
    db.session.commit()
    return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name)

# Route: roll omens on omen edit
@character_edit.route('/charedit/omen-roll/<username>/<url_name>', methods=['POST'])
def charedit_omen_roll(username, url_name):
    user, character = get_char_data(username, url_name)  
    omens = load_omens()
    data = request.form
    result = roll_list(omens)
    if data["omens"] != "":
        result = data["omens"] + "\n \n" + result
    form = CharacterEditFormOmens(obj=character)
    form.omens.data = result
    return render_template('partial/charedit/omens.html', user=user, character=character, form=form, username=username, url_name=url_name)

# --- INVENTORY ---

# Route: select inventory container
@character_edit.route('/charedit/inventory-select-container/<username>/<url_name>/<container_id>', methods=['GET'])
def charedit_inventory_select_container(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.select(int(container_id))
    inventory.decorate()
    tpl = 'partial/charview/inventory.html'
    mode = request.args.get('mode')
    if mode != None and mode == "edit":
        tpl = 'partial/charedit/inventory.html'
    return render_template(tpl, user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: edit inventory in-place
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>', methods=['GET'])
def charedit_inplace_inventory(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    if container_id != "None":
        inventory.select(int(container_id))
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: close inventory editor
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/close', methods=['GET'])
def charedit_inplace_inventory_close(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.select(int(container_id))
    inventory.decorate()
    return render_template('partial/charview/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: remove inventory item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/item-delete/<item_id>', methods=['GET'])
def charedit_inplace_inventory_delete_item(username, url_name, container_id, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.delete_item(container_id, item_id)
    inventory.select(int(container_id))
    inventory.decorate()
    render =  render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response

# Route: add fatigue inventory item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/fatigue', methods=['GET'])
def charedit_inplace_inventory_add_fatigue(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.add_fatigue(container_id)
    inventory.select(int(container_id))
    inventory.decorate()
    render = render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response

# Route: edit container dialog
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/container-edit/<container_id>', methods=['GET'])
def charedit_inplace_inventory_container_edit(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        container = inventory.get_container(container_id)
    else:
        container = None
    return render_template('partial/modal/edit_container.html', user=user, character=character, username=username, url_name=url_name, 
                           inventory=inventory, container=container, mode=mode)

# Route: edit container dialog save
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/container-edit/<container_id>/save', methods=['POST'])
def charedit_inplace_inventory_container_edit_save(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
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
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: delete container
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/container-edit/<container_id>/delete', methods=['POST'])
def charedit_inplace_inventory_container_delete(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    data = request.form
    inventory.delete_container(container_id, data["delete-items"])
    inventory.select(0)
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: edit item dialog
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>', methods=['GET'])
def charedit_inplace_inventory_item_edit(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        item = inventory.get_item(item_id)
    else:
        item = None
    return render_template('partial/modal/edit_item.html', user=user, character=character, username=username, url_name=url_name, 
                           inventory=inventory, item=item, mode=mode)

@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/save', methods=['POST'])
def charedit_inplace_inventory_item_edit_save(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
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
    render = render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name,inventory=inventory)    
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response
    
    
# Route: change somea amount property in item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/amount', methods=['GET'])
def charedit_inplace_inventory_item_edit_amount(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    prop = request.args.get('property')
    action = request.args.get('action')
    item = inventory.change_amount(item_id, action, prop)
    inventory.select(item["location"])
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)    

# Route: move item to party storage
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/party', methods=['GET'])
def charedit_inplace_inventory_item_edit_party(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    item = inventory.move_item_to_party(item_id)
    inventory.select(item["location"])
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory) 
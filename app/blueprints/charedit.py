# Character inline editor blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import load_scars, load_images, character_portrait_link, is_url_image, load_omens, roll_list, Inventory


character_edit = Blueprint('character_edit', __name__)
bool_fields = ['deprived']

# Retrieve character data
def get_char_data(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    return user, character

# Route: enter character stats editing
@character_edit.route('/charedit/inplace-stats/<username>/<url_name>')
def charedit_inplace_stats(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditForm(obj=character)
    return render_template('partial/charedit/stats.html', user=user, character=character, form=form, username=username, url_name=url_name)

# Route: save edited character stats
@character_edit.route('/charedit/inplace-stats/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_stats_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    for field in data:
        value = data[field]
        if field in bool_fields:
            if value == 'y':
                value = True
        setattr(character, field, value) # TODO: sanitize data
    # bool field disappears when unchecked
    for bf in bool_fields:
        if not bf in data:
            setattr(character, bf, False)
    db.session.commit()
    return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name)

    
# Route: cancel character stats editing    
@character_edit.route('/charedit/inplace-stats/<username>/<url_name>/cancel')
def charedit_inplace_stats_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name)


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

# Route: enter character text field editing
@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>', methods=['GET'])
def charedit_inplace_text(username, url_name, field_name):
    user, character = get_char_data(username, url_name)
    party, party_url = prepare_party_data(character.party_id)
    if field_name == "traits":
        form = CharacterEditFormTraits(obj=character)
        template = 'partial/charedit/traits.html'
    elif field_name == "description":
        form = CharacterEditFormDescription(obj=character)
        template = 'partial/charedit/description.html'
    elif field_name == "bonds":
        form = CharacterEditFormBonds(obj=character)
        template = 'partial/charedit/bonds.html'        
    elif field_name == "omens":
        form = CharacterEditFormOmens(obj=character)
        template = 'partial/charedit/omens.html'                
    elif field_name == "notes":
        form = CharacterEditFormNotes(obj=character)
        template = 'partial/charedit/notes.html'                
    elif field_name == "party_code":
        form = CharacterEditFormParty(obj=character)
        template = 'partial/charedit/party.html'                        
    return render_template(template, user=user, character=character, form=form, username=username, url_name=url_name, party=party, party_url=party_url)
    
# Route: save edited character text fields    
@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/save', methods=['POST'])
def charedit_inplace_text_save(username, url_name, field_name):
    err = None
    user, character = get_char_data(username, url_name)
    data = request.form
    if field_name == "party_code":
        party = Party.query.filter_by(join_code=data[field_name].strip()).first()
        if party:
            character.party_id = party.id
            add_character_to_party(character)
            owner_username = User.query.filter_by(id=party.owner).first().username
            party_url = 'users/' + owner_username + '/parties/' + party.party_url + '/'
            print("proper", party_url)
        else:
            err = "Invalid party join code ("+data[field_name]+")"
            party_url = None
    else: 
        setattr(character, field_name, sanitize_data(data[field_name]))
        party, party_url = prepare_party_data(character.party_id)
    db.session.commit()
    
    if field_name == "traits":
        template = 'partial/charview/traits.html'
    elif field_name == "description":
        template = 'partial/charview/description.html'
    elif field_name == "bonds":
        template = 'partial/charview/bonds.html'
    elif field_name == "omens":
        template = 'partial/charview/omens.html'        
    elif field_name == "notes":
        template = 'partial/charview/notes.html'        
    elif field_name == "party_code":
        template = 'partial/charview/party.html'                
    return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url, err=err)

# Route: cancel character text field editing
@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/cancel', methods=['GET'])
def charedit_inplace_text_cancel(username, url_name, field_name):
    user, character = get_char_data(username, url_name)
    party, party_url = prepare_party_data(character.party_id)   
    if field_name == "traits":
        template = 'partial/charview/traits.html'
    elif field_name == "description":
        template = 'partial/charview/description.html'
    elif field_name == "bonds":
        template = 'partial/charview/bonds.html'        
    elif field_name == "omens":
        template = 'partial/charview/omens.html'                
    elif field_name == "notes":
        template = 'partial/charview/notes.html'                
    elif field_name == "party_code":
        template = 'partial/charview/party.html'                        
    return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url)

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

# --- Info ---

# Route: edit character name
@character_edit.route('/charedit/inplace-name/<username>/<url_name>', methods=['GET'])
def charedit_inplace_name(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditFormName(obj=character)
    return render_template('partial/charedit/name.html', user=user, character=character, username=username, url_name=url_name, form=form)

# Route: edit character name save
@character_edit.route('/charedit/inplace-name/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_name_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    setattr(character,"name",data["name"])
    db.session.commit()
    return render_template('partial/charview/name.html', user=user, character=character, username=username, url_name=url_name)    

# Route: edit character name cancel
@character_edit.route('/charedit/inplace-name/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_name_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    return render_template('partial/charview/name.html', user=user, character=character, username=username, url_name=url_name)    

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
    return render_template('partial/charview/portrait.html', user=user, character=character, username=username, url_name=url_name, portrait_src=portrait_src)

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
    portrait_src = character_portrait_link(character)
    return render_template('partial/charview/portrait.html', user=user, character=character, username=username, url_name=url_name, portrait_src=portrait_src)


# Route: export character to JSON
@character_edit.route('/charedit/export/<username>/<url_name>', methods=['GET'])
def charedit_export(username, url_name):
    user, character = get_char_data(username, url_name)
    response_bytes = character.toJSON()
    response = make_response(response_bytes)
    response.headers.set('Content-Type', 'application/json')
    response.headers.set(
        'Content-Disposition', 'attachment', filename=user.username + '_'+character.name + '.json' )
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
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

# Route: add fatigue inventory item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/fatigue', methods=['GET'])
def charedit_inplace_inventory_add_fatigue(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    inventory.add_fatigue(container_id)
    inventory.select(int(container_id))
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)

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

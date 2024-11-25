# Character inline editor blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import load_scars, load_images, character_portrait_link, is_url_image


character_edit = Blueprint('character_edit', __name__)
bool_fields = ['deprived']

# Retrieve character data
def get_char_data(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    return user, character

# Route: enter character stats editing
@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>')
def charedit_inplace_attrs(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditForm(obj=character)
    return render_template('partial/charedit_attrs.html', user=user, character=character, form=form, username=username, url_name=url_name)

# Route: save edited character stats
@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_attrs_save(username, url_name):
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
    return render_template('partial/charview_attrs.html', user=user, character=character, username=username, url_name=url_name)

    
# Route: cancel character stats editing    
@character_edit.route('/charedit/inplace-attrs/<username>/<url_name>/cancel')
def charedit_inplace_attrs_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    return render_template('partial/charview_attrs.html', user=user, character=character, username=username, url_name=url_name)


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
        template = 'partial/charedit_traits.html'
    elif field_name == "description":
        form = CharacterEditFormDescription(obj=character)
        template = 'partial/charedit_description.html'
    elif field_name == "bonds":
        form = CharacterEditFormBonds(obj=character)
        template = 'partial/charedit_bonds.html'        
    elif field_name == "omens":
        form = CharacterEditFormOmens(obj=character)
        template = 'partial/charedit_omens.html'                
    elif field_name == "notes":
        form = CharacterEditFormNotes(obj=character)
        template = 'partial/charedit_notes.html'                
    elif field_name == "party_code":
        form = CharacterEditFormParty(obj=character)
        template = 'partial/charedit_party.html'                        
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
    print("save", party, party_url)
    
    if field_name == "traits":
        template = 'partial/charview_traits.html'
    elif field_name == "description":
        template = 'partial/charview_description.html'
    elif field_name == "bonds":
        template = 'partial/charview_bonds.html'
    elif field_name == "omens":
        template = 'partial/charview_omens.html'        
    elif field_name == "notes":
        template = 'partial/charview_notes.html'        
    elif field_name == "party_code":
        template = 'partial/charview_party.html'                
    return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url, err=err)

# Route: cancel character text field editing
@character_edit.route('/charedit/inplace-text/<username>/<url_name>/<field_name>/cancel', methods=['GET'])
def charedit_inplace_text_cancel(username, url_name, field_name):
    user, character = get_char_data(username, url_name)
    party, party_url = prepare_party_data(character.party_id)   
    if field_name == "traits":
        template = 'partial/charview_traits.html'
    elif field_name == "description":
        template = 'partial/charview_description.html'
    elif field_name == "bonds":
        template = 'partial/charview_bonds.html'        
    elif field_name == "omens":
        template = 'partial/charview_omens.html'                
    elif field_name == "notes":
        template = 'partial/charview_notes.html'                
    elif field_name == "party_code":
        template = 'partial/charview_party.html'                        
    return render_template(template, user=user, character=character, username=username, url_name=url_name, party=party, party_url=party_url)

# Route: leave current character party
@character_edit.route('/charedit/leave-party/<username>/<url_name>', methods=['GET'])
def charedit_leave_party(username, url_name):
    user, character = get_char_data(username, url_name)
    remove_character_from_party(character)
    db.session.commit()
    return render_template('partial/charview_party.html', user=user, character=character, username=username, url_name=url_name, party=None, party_url="")
    None
    
# ----- SCARS ----    

# Route: character scars editing
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>', methods=['GET'])
def charedit_inplace_scars(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditFormScars(obj=character)
    scarlist = load_scars()
    return render_template('partial/charedit_scars.html', user=user, character=character, username=username, url_name=url_name, form=form, scarlist=scarlist)

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
    return render_template('partial/charview_scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)
    
# Route: character scars editing save
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_scars_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    setattr(character, "scars",data["scars"])
    db.session.commit()
    scarlist = load_scars()
    return render_template('partial/charview_scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)

# Route: character scars editing cancel
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_scars_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    scarlist = load_scars()
    return render_template('partial/charview_scars.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist)

# --- Info ---

# Route: edit character name
@character_edit.route('/charedit/inplace-name/<username>/<url_name>', methods=['GET'])
def charedit_inplace_name(username, url_name):
    user, character = get_char_data(username, url_name)
    form = CharacterEditFormName(obj=character)
    return render_template('partial/charedit_name.html', user=user, character=character, username=username, url_name=url_name, form=form)

# Route: edit character name save
@character_edit.route('/charedit/inplace-name/<username>/<url_name>/save', methods=['POST'])
def charedit_inplace_name_save(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    setattr(character,"name",data["name"])
    db.session.commit()
    return render_template('partial/charview_name.html', user=user, character=character, username=username, url_name=url_name)    

# Route: edit character name cancel
@character_edit.route('/charedit/inplace-name/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_name_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    return render_template('partial/charview_name.html', user=user, character=character, username=username, url_name=url_name)    

# Route: edit character portrait
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>', methods=['GET'])
def charedit_inplace_portrait(username, url_name):
    user, character = get_char_data(username, url_name)
    images = load_images()
    return render_template('partial/charedit_portrait.html', user=user, character=character, username=username, url_name=url_name, images=images)

# Route: edit character portrait - cancel
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_portrait_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    portrait_src = character_portrait_link(character)
    return render_template('partial/charview_portrait.html', user=user, character=character, username=username, url_name=url_name, portrait_src=portrait_src)

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
    return render_template('partial/charview_portrait.html', user=user, character=character, username=username, url_name=url_name, portrait_src=portrait_src)

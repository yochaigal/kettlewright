# Character inline editor blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response, abort, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import *
from app.models.character import BACKGROUND_FIELDS
from app.lib.quick_stats import save_character_stat
from app.lib.companions import save_item_to_companion, finish_companion_transfers, can_transfer_from
from unidecode import unidecode
from flask_babel import _
from flask_babel import lazy_gettext as _l



character_edit = Blueprint('character_edit', __name__)
bool_fields = ['deprived']

@character_edit.app_context_processor
def inventory_permissions():
    return dict(can_edit_inventory=can_transfer_from)


@character_edit.context_processor
def character_editor_context():
    # HTMX fragments need the same ownership and edit context as the full page.
    username = (request.view_args or {}).get('username')
    return dict(is_owner=current_user.is_authenticated and current_user.username == username,
                inventory_full_edit=request.values.get('inventory_context') == 'character')


@character_edit.before_request
def protect_inventory_editor():
    endpoint = request.endpoint.rsplit('.', 1)[-1]
    editing = endpoint.startswith('charedit_inplace_inventory') or (
        endpoint == 'charedit_inventory_select_container' and request.args.get('mode') == 'edit')
    if editing:
        _, character = get_char_data(request.view_args['username'], request.view_args['url_name'])
        if not can_transfer_from(character):
            abort(403)
        if request.method == 'POST' and not FlaskForm().validate_on_submit():
            abort(400)


@character_edit.after_request
def refresh_inventory_stats(response):
    # Container capacity and item uses can change armor or available HP too.
    if (request.endpoint.rsplit('.', 1)[-1].startswith('charedit_inplace_inventory')
            and request.method == 'POST' and response.status_code == 200
            and 'HX-Retarget' not in response.headers):
        response.headers.setdefault('HX-Trigger', 'refresh-stats')
    return response



# Prepare some party data for template
def prepare_party_data(party_id):
    party = Party.query.filter_by(id=party_id).first()
    if party:
        owner_username = User.query.filter_by(id=party.owner).first().username
        party_url = 'users/' + owner_username + '/parties/' + party.party_url + '/'
    else:
        party_url = None
    return party, party_url


# Each inline editor writes only its own fields, preserving other sheet changes.
INLINE_SECTIONS = {
    'name': ('name',),
    **{field: (field,) for field in ('traits', 'description', 'bonds', 'omens', 'scars', 'notes')},
    'background': BACKGROUND_FIELDS,
    'party': ('party_code',),
}


@character_edit.route('/charedit/<username>/<url_name>/section/<section>', methods=['GET', 'POST'])
@login_required
def character_section(username, url_name, section):
    user, character = get_char_data(username, url_name)
    if character.owner != current_user.id:
        abort(403)
    if section not in INLINE_SECTIONS:
        abort(404)
    fields = INLINE_SECTIONS[section]
    form = CharacterEditForm(obj=character)
    editing = request.args.get('view') != '1'
    errors = []
    if request.method == 'POST':
        if not FlaskForm().validate_on_submit():
            abort(400)
        editing = True
        for field in fields:
            if not form[field].validate(form):
                errors.extend(form[field].errors)
        if section == 'party' and not errors:
            if request.form.get('leave_party') == '1':
                remove_character_from_party(character)
            else:
                code = (form.party_code.data or '').strip()
                party = Party.query.filter_by(join_code=code).first() if code else None
                if not party:
                    errors.append(_('Invalid party code: %(code)s', code=code))
                else:
                    if character.party_id != party.id:
                        remove_character_from_party(character)
                    character.party_id = party.id
                    character.party_code = code
                    add_character_to_party(character)
        if not errors:
            if section != 'party':
                for field in fields:
                    setattr(character, field, sanitize_data(form[field].data))
            db.session.commit()
            editing = False
    party, party_url = prepare_party_data(character.party_id)
    response = make_response(render_template(
        'partial/charview/inline_section.html', section=section, editing=editing,
        fields=fields, form=form, errors=errors, character=character, username=username,
        url_name=url_name, is_owner=True, stat_form=FlaskForm(), party=party,
        party_url=party_url, scarlist=load_scars()))
    response.headers['Cache-Control'] = 'no-store'
    if request.method == 'POST' and not errors:
        response.headers['HX-Trigger'] = json.dumps({'character-section-saved': {
            'section': section, 'partyId': character.party_id}})
    return response


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
    if character.party_code != None and character.party_code.startswith('Invalid last party code:'):
        form.party_code.data = ""
    party, party_url = prepare_party_data(character.party_id)
    render =  render_template('main/character_edit.html', user=user, character=character, username=username, url_name=url_name, scarlist=scarlist, inventory=inventory, portrait_src=portrait_src, is_owner=is_owner, form=form,old_items = character.items, party=party, old_containers=character.containers, party_url=party_url)
    response = make_response(render)
    
    response.headers['HX-Trigger-After-Settle'] = "charedit-loaded"
    return response

# Route: character page save
@character_edit.route('/charedit/<username>/<url_name>/save', methods=['POST'])
@login_required
def charedit_save(username, url_name):
    user, character = get_char_data(username, url_name)
    if character.owner != current_user.id:
        abort(403)
    form = CharacterEditForm(obj=character)
    fields_to_update = ['strength_max', 'strength','dexterity_max', 'dexterity', 'willpower_max', 'willpower','hp_max', 'hp', 'deprived', 'gold','description', 'name','omens', 'scars','traits','bonds','notes','panicked','dead']
    fields_to_update.extend(BACKGROUND_FIELDS)
    for field in fields_to_update:
        setattr(character, field, sanitize_data(getattr(form, field).data))
    err = None
    party_code = getattr(form, 'party_code').data
    if  party_code != "":
        party = Party.query.filter_by(join_code=party_code.strip()).first()
        if party:
            character.party_id = party.id
            add_character_to_party(character)
            character.party_code = party_code
        else:
            party_url = None
            flash("Invalid party code: "+party_code)
    else:
        character.party_code = ""
    character.armor = character.armorValue() # update armor
    # Backward compatibility: update item ids
    items = json.loads(character.items)
    result = []
    for it in items:
        if isinstance(it["id"], int):
            it["id"] = uuid.uuid4().hex
        result.append(it)
    character.items = json.dumps(result)
    finish_companion_transfers(character)
    db.session.commit()
    
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name

    return response

# Route: character page cancel
@character_edit.route('/charedit/<username>/<url_name>/cancel', methods=['POST'])
def charedit_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    if not current_user.is_authenticated or character.owner != current_user.id:
        abort(403)
    data = request.form
    changed = False
    # restore some data
    if data['old_items'] != None:
        restored_items = json.loads(data['old_items'])
        finish_companion_transfers(character, restored_items)
        character.items = json.dumps(restored_items)
        character.armor = character.armorValue() # update armor
        changed = True
    if data['old_gold'] != None:
        character.gold = data['old_gold']
        changed = True
    if data['old_containers'] != None:
        character.containers = data['old_containers']
        changed = True
    if changed:
        db.session.commit()        
    inventory = Inventory(character)
    inventory.remove_items_from_party(json.loads(character.items))
    
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name
    return response

# ----- PARTY ----    


# Route: leave current character party
@character_edit.route('/charedit/leave-party/<username>/<url_name>', methods=['GET'])
def charedit_leave_party(username, url_name):
    user, character = get_char_data(username, url_name)
    remove_character_from_party(character)
    db.session.commit()
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/charedit/"+username+"/"+url_name
    return response

@character_edit.route('/charedit/clear-party-err/<username>/<url_name>', methods=['GET'])
def charedit_clear_party_err(username, url_name):
    user, character = get_char_data(username, url_name)
    character.party_code = ""
    db.session.commit()
    response = make_response("")
    return response

    
# ----- SCARS ----    


# Route: character scars add new scar
@character_edit.route('/charedit/inplace-scars/<username>/<url_name>/add', methods=['POST'])
def charedit_inplace_scars_add(username, url_name):
    user, character = get_char_data(username, url_name)
    data = request.form
    scarlist = load_scars()
    selected_scar = data['scars-select']
    result = data["scars"]
    if selected_scar != None:
        result = result + "\n"+_(selected_scar)+": "+_(scarlist[selected_scar])
    response = make_response(result)
    response.headers["HX-Trigger-After-Settle"] = 'scar-roll'
    return response
    

# ----- PORTRAIT -----

# Route: edit character portrait
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>', methods=['GET'])
@login_required
def charedit_inplace_portrait(username, url_name):
    user, character = get_char_data(username, url_name)
    if character.owner != current_user.id:
        abort(403)
    images = load_images()
    return render_template('partial/charedit/portrait.html', user=user, character=character, username=username, url_name=url_name, images=images, portrait_form=FlaskForm())

# Route: edit character portrait - cancel
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>/cancel', methods=['GET'])
def charedit_inplace_portrait_cancel(username, url_name):
    user, character = get_char_data(username, url_name)
    portrait_src = character_portrait_link(character)
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/charedit/"+username+"/"+url_name
    if request.values.get('sheet_context') == 'inline':
        return render_template('partial/charview/portrait.html', character=character,
                               username=username, url_name=url_name,
                               is_owner=current_user.is_authenticated and current_user.id == character.owner,
                               portrait_src=character_portrait_link(character))
    return response

# Route: edit character portrait - save
@character_edit.route('/charedit/inplace-portrait/<username>/<url_name>/save', methods=['POST'])
@login_required
def charedit_inplace_portrait_save(username, url_name):
    user, character = get_char_data(username, url_name)
    if character.owner != current_user.id:
        abort(403)
    if request.content_length and request.content_length > 3 * 1024 * 1024:
        return render_template('partial/charedit/portrait.html', user=user, character=character,
                               username=username, url_name=url_name, images=load_images(),
                               portrait_form=FlaskForm(formdata=None),
                               error=_('Choose an image smaller than 2 MB.'))
    form = FlaskForm()
    if not form.validate_on_submit():
        abort(400)
    from app.lib.portraits import save_portrait, delete_unreferenced_portrait
    previous_portrait = character.image_url
    upload = request.files.get('portrait-file')
    if upload and upload.filename:
        try:
            portrait_url = save_portrait(upload)
        except ValueError as error:
            return render_template('partial/charedit/portrait.html', user=user, character=character,
                                   username=username, url_name=url_name, images=load_images(),
                                   portrait_form=form, error=_(str(error)))
        character.image_url = portrait_url
        character.custom_image = True
        db.session.commit()
        delete_unreferenced_portrait(previous_portrait)
        response = make_response('Redirecting')
        response.headers['HX-Redirect'] = url_for('character_edit.charedit_show', username=username, url_name=url_name)
        if request.values.get('sheet_context') == 'inline':
            return render_template('partial/charview/portrait.html', character=character,
                                   username=username, url_name=url_name, is_owner=True,
                                   portrait_src=character_portrait_link(character))
        return response
    data = request.form
    custom_url = data['custom-url']
    selected_portrait = data['selected-portrait']
    if custom_url != None and custom_url != "":
        if not is_url_image(custom_url):
            print("Bad image url!!!", custom_url)
        else:
            setattr(character,"image_url", custom_url)
            setattr(character,"custom_image",True)
            db.session.commit()    
    elif selected_portrait != "" and selected_portrait != None:
        setattr(character,"image_url", selected_portrait)
        setattr(character,"custom_image",False)
        db.session.commit()    
    delete_unreferenced_portrait(previous_portrait)
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = "/charedit/"+username+"/"+url_name
    if request.values.get('sheet_context') == 'inline':
        return render_template('partial/charview/portrait.html', character=character,
                               username=username, url_name=url_name, is_owner=True,
                               portrait_src=character_portrait_link(character))
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
@login_required
def charedit_rest(username, url_name):
    user, character = get_char_data(username, url_name)
    if character.owner != current_user.id:
        abort(403)
    setattr(character,"hp",character.hp_max)
    db.session.commit()
    return render_template('partial/charview/stats.html', user=user, character=character, username=username, url_name=url_name, is_owner=True, stat_form=FlaskForm())


@character_edit.route('/charedit/<username>/<url_name>/stats', methods=['GET'])
def character_stats(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(owner=user.id, url_name=url_name).first_or_404()
    is_owner = current_user.is_authenticated and current_user.id == character.owner
    response = make_response(render_template('partial/charview/stats.html', character=character,
                             username=username, url_name=url_name, is_owner=is_owner, stat_form=FlaskForm()))
    response.headers['Cache-Control'] = 'no-store'
    return response


@character_edit.route('/charedit/<username>/<url_name>/stat', methods=['POST'])
@login_required
def character_stat_save(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(owner=user.id, url_name=url_name).first_or_404()
    if character.owner != current_user.id:
        abort(403)
    return save_character_stat(character)

# Route: roll omens on omen edit
@character_edit.route('/charedit/omen-roll/<username>/<url_name>', methods=['POST'])
def charedit_omen_roll(username, url_name):
    user, character = get_char_data(username, url_name)
    omens = load_omens()
    data = request.form
    result = roll_list(omens)
    if data["omens"] != "":
        result = data["omens"] + "\n \n" + _(result)
    else:
        result = _(result)
    response = make_response(result)
    response.headers["HX-Trigger-After-Settle"] = 'omen-roll'
    return response

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

@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/move', methods=['POST'])
def charedit_inplace_inventory_move(username, url_name):
    _, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    try:
        slot = int(request.form['slot'])
    except (KeyError, ValueError):
        abort(400)
    inventory.place_item(request.form.get('item_id'), slot)
    inventory.decorate()
    return render_template('partial/charview/inventory_slots.html', character=character,
                           username=username, url_name=url_name, inventory=inventory)


# Route: remove inventory item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/item-delete/<item_id>', methods=['POST'])
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
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/<container_id>/fatigue', methods=['POST'])
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
    if request.args.get('container', '').isdigit():
        inventory.select(int(request.args['container']))
    inventory.decorate()
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    if mode == "edit":
        item = inventory.get_item(item_id)
    else:
        item = None
    return render_template('partial/modal/edit_item.html', user=user, character=character, username=username, url_name=url_name, 
                           inventory=inventory, item=item, mode=mode, library=Market().buy([it["name"] for it in load_market()]),
                           party_containers=json.loads(party.containers or '[]') if
                           (party := db.session.get(Party, character.party_id)) and
                           character.id in json.loads(party.members or '[]') else [])

# Route: edit item save
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/save', methods=['POST'])
def charedit_inplace_inventory_item_edit_save(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    data = request.form
    mode = request.args.get('mode')
    if mode == None or mode == "":
        mode = "edit"
    destination = data["edit_item_container"]
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
    elif destination.startswith('party:'):
        if not can_transfer_from(character):
            abort(403)
        if mode != 'edit':
            abort(400)
        source = inventory.get_item(item_id)
        if source is None:
            abort(404)
        try:
            party_container = int(destination.removeprefix('party:'))
        except ValueError:
            abort(400)
        from werkzeug.exceptions import HTTPException
        try:
            # Persist the edits and transfer together; a rejected destination
            # must leave both inventories unchanged.
            inventory.update_item(item_id, data["edit_item_name"], data["edit_item_tags"],
                                  data["edit_item_uses"], data["edit_item_charges"],
                                  data["edit_item_max_charges"], source['location'],
                                  data["edit_item_description"],
                                  armor_active=data.get("edit_item_armor_active") == "on", commit=False)
            inventory.move_item_to_party(item_id, party_container)
        except HTTPException as error:
            db.session.rollback()
            response = make_response(render_template('partial/inventory_error.html', message=error.description))
            response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
            return response
        inventory.select(source['location'])
    elif mode == "edit":
        item = inventory.update_item(item_id,data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on")
        inventory.select(int(item["location"]))
    else:
        item = inventory.create_item(data["edit_item_name"],data["edit_item_tags"],data["edit_item_uses"],
                                     data["edit_item_charges"], data["edit_item_max_charges"], data["edit_item_container"],
                                     data["edit_item_description"], armor_active=data.get("edit_item_armor_active") == "on", commit=False)
        if item is None:
            response = make_response(render_template('partial/inventory_error.html',
                message=_('The item does not fit in this container.')))
            response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
            return response
        inventory.select(int(item["location"]))
        requested_slot = data.get('edit_item_slot', '')
        if requested_slot.isdigit() and str(item['location']) == data.get('slot_container'):
            from app.lib.inventory_slots import item_size
            size = item_size(item)
            if size:
                last_slot = int(inventory.selected_container['slots']) - size
                from werkzeug.exceptions import HTTPException
                try:
                    inventory.place_item(item['id'], min(int(requested_slot), last_slot), commit=False)
                except HTTPException as error:
                    db.session.rollback()
                    response = make_response(render_template('partial/inventory_error.html', message=error.description))
                    response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
                    return response
        db.session.commit()
    inventory.decorate()
    render = render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name,inventory=inventory)    
    response = make_response(render)
    response.headers["HX-Trigger"] = "refresh-stats"
    return response
    
    
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/uses', methods=['POST'])
def charedit_inplace_inventory_item_uses(username, url_name, item_id):
    _, character = get_char_data(username, url_name)
    items = json.loads(character.items)
    item = next((item for item in items if str(item['id']) == item_id), None)
    if item is None:
        abort(404)
    if 'uses' not in item.get('tags', []):
        abort(400)
    maximum = max(1, item.get('max_uses', item.get('uses', 0)), item.get('uses', 0))
    try:
        uses = int(request.form['uses'])
    except (KeyError, ValueError):
        abort(400)
    if not 0 <= uses <= maximum:
        abort(400)
    item['uses'], item['max_uses'] = uses, maximum
    character.items = json.dumps(items)
    db.session.commit()
    inventory = Inventory(character)
    inventory.select(item['location'])
    inventory.decorate()
    return render_template('partial/charview/inventory_slots.html', character=character,
                           username=username, url_name=url_name, inventory=inventory)


# Route: change some amount property in item
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/amount', methods=['POST'])
def charedit_inplace_inventory_item_edit_amount(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    inventory = Inventory(character)
    prop = request.args.get('property')
    action = request.args.get('action')
    item = inventory.change_amount(item_id, action, prop)
    if "location" in item:
        inventory.select(item["location"])
    inventory.decorate()
    return render_template('partial/charedit/inventory.html', user=user, character=character, username=username, url_name=url_name, inventory=inventory)    

# Route: move item to party storage
@character_edit.route('/charedit/inplace-inventory/<username>/<url_name>/item-edit/<item_id>/party', methods=['POST'])
@login_required
def charedit_inplace_inventory_item_edit_party(username, url_name, item_id):
    user, character = get_char_data(username, url_name)
    if not can_transfer_from(character):
        abort(403)
    inventory = Inventory(character)
    source = inventory.get_item(item_id)
    if source is None:
        abort(404)
    source_container = source['location']
    destination = request.form.get('party_container', '0')
    try:
        destination = int(destination)
    except ValueError:
        abort(400)
    from werkzeug.exceptions import HTTPException
    try:
        inventory.move_item_to_party(item_id, destination)
    except HTTPException as error:
        response = make_response(render_template('partial/inventory_error.html', message=error.description))
        response.headers['HX-Retarget'] = '#add-edit-item-modal-error-text'
        return response
    inventory.select(source_container)
    inventory.decorate()
    response = make_response(render_template('partial/charedit/inventory.html', user=user, character=character,
                             username=username, url_name=url_name, inventory=inventory))
    response.headers['HX-Trigger'] = 'refresh-stats'
    return response


@character_edit.get('/portraits/<filename>')
def uploaded_portrait(filename):
    import re
    from app.lib.portraits import portrait_directory
    if not re.fullmatch(r'[0-9a-f]{64}\.webp', filename):
        abort(404)
    response = send_from_directory(portrait_directory(), filename, mimetype='image/webp', max_age=31536000)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

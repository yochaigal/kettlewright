

# Character creation blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import *
from unidecode import unidecode
from flask_babel import _
from flask_babel import lazy_gettext as _l
import urllib.parse
import json

character_create = Blueprint('character_create', __name__)

def rebuild_names(names):
    result = [('', _l('Name (d10)...')), ('Custom', _l('** Custom **'))]
    for name in names:
        result.append((name, name))
    return result

def rebuild_all_names():
    backgrounds = load_backgrounds()
    result = [('', _l('Name (d10)...')), ('Custom', _l('** Custom **'))]
    for bkg in backgrounds:
        for name in backgrounds[bkg]['names']:
            result.append((name, name))
    return result

def get_background(form):
    bkgs = load_backgrounds()
    if form.background.data != '' and form.background.data != 'Custom':
        return bkgs[form.background.data]
    return None

def update_name_choices(form):
    background=get_background(form)
    if background != None:
        form.name.choices = rebuild_names(background['names'])
    else:
        form.name.choices = rebuild_all_names()
        
def get_custom_fields(data):
    result = {}
    names = ["background_table1_select", "background_table2_select", "age","bonds_selected","omens_selected",
             "armor","gold","bonus_gold_t1", "bonus_gold_t2", "bonus_gold_bond","items","bond_items",
             "Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    for n in names:
        if n in data:
            result[n] = data[n]
        else:
            result[n] = None            
    return result

# Fill all needed data from request
def process_form_data(data):
    form = CharacterForm(formdata=data)
    custom_fields = get_custom_fields(data)
    background = get_background(form)
    if background != None:
        form.custom_background.process_data("")
        form.name.choices = rebuild_names(background['names'])
    else:
        form.name.choices = rebuild_all_names()
    custom_fields['background'] = background
    custom_fields['traits'] = load_traits()
    custom_fields['bonds'] = load_bonds()
    custom_fields['omens'] = load_omens()
    custom_fields['bonds_selected'] = data['bonds_select']
    custom_fields['omens_selected'] = data['omens_select']
    character = DummyCharacter()    
    if custom_fields['items'] != None and custom_fields['items'] != '':
        character.items = custom_fields['items']
    inventory = Inventory(character)
    inventory.decorate()
    custom_fields['inventory'] = inventory
    return form, custom_fields, background
    
 
 # update items in inventory
def update_items(custom_fields,items):
    if custom_fields['inventory']:
        custom_fields['inventory'].remove_items(0)
        for it in items:
            if not "tags" in it:
                it['tags'] = []
            item = custom_fields['inventory'].create_item(sdv(it,'name'),",".join(sdv(it,'tags',[])),sdv(it,'uses'),
                                                    sdv(it,'charges'), sdv(it,'max_charges'),0,sdv(it,'description'))            
    if custom_fields['bond_items']:
        bitems = json.loads(custom_fields['bond_items'])
        for it in bitems:
            if not "tags" in it:
                it['tags'] = []
            item = custom_fields['inventory'].create_item(sdv(it,'name'),",".join(sdv(it,'tags',[])),sdv(it,'uses'),
                                                    sdv(it,'charges'), sdv(it,'max_charges'),0,sdv(it,'description'))            
    custom_fields['items'] = json.dumps(custom_fields['inventory'].get_items_for_container(0, False))
    custom_fields['inventory'].select(0)
    custom_fields['inventory'].decorate()
    custom_fields['armor'] = custom_fields['inventory'].compute_armor()
    
    
# update additional gold
def update_gold(custom_fields, field, gold):
    if not gold or gold == "":
        custom_fields[field] = 0
        return 0    
    custom_fields[field] = gold 
    return gold  
   
# Route: edit new character portrait
@character_create.route('/charcreo/portrait', methods=['GET'])
def charedit_inplace_portrait():
    portrait_src = request.args.get('src')
    images = load_images()
    custom_image = request.args.get("custom_image")
    portrait_src = urllib.parse.quote_plus(portrait_src)
    return render_template('partial/charcreo/portrait.html', images=images, portrait_src=portrait_src, custom_image=custom_image)

# Route: edit new character portrait - cancel
@character_create.route('/charcreo/portrait/cancel', methods=['GET'])
def charcreo_portrait_cancel():
    portrait_src = ""
    ps = request.args.get("src")
    if ps != None and ps != "":
        portrait_src = ps
    portrait_src = urllib.parse.quote_plus(portrait_src)
    custom_image = request.args.get("custom_image")
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image)          

# Route: edit new character portrait - save
@character_create.route('/charcreo/portrait/save', methods=['POST'])
def charcreo_portrait_save():
    data = request.form
    custom_url = data['custom-url']
    selected_portrait = data['selected-portrait']
    portrait_src = "/static/images/portraits/default-portrait.webp"
    if custom_url != None and custom_url != "":
        if not is_url_image(custom_url):
            print("Bad image url!!!", custom_url)
        else:
            portrait_src = custom_url
            custom_image = True
    elif selected_portrait != "" and selected_portrait != None:
            portrait_src = "/static/images/portraits/"+selected_portrait
            custom_image = False
    portrait_src = urllib.parse.quote_plus(portrait_src)
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image)        


# route: select background
@character_create.route('/charcreo/select-background', methods=['POST'])
def charcreo_select_background():
    form, custom_fields, background = process_form_data(request.form)
    if background != None:
        form.name.process_data('')
        update_items(custom_fields,background['starting_gear'])
    else:
        update_items(custom_fields,[])
    custom_fields["background_table1_select"] = None
    custom_fields["background_table2_select"] = None
    render = render_template('partial/charcreo/fields.html', form=form,custom_fields=custom_fields)
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response
    
# route: roll background
@character_create.route('/charcreo/roll-background', methods=['POST'])
def charcreo_roll_background():
    form, custom_fields, background = process_form_data(request.form)
    bkgs = load_backgrounds()
    key, background = roll_dict(bkgs)
    form.background.process_data(key)
    form.custom_background.process_data("")
    form.name.choices = rebuild_names(background['names'])
    form.name.process_data('')
    custom_fields['background'] = background
    update_items(custom_fields,background['starting_gear'])
    custom_fields["background_table1_select"] = None
    custom_fields["background_table2_select"] = None  
    
    render = render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields)
    response = make_response(render)    
    response.headers['HX-Trigger'] = "background-changed"
    return response
    
# route: select name
@character_create.route('/charcreo/select-name', methods=['POST'])
def charcreo_select_name():
    form, custom_fields, background = process_form_data(request.form)
    return render_template('partial/charcreo/fields.html', form=form,custom_fields=custom_fields)    

# route: roll name
@character_create.route('/charcreo/roll-name', methods=['POST'])
def charcreo_roll_name():
    form, custom_fields, background = process_form_data(request.form)
    lst = form.name.choices[2:]     
    name,_ = roll_list(lst)            
    form.name.process_data(name)    
    return render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields)    

# route: select background table
@character_create.route('/charcreo/bkg-table-select/<num>', methods=['POST'])
def charcreo_bkg_table_select(num):
    form, custom_fields, background = process_form_data(request.form)
    items = []
    if background:
        items = background['starting_gear']
    opt = None
    gfield = None
    match num:
        case "1":
            opt = find_background_table_option(background,'table1',custom_fields['background_table1_select'])
            gfield = 'bonus_gold_t1'
        case "2":
            opt = find_background_table_option(background,'table2',custom_fields['background_table2_select'])
            gfield = 'bonus_gold_t2'
    if opt:
        items.extend(sdv(opt,'items',[]))
        update_items(custom_fields, items)
        if gfield:
            update_gold(custom_fields, gfield ,sdv(opt, 'bonus_gold',0))        
    render =  render_template('partial/charcreo/fields.html', form=form,custom_fields=custom_fields )
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response


# route: roll background table
@character_create.route('/charcreo/bkg-table-roll/<nr>', methods=['POST'])
def charcreo_bkg_table_roll(nr):
    form, custom_fields, background = process_form_data(request.form)
    items = []
    if background:
        items = background['starting_gear']
    if nr == "1":
        lst = background['table1']['options']
        field="background_table1_select"        
    else:
        lst = background['table2']['options']
        field="background_table2_select"
    opt=roll_list(lst)
    if 'items' in opt:
        items.extend(opt['items'])
    update_items(custom_fields, items)   
    update_gold(custom_fields, sdv(opt, 'bonus_gold',0))                    
    custom_fields[field]=opt['description']
    render = render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields )
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response

# route: roll attribute
@character_create.route('/charcreo/attr-roll/<atype>', methods=['POST'])
def charcreo_attr_roll(atype):
    form, custom_fields, background = process_form_data(request.form)
    match atype:
        case "str":
            _, total = roll_multi_dice(6,3)
            # hack, because flask cannot change numeric field
            form.strength_max.data = total
            form.strength_max.raw_data = None
        case "dex":
            _, total = roll_multi_dice(6,3)
            form.dexterity_max.data = total
            form.dexterity_max.raw_data = None
        case "wil":
            _, total = roll_multi_dice(6,3)
            form.willpower_max.data = total
            form.willpower_max.raw_data = None            
        case "hp":
            _, total = roll_multi_dice(6,1)
            form.hp_max.data = total
            form.hp_max.raw_data = None                    
    return render_template('partial/charcreo/attrs.html', form=form,custom_fields=custom_fields )

# route: swap attributes
@character_create.route('/charcreo/attr-swap', methods=['POST'])
def charcreo_swap_attr():
    data = request.form
    form, custom_fields, background = process_form_data(data)
    attr1 = data['swap_attribute_1']
    attr2 = data['swap_attribute_2']
    if attr1 != "" and attr2 != "":
        match attr1:
            case "str":
                match attr2:
                    case "dex":
                        v = form.dexterity_max.data
                        form.dexterity_max.data = form.strength_max.data
                        form.strength_max.data = v
                        form.strength_max.raw_data = None
                        form.dexterity_max.raw_data = None
                    case "wil":
                        v = form.willpower_max.data
                        form.willpower_max.data = form.strength_max.data
                        form.strength_max.data = v
                        form.strength_max.raw_data = None
                        form.willpower_max.raw_data = None
            case "dex":
                match attr2:
                    case "str":
                        v = form.dexterity_max.data
                        form.dexterity_max.data = form.strength_max.data
                        form.strength_max.data = v
                        form.strength_max.raw_data = None
                        form.dexterity_max.raw_data = None
                    case "wil":
                        v = form.willpower_max.data
                        form.willpower_max.data = form.dexterity_max.data
                        form.dexterity_max.data = v
                        form.willpower_max.raw_data = None
                        form.dexterity_max.raw_data = None
            case "wil":
                match attr2:
                    case "str":
                        v = form.strength_max.data
                        form.strength_max.data = form.willpower_max.data
                        form.willpower_max.data = v
                        form.strength_max.raw_data = None
                        form.willpower_max.raw_data = None
                    case "dex":
                        v = form.willpower_max.data
                        form.willpower_max.data = form.dexterity_max.data
                        form.dexterity_max.data = v            
                        form.willpower_max.raw_data = None
                        form.dexterity_max.raw_data = None
    return render_template('partial/charcreo/attrs.html', form=form,custom_fields=custom_fields )


# route: select trait
@character_create.route('/charcreo/trait-select/<ttype>', methods=['POST'])
def charcreo_trait_select(ttype):
    form, custom_fields, background = process_form_data(request.form)
    names = ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    tts = []
    for n in names:
        tts.append(TraitValue(n, custom_fields[n]))
    form.traits.process_data(traits_text(0, tts))
    return render_template('partial/charcreo/traits.html', form=form,custom_fields=custom_fields )

# route: roll traits
@character_create.route('/charcreo/trait-roll', methods=['POST'])
def charcreo_trait_roll():
    form, custom_fields, background = process_form_data(request.form)
    names = ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    tts = []
    for n in names:
        custom_fields[n] = roll_list(custom_fields['traits'][n])
        tts.append(TraitValue(n, custom_fields[n]))
    form.traits.process_data(traits_text(0, tts))
    return render_template('partial/charcreo/traits.html', form=form,custom_fields=custom_fields )

# route: age roll
@character_create.route('/charcreo/age-roll', methods=['POST'])
def charcreo_age_roll():
    form, custom_fields, background = process_form_data(request.form)
    _, total = roll_multi_dice(20,2)
    custom_fields['age'] = total + 10
    return render_template('partial/charcreo/abo.html', form=form,custom_fields=custom_fields )

# route: select bond or omen
@character_create.route('/charcreo/bonds-omen-select/<tp>', methods=['POST'])
def charcreo_bonds_select(tp):
    form, custom_fields, background = process_form_data(request.form)    
    if tp == 'b':
        bond = find_bond_by_description(custom_fields['bonds_selected'])
        print('bond',bond)
        if bond:
            update_gold(custom_fields,'bonus_gold_bond',sdv(bond,'gold',0))
            custom_fields['bond_items'] = json.dumps(sdv(bond,'items',[]))                       
        else:
            custom_fields['bond_items'] = '[]'
        if background:
            update_items(custom_fields, background['starting_gear'])
        else:
            update_items(custom_fields, []) 
    render = render_template('partial/charcreo/abo_oob.html', form=form,custom_fields=custom_fields )            
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "bond-changed"
    return response

# route: bond roll
@character_create.route('/charcreo/bond-roll', methods=['POST'])
def charcreo_bond_roll():
    form, custom_fields, background = process_form_data(request.form)
    b = roll_list(load_bonds())
    custom_fields['bonds_selected'] = b['description']
    update_gold(custom_fields,'bonus_gold_bond',sdv(b,'gold',0))
    custom_fields['bond_items'] = json.dumps(sdv(b,'items',[]))
    if background:
        update_items(custom_fields, background['starting_gear'])            
    else:
        update_items(custom_fields, []) 
    render = render_template('partial/charcreo/abo_oob.html', form=form,custom_fields=custom_fields )
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "bond-changed"
    return response

# route: omen roll
@character_create.route('/charcreo/omen-roll', methods=['POST'])
def charcreo_omen_roll():
    form, custom_fields, background = process_form_data(request.form)
    o = roll_list(load_omens())
    custom_fields['omens_selected'] = o
    return render_template('partial/charcreo/abo.html', form=form,custom_fields=custom_fields )

# route: gold roll
@character_create.route('/charcreo/gold-roll', methods=['POST'])
def charcreo_gold_roll():
    form, custom_fields, background = process_form_data(request.form)
    _, total = roll_multi_dice(6,3)
    custom_fields['gold'] = total
    return render_template('partial/charcreo/items.html', form=form,custom_fields=custom_fields )

# route: refresh items
@character_create.route('/charcreo/refresh-items', methods=['POST'])
def charcreo_refresh_items():
    form, custom_fields, background = process_form_data(request.form)
    return render_template('partial/charcreo/items.html', form=form,custom_fields=custom_fields )
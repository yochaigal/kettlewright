

# Character creation blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import create_unique_url_name
from app.lib import *
from unidecode import unidecode
from flask_babel import _
from flask_babel import lazy_gettext as _l
import urllib.parse
import json
from flask_login import login_required, current_user


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
    if form.background.data and form.background.data != '' and form.background.data != 'Custom':
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
    names = ["background_table1_select", "background_table2_select", "age","bonds_selected","omens_selected","containers",
             "armor","gold","bonus_gold_t1", "bonus_gold_t2", "bonus_gold_bond","items","bond_items", "t1_items","t2_items","bkg_items",
             "selected-portrait","Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice", "portrait_src","custom_image"]
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
    if custom_fields['containers'] != None and custom_fields['containers'] != '':
        character.containers = custom_fields['containers']
    inventory = Inventory(character)
    inventory.decorate()
    custom_fields['inventory'] = inventory
    return form, custom_fields, background


def process_dict_data(data):
    form = CharacterForm(data=data)
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
    if custom_fields['containers'] != None and custom_fields['containers'] != '':
        character.containers = custom_fields['containers']        
    inventory = Inventory(character)
    inventory.decorate()
    custom_fields['inventory'] = inventory
    return form, custom_fields, background


# update items in inventory
def update_items(custom_fields):
    if custom_fields['inventory']:
        custom_fields['inventory'].remove_items(0)
    for cat in ["bond_items","t1_items","t2_items","bkg_items"]:
        if custom_fields[cat]:
            bitems = json.loads(custom_fields[cat])
            for it in bitems:
                if not "tags" in it:
                    it['tags'] = []
                custom_fields['inventory'].create_item(sdv(it,'name'),",".join(sdv(it,'tags',[])),sdv(it,'uses'),
                                                    sdv(it,'charges'), sdv(it,'max_charges'),0,sdv(it,'description'))            
    custom_fields['items'] = json.dumps(custom_fields['inventory'].get_items_for_container(0, False))
    custom_fields['inventory'].select(0)
    custom_fields['inventory'].decorate()
    custom_fields['armor'] = custom_fields['inventory'].compute_armor()
    
def update_containers(custom_fields, conts):
    if custom_fields['inventory']:
        custom_fields['inventory'].containers = [{"name": "Main", "slots": 10, "id": 0}]
        for c in conts:
            if 'id' in c and int(c['id']) == 0:
                continue
            custom_fields['inventory'].add_container(sdv(c,'name','?'),sdv(c,'slots',0),None,None)            
    custom_fields['containers'] = json.dumps(custom_fields['inventory'].get_containers_wo_items())
            
    
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
    custom_fields = {}
    custom_fields['portrait_src'] = portrait_src
    custom_fields['custom_image'] = custom_image
    portrait_src = urllib.parse.quote_plus(portrait_src)
    return render_template('partial/charcreo/portrait.html', images=images, portrait_src=portrait_src, custom_image=custom_image, custom_fields=custom_fields)

# Route: edit new character portrait - cancel
@character_create.route('/charcreo/portrait/cancel', methods=['GET'])
def charcreo_portrait_cancel():
    portrait_src = ""
    ps = request.args.get("src")
    if ps != None and ps != "":
        portrait_src = ps
    portrait_src = urllib.parse.quote_plus(portrait_src)
    custom_image = request.args.get("custom_image")
    custom_fields = {}
    custom_fields['portrait_src'] = portrait_src
    custom_fields['custom_image'] = custom_image
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image, custom_fields=custom_fields)          

# Route: edit new character portrait - save
@character_create.route('/charcreo/portrait/save', methods=['POST'])
def charcreo_portrait_save():
    data = request.form
    custom_url = data['custom-url']
    selected_portrait = data['selected-portrait']
    portrait_src = "default-portrait.webp"
    if custom_url != None and custom_url != "":
        if not is_url_image(custom_url):
            print("Bad image url!!!", custom_url)
        else:
            portrait_src = custom_url
            custom_image = "true"
    elif selected_portrait != "" and selected_portrait != None:
            portrait_src = selected_portrait
            custom_image = "false"
    portrait_src = urllib.parse.quote_plus(portrait_src)
    custom_fields = {}
    custom_fields['portrait_src'] = portrait_src
    custom_fields['custom_image'] = custom_image
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image, custom_fields=custom_fields)        


# route: select background
@character_create.route('/charcreo/select-background', methods=['POST'])
def charcreo_select_background():
    form, custom_fields, background = process_form_data(request.form)
    if background != None:
        form.name.process_data('')
        custom_fields['bkg_items'] = json.dumps(sdv(background,'starting_gear',[]))
        update_items(custom_fields)
        update_containers(custom_fields,sdv(background,'starting_containers',[]))
    else:
        update_items(custom_fields)
    custom_fields["background_table1_select"] = None
    custom_fields["background_table2_select"] = None
    custom_fields['t1_items'] = '[]'
    custom_fields['t2_items'] = '[]'
    render = render_template('partial/charcreo/fields.html', form=form,custom_fields=custom_fields)
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response
    
# route: roll background
@character_create.route('/charcreo/roll-background', methods=['POST'])
def charcreo_roll_background():
    form, custom_fields, background = process_form_data(request.form)
    key, background = random_background()
    form.background.process_data(key)
    form.custom_background.process_data("")
    form.name.choices = rebuild_names(background['names'])
    form.name.process_data('')
    custom_fields['background'] = background
    custom_fields['bkg_items'] = json.dumps(sdv(background,'starting_gear',[]))
    update_items(custom_fields)
    update_containers(custom_fields,sdv(background,'starting_containers',[]))
    custom_fields["background_table1_select"] = None
    custom_fields["background_table2_select"] = None  
    custom_fields['t1_items'] = '[]'
    custom_fields['t2_items'] = '[]'
    render = render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields)
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response
    
# route: select name
@character_create.route('/charcreo/select-name', methods=['POST'])
def charcreo_select_name():
    form, custom_fields, _ = process_form_data(request.form)
    return render_template('partial/charcreo/fields.html', form=form,custom_fields=custom_fields)    

# route: roll name
@character_create.route('/charcreo/roll-name', methods=['POST'])
def charcreo_roll_name():
    form, custom_fields, _ = process_form_data(request.form)
    lst = form.name.choices[2:]     
    name,_ = roll_list(lst)            
    form.name.process_data(name)    
    return render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields)    

# route: select background table
@character_create.route('/charcreo/bkg-table-select/<num>', methods=['POST'])
def charcreo_bkg_table_select(num):
    form, custom_fields, background = process_form_data(request.form)
    containers = []
    opt = None
    gfield = None
    match num:
        case "1":
            opt = find_background_table_option(background,'table1',custom_fields['background_table1_select'])
            gfield = 'bonus_gold_t1'
            custom_fields['t1_items'] = json.dumps(sdv(opt,'items',[]))
        case "2":
            opt = find_background_table_option(background,'table2',custom_fields['background_table2_select'])
            gfield = 'bonus_gold_t2'
            custom_fields['t2_items'] = json.dumps(sdv(opt,'items',[]))
    if opt:
        containers.extend(sdv(opt,'containers',[]))
        update_items(custom_fields)
        update_containers(custom_fields,containers)
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
    containers = []
    if nr == "1":
        lst = background['table1']['options']
        field="background_table1_select"
        gfield = 'bonus_gold_t1'          
    else:
        lst = background['table2']['options']
        field="background_table2_select"
        gfield = 'bonus_gold_t2'
        custom_fields['t2_items'] = sdv(opt,'items',[])
    opt=roll_list(lst)
    if nr == "1":
        custom_fields['t1_items'] = json.dumps(sdv(opt,'items',[]))
    else:
        custom_fields['t2_items'] = json.dumps(sdv(opt,'items',[]))
    containers.extend(sdv(opt,'containers',[]))
    update_items(custom_fields)   
    update_containers(custom_fields, containers)   
    update_gold(custom_fields,gfield,sdv(opt, 'bonus_gold',0))                    
    custom_fields[field]=opt['description']
    render = render_template('partial/charcreo/fields.html', form=form, custom_fields=custom_fields )
    response = make_response(render)    
    response.headers['HX-Trigger-After-Settle'] = "background-changed"
    return response

# route: roll attribute
@character_create.route('/charcreo/attr-roll/<atype>', methods=['POST'])
def charcreo_attr_roll(atype):
    form, custom_fields, _ = process_form_data(request.form)
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
    form, custom_fields, _ = process_form_data(data)
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
    form, custom_fields, _ = process_form_data(request.form)
    names = ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    tts = []
    for n in names:
        tts.append(TraitValue(n, custom_fields[n]))
    form.traits.process_data(traits_text(0, tts))
    return render_template('partial/charcreo/traits.html', form=form,custom_fields=custom_fields )

# route: roll traits
@character_create.route('/charcreo/trait-roll', methods=['POST'])
def charcreo_trait_roll():
    form, custom_fields, _ = process_form_data(request.form)
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
    form, custom_fields, _ = process_form_data(request.form)
    _, total = roll_multi_dice(20,2)
    custom_fields['age'] = total + 10
    return render_template('partial/charcreo/abo.html', form=form,custom_fields=custom_fields )

# route: select bond or omen
@character_create.route('/charcreo/bonds-omen-select/<tp>', methods=['POST'])
def charcreo_bonds_select(tp):
    form, custom_fields, background = process_form_data(request.form)    
    if tp == 'b':
        bond = find_bond_by_description(custom_fields['bonds_selected'])
        if bond:
            update_gold(custom_fields,'bonus_gold_bond',sdv(bond,'gold',0))
            custom_fields['bond_items'] = json.dumps(sdv(bond,'items',[]))                       
        else:
            custom_fields['bond_items'] = '[]'
        if background:
            update_items(custom_fields, background['starting_gear'])
        else:
            update_items(custom_fields, []) 
    form.omens.process_data(custom_fields['omens_selected'])
    form.bonds.process_data(custom_fields['bonds_selected'])
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
    form.bonds.process_data(custom_fields['bonds_selected'])
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
    form, custom_fields, _ = process_form_data(request.form)
    o = roll_list(load_omens())
    custom_fields['omens_selected'] = o
    form.omens.process_data(custom_fields['omens_selected'])
    return render_template('partial/charcreo/abo.html', form=form,custom_fields=custom_fields )

# route: gold roll
@character_create.route('/charcreo/gold-roll', methods=['POST'])
def charcreo_gold_roll():
    form, custom_fields, _ = process_form_data(request.form)
    _, total = roll_multi_dice(6,3)
    custom_fields['gold'] = total
    return render_template('partial/charcreo/items.html', form=form,custom_fields=custom_fields )

# route: refresh items
@character_create.route('/charcreo/refresh-items', methods=['POST'])
def charcreo_refresh_items():
    form, custom_fields, _ = process_form_data(request.form)
    return render_template('partial/charcreo/items.html', form=form,custom_fields=custom_fields )

# route: roll all character data
@character_create.route('/charcreo/roll-all', methods=['GET'])
def charcreo_roll_all():
    # roll values
    data = {}
    containers = []
    key, background = random_background()
    name = random_name(background)
    data['bkg_items'] = json.dumps(sdv(background,'starting_gear',[]))
    containers.extend(sdv(background, 'starting_containers',[]))
    data['background'] = key
    data['name'] = name
    t1 = random_table_option(background, 'table1')
    t2 = random_table_option(background, 'table2')
    data['t1_items'] = json.dumps(sdv(t1,'items',[]))
    data['t2_items'] = json.dumps(sdv(t2,'items',[]))
    data['background_table1_select'] = t1['description']
    data['background_table2_select'] = t2['description']
    bond = roll_list(load_bonds())
    data['bonds_select'] = bond['description']
    data['bond_items'] = json.dumps(sdv(bond,'items',[]))
    omen = roll_list(load_omens())
    data['omens_select'] = omen   
    update_gold(data,'bonus_gold_bond',sdv(bond,'gold',0)) 
    update_gold(data, "bonus_gold_t1" ,sdv(t1, 'bonus_gold',0))
    update_gold(data, "bonus_gold_t2" ,sdv(t2, 'bonus_gold',0))
    _, total = roll_multi_dice(6,3)
    data['gold'] = total
    _, total = roll_multi_dice(20,2)
    data['age'] = total + 10 
    
    # prepare form 
    form, custom_fields, background = process_dict_data(data)
    custom_fields['containers'] = '[{"name": "Main", "slots": 10, "id": 0}]'
    update_items(custom_fields) 
    update_containers(custom_fields, containers)   
    tnames = ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    tts = []
    for n in tnames:
        custom_fields[n] = roll_list(custom_fields['traits'][n])
        tts.append(TraitValue(n, custom_fields[n]))
    form.traits.process_data(traits_text(0, tts))
    _, total = roll_multi_dice(6,3)
    form.strength_max.data = total
    form.strength_max.raw_data = None
    _, total = roll_multi_dice(6,3)
    form.dexterity_max.data = total
    form.dexterity_max.raw_data = None
    _, total = roll_multi_dice(6,3)
    form.willpower_max.data = total
    form.willpower_max.raw_data = None            
    _, total = roll_multi_dice(6,1)
    form.hp_max.data = total
    form.hp_max.raw_data = None 
    image = roll_list(load_images())
    custom_fields['portrait_src'] = image
    custom_fields['custom_image'] = 'false'
    form.omens.process_data(custom_fields['omens_selected'])
    form.bonds.process_data(custom_fields['bonds_selected'])
    
    render = render_template('partial/charcreo/body.html', form=form, custom_fields=custom_fields, portrait_src=custom_fields['portrait_src'], custom_image=custom_fields['custom_image'])
    response = make_response(render)    
    return response


form_attr = {
    "str": "strength_max",
    "dex": "dexterity_max",
    "wil": "willpower_max",
    "hp": "hp_max"
}

DEFAULT_PORTRAIT = urllib.parse.quote_plus("/static/images/portraits/default-portrait.webp")

# route: roll remaining character data
@character_create.route('/charcreo/roll-remaining', methods=['POST'])
def charcreo_roll_remaining():
    form, custom_fields, background = process_form_data(request.form)
    custom_fields['containers'] = '[{"name": "Main", "slots": 10, "id": 0}]'
    containers = []
    if not custom_fields['background']:
        key, background = random_background()
        custom_fields['background'] = background
        custom_fields['background_table1_select'] = None
        custom_fields['background_table2_select'] = None
        custom_fields['bkg_items'] = json.dumps(sdv(background,'starting_gear',[]))
        containers.extend(sdv(background,'starting_containers',[]))
        update_items(custom_fields)
        form.background.process_data(key)
        form.custom_background.process_data("")
        form.name.choices = rebuild_names(background['names'])
    if not form.name.data or form.name.data == '':        
        form.name.process_data(random_name(background))
    if not custom_fields['background_table1_select']:
        lst = background['table1']['options']
        opt=roll_list(lst)
        custom_fields['t1_items'] = json.dumps(sdv(opt,'items',[]))
        containers.extend(sdv(opt,'containers',[]))    
        update_items(custom_fields)   
        update_gold(custom_fields,'bonus_gold_t1',sdv(opt, 'bonus_gold',0))                    
        custom_fields['background_table1_select']=opt['description']
    if not custom_fields['background_table2_select']:
        lst = background['table2']['options']
        opt=roll_list(lst)
        custom_fields['t2_items'] = json.dumps(sdv(opt,'items',[]))
        containers.extend(sdv(opt,'containers',[]))    
        update_items(custom_fields)   
        update_gold(custom_fields,'bonus_gold_t2',sdv(opt, 'bonus_gold',0))                    
        custom_fields['background_table2_select']=opt['description']
    for atype in ['str','dex','wil','hp']:
        if not form[form_attr[atype]].data or form[form_attr[atype]].data == '':
            match atype:
                case "str":
                    _, total = roll_multi_dice(6,3)
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
    update_containers(custom_fields, containers)
    names = ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
    tts = []
    for n in names:
        if not custom_fields[n] or custom_fields[n] == '' or custom_fields[n] == '___':
            custom_fields[n] = roll_list(custom_fields['traits'][n])
        tts.append(TraitValue(n, custom_fields[n]))
    form.traits.process_data(traits_text(0, tts))   
    if not custom_fields['age'] or custom_fields['age'] == '':
        _, total = roll_multi_dice(20,2)
        custom_fields['age'] = total + 10
    if not custom_fields['bonds_selected'] or custom_fields['bonds_selected'] == '':
        b = roll_list(load_bonds())
        custom_fields['bonds_selected'] = b['description']
        form.bonds.process_data(custom_fields['bonds_selected'])
        update_gold(custom_fields,'bonus_gold_bond',sdv(b,'gold',0))
        custom_fields['bond_items'] = json.dumps(sdv(b,'items',[]))        
    if not custom_fields['omens_selected'] or custom_fields['omens_selected'] == '':
        o = roll_list(load_omens())
        custom_fields['omens_selected'] = o
        form.omens.process_data(custom_fields['omens_selected'])
    if not custom_fields['gold'] or custom_fields['gold'] == '0':
        _, total = roll_multi_dice(6,3)
        custom_fields['gold'] = total
    if not custom_fields['portrait_src'] or custom_fields['portrait_src'] == '' or custom_fields['portrait_src'] == DEFAULT_PORTRAIT:
        image = roll_list(load_images())
        custom_fields['portrait_src'] = image
        custom_fields['custom_image'] = 'false'
    render = render_template('partial/charcreo/body.html', form=form, custom_fields=custom_fields, portrait_src=custom_fields['portrait_src'], custom_image=custom_fields['custom_image'])
    response = make_response(render)    
    return response
    

def check_char_sanity(form):
    errors = []
    if not form.background.data:
        errors.append('<li>Required background selection</li>')
    if form.name.data == None or form.name.data == '':
        errors.append('<li>Required character name</li>')
    if not form.strength_max.data:
        errors.append('<li>Required STR attribute</li>')
    if not form.dexterity_max.data:
        errors.append('<li>Required DEX attribute</li>')
    if not form.willpower_max.data:
        errors.append('<li>Required WIL attribute</li>')
    if not form.hp_max.data:
        errors.append('<li>Required HP attribute</li>')
    
    if len(errors) > 0:
        return False, errors
    return True,None
    

# Route: save character
@character_create.route('/charcreo/save', methods=['POST'])
def charcreo_save():
    form, custom_fields, background = process_form_data(request.form)
    form.custom_background.data = bleach.clean(form.custom_background.data)
    form.custom_name.data = bleach.clean(form.custom_name.data)

    # create url_name
    if form.name.data == 'Custom':
        url_name = create_unique_url_name(form.custom_name.data)
        form.name.data = form.custom_name.data
    else:
        url_name = create_unique_url_name(form.name.data)

    if form.background.data == 'Custom':
        form.background.data = form.custom_background.data
    
    sane, errors = check_char_sanity(form)
    if not sane:
        return render_template('partial/modal/save_char_error.html', error="<ul>"+"".join(errors)+"</ul>")    
    
    # add character to db

    custom_image = custom_fields['custom_image'] == 'true'
    containers = custom_fields['containers']
    
    description = ''
    if background:
        description=sdv(background,'background_description','')
                
    new_character = Character(
                name=form.name.data, owner_username=current_user.username, background=form.background.data, owner=current_user.id, url_name=url_name, custom_background=form.custom_background.data, custom_name=form.custom_name.data, items=form.items.data, 
                containers=containers, # form.containers.data,
                strength_max=form.strength_max.data, dexterity_max=form.dexterity_max.data, willpower_max=form.willpower_max.data, 
                hp_max=form.hp_max.data, strength=form.strength_max.data, dexterity=form.dexterity_max.data, armor=form.armor.data, scars="",
                willpower=form.willpower_max.data, hp=form.hp_max.data, deprived=False, 
                description=description, traits=form.traits.data, notes=form.notes.data, 
                gold=form.gold.data, bonds=form.bonds.data, omens=form.omens.data, custom_image=custom_image, image_url=custom_fields['portrait_src'])
    db.session.add(new_character)
    db.session.commit()
    response = make_response("Redirecting")
    response.headers["HX-Redirect"] = url_for('main.character', username=current_user.username, url_name=url_name)
    return response

# Route: save character error cancel
@character_create.route('/charcreo/save/error', methods=['GET'])
def charcreo_save_error_cancel():
    return ""
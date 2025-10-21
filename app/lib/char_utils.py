from app.models import db, User, Character, Party
from app.lib import load_backgrounds, load_traits, load_bonds, load_omens, roll_list, roll_dice, roll_multi_dice, roll_dict
import random
import json
import re
from flask import render_template
from flask_babel import _
NO_ARMOR = 'No upper body protection, no helmet nor shield'

# Retrieve character data
def get_character(character_id):
    character = Character.query.filter_by(id=character_id).first()
    return character


def item_text(item):
    name = _(item['name'])
    tags = []
    for t in item['tags']:
        if t == 'bonus defense':
            continue
        if t == 'uses':
            tags.append(str(item['uses'])+ ' ' + _('uses'))
            continue
        if t == "charges":
            c = item['charges']
            if "max_charges" in item:
                mc = item['max_charges'] 
            else:
                mc = c
            tags.append(str(c)+ '/'+ str(mc)+ ' ' + _('charges'))
            continue
        if t == '1 Armor' or t == '2 Armor' or t == '3 Armor':
            v = _(t)
            if 'bonus defense' in item['tags']:
                v = '+'+v
            if not v in tags:
                tags.append(v)
            continue
        tags.append(_(t))        
    result = name
    if len(tags) > 0:
        result = result + ' ('+', '.join(tags)+')'
    return result



class TraitValue:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        
        
# generate traits text, table contains: Physique, Skin, Hair, Face, Speech, Clothing, Virtue, Vice        
def traits_text(age, traits):
    txt = _('You have a')+' '+_(traits[0].value)+' '+_(traits[0].name)+', '+_(traits[1].value)+' '+_(traits[1].name)+', '+_('and')+' '+_(traits[2].value)+' '+_(traits[2].name)+'. '+_('Your')+' '+_(traits[3].name)+' '+_('is')+' '+_(traits[3].value)+', '+_('your')+' '+ _(traits[4].name)+' '+_(traits[4].value)+'. '+_('You have')+ ' '+_(traits[5].value)+' '+_(traits[5].name)+'. '+_('You are')+' '+    _(traits[6].value)+' ' +_('and')+' '+_(traits[7].value)+'. '
    if age != "" and int(age) > 0:
        txt += _('You are %(num)s years old.', num=age)
    return txt
    
        
class TableValue:
    def __init__(self, question, option):
        self.question = question
        self.option = option
        
class AttrsValue:
    def __init__(self):
        self.str = 10
        self.dex = 10
        self.wil = 10
        self.armor = 0
        self.hp = 1

class GeneratedCharacter:
    def __init__(self):
        self.name = ""
        self.background = None
        self.background_name = ""
        self.bond = None
        self.bond2 = None  # Second bond for Fieldwarden/Outrider
        self.omen = None
        self.items = []
        self.table1 = None
        self.table2 = None
        self.attributes = None
        self.traits = []
        self.gold = 0
        self.age = 10
        self.slots = 0
        self.description = ""
        self.containers = []
        
    def used_slots(self):
        slots = 0
        for it in self.items:
            if "bulky" in it["tags"]:
                slots += 2
                continue
            if "petty" in it["tags"]:
                continue
            slots += 1
        return slots

    def armor(self):
        armor = 0
        for it in self.items:
            if "1 Armor" in it["tags"]:
                armor += 1
                continue
            if "2 Armor" in it["tags"]:
                armor += 2
                continue
            if "3 Armor" in it["tags"]:
                armor += 3
                continue
        if armor > 3:
            armor = 3
        return armor
    
    def container_items(self):
        r = []
        for c in self.containers:
            r.append(c['name']+' ('+str(c['slots'])+')')
        return ", ".join(r)
    
    def toJSON(self):
        r = {}
        r['armor'] = self.attributes.armor
        if r['armor'] == NO_ARMOR:
            r['armor'] = 0
        r['background'] = _(self.background_name)
        r['bonds'] = _(self.bond['description'])
        if self.bond2:
            r['bonds'] += '\n\n' + _(self.bond2['description'])
        r['containers'] = self.containers
        r['deprived'] = False
        r['description'] = _(self.description)
        r['dexterity'] = self.attributes.dex
        r['dexterity_max'] = self.attributes.dex
        r['gold'] = self.gold
        r['hp'] = self.attributes.hp
        r['hp_max'] = self.attributes.hp
        tritems = []
        for it in self.items:
            tit = it
            tit['name'] = _(tit['name'])
            if 'description' in tit:
                tit['description'] = _(tit['description'])
            tritems.append(tit)
        r['items'] = tritems
        r['name'] = self.name
        r['notes'] = _(self.table1.question)+"\n"+_(self.table1.option['description'])+'\n'+_(self.table2.question)+'\n'+_(self.table2.option['description'])
        r['omens'] = _(self.omen)
        r['scars'] = ''
        r['strength'] = self.attributes.str
        r['strength_max'] = self.attributes.str
        r['traits'] = traits_text(self.age, self.traits)
        r['willpower'] = self.attributes.wil
        r['willpower_max'] = self.attributes.wil
        r['image_url'] = "default-portrait.webp"
        return r

def find_background(list, bkg):
    keys = {}
    for k in list:
        keys[k.casefold()] = k
    return keys[bkg.casefold()]


def generate_character(bkg):
    genchar = GeneratedCharacter()
    
    bkgs = load_backgrounds()
    keys = []
    for k in bkgs:
        keys.append(k)
    selected = keys[random.randint(0,len(keys)-1)]
    if bkg and bkg != "":
        bc = find_background(bkgs, bkg)
        if bc:
            selected = bc
    genchar.background = bkgs[selected]
    genchar.description = genchar.background['background_description']
    genchar.background_name = selected
    
    genchar.name = genchar.background['names'][random.randint(0,len(genchar.background['names'])-1)]
    
    omens = load_omens()
    genchar.omen = omens[random.randint(0, len(omens)-1)]
    
    items = genchar.background['starting_gear']
    t1q = genchar.background['table1']['question']
    t1o = genchar.background['table1']['options'][random.randint(0, len(genchar.background['table1']['options'])-1)]
    if "items" in t1o:
        for it in t1o['items']:
            items.append(it)
    genchar.table1 = TableValue(t1q, t1o)
            
    t2q = genchar.background['table2']['question']
    t2o = genchar.background['table2']['options'][random.randint(0, len(genchar.background['table2']['options'])-1)]
    if "items" in t2o:
        for it in t2o['items']:
            items.append(it)
    genchar.table2 = TableValue(t2q, t2o)
    
    bonds = load_bonds()
    genchar.bond = bonds[random.randint(0, len(bonds)-1)]
    
    bonds_required = get_required_bonds_count(selected, t1o.get('description', ''))
    genchar.bond2 = None
    
    if bonds_required == 2:
        genchar.bond2 = roll_bond_excluding([genchar.bond['description']])
            
    if 'items' in genchar.bond:
        for it in genchar.bond['items']:
            if not 'tags' in it:
                it['tags'] = []
            items.append(it)
    
    if genchar.bond2 and 'items' in genchar.bond2:
        for it in genchar.bond2['items']:
            if not 'tags' in it:
                it['tags'] = []
            items.append(it)
            
    filtered = []
    check = {}
    for it in items:
        if not it['name'] in check:
            check[it['name']] = True
            it['title'] = item_text(it)
            filtered.append(it)
    genchar.items = filtered
    
    genchar.attributes = AttrsValue()
    
    genchar.attributes.hp=random.randint(1,6)
    genchar.attributes.str=random.randint(3,18)
    genchar.attributes.dex=random.randint(3,18)
    genchar.attributes.wil=random.randint(3,18)
    genchar.attributes.armor = genchar.armor()
         
    traits = load_traits()
    for key in traits:
        val = traits[key][random.randint(0, len(traits[key])-1)]
        genchar.traits.append(TraitValue(key, val))
        
    genchar.age = random.randint(2, 40) + 10
    genchar.gold = random.randint(3,18)
    if 'gold' in genchar.bond and genchar.bond['gold'] != '':
         genchar.gold += int(genchar.bond['gold'])
    if genchar.bond2 and 'gold' in genchar.bond2 and genchar.bond2['gold'] != '':
         genchar.gold += int(genchar.bond2['gold'])
    
    genchar.slots = genchar.used_slots()
        
    # apply ids and location to items
    idx = 1
    for it in genchar.items:
        it['id'] = idx
        it['location'] = 0
        idx += 1
    
    genchar.containers.append({
            "id": 0,
            "name": "Main",
            "slots": 10
        })
    if "starting_containers" in genchar.background:
        idx = 1
        for c in genchar.background['starting_containers']:
            c['id'] = idx 
            idx += 1
            genchar.containers.append(c)
    if "containers" in t1o:
        for c in t1o['containers']:
            c['id'] = idx
            idx += 1
            genchar.containers.append(c)
    if "containers" in t2o:
        for c in t2o['containers']:
            c['id'] = idx
            idx += 1
            genchar.containers.append(c)            
            
    json_data = json.dumps(genchar.toJSON())
    
    return genchar, json_data



# used for character creation inventory
class DummyCharacter:
    def __init__(self):
        self.name = ""
        self.background = None
        self.background_name = ""
        self.bond = None
        self.omen = None
        self.items = '[]'
        self.table1 = None
        self.table2 = None
        self.attributes = None
        self.traits = ''
        self.gold = 0
        self.age = 10
        self.slots = 0
        self.description = ""
        self.containers = '[{"name": "Main", "slots": 10, "id": 0}]'
        
def find_background_table_option(background, tablename, option):
    if tablename in background and 'options' in background[tablename]:
        for it in background[tablename]['options']:
            if not 'description' in it:
                continue
            if it['description'] == option:
                return it
    return None

def find_bond_by_description(desc):
    bonds = load_bonds()
    for b in bonds:
        if b['description'] == desc:
            return b
    return None

def roll_bond_excluding(excluded_descriptions=None):
    """Roll a random bond, excluding any bonds with descriptions in the excluded list."""
    if excluded_descriptions is None:
        excluded_descriptions = []
    
    bonds = load_bonds()
    available_bonds = [b for b in bonds if b['description'] not in excluded_descriptions]
    
    if not available_bonds:
        available_bonds = bonds
    
    return roll_list(available_bonds)

def random_background():
    bkgs = load_backgrounds()
    key, background = roll_dict(bkgs)
    return key, background

def random_name(background):
    if background != None and 'names' in background:
        return roll_list(background['names'])
    names = []
    bkgs = load_backgrounds()
    for key in bkgs:
        names.extend(bkgs[key]['names'])
    return roll_list(names)

def random_table_option(background, name):
    if not background or not name in background:
        return None
    return roll_list(background[name]['options'])

# ["Physique", "Skin", "Hair", "Face", "Speech", "Clothing", "Virtue", "Vice"]
def random_trait(name):
    traits = load_traits()
    if not name in traits:
        return None
    return roll_list(traits[name])

def random_bond():
    b = roll_list(load_bonds())
    return b

def random_omen():
    b = roll_list(load_omens())
    return b


def get_required_bonds_count(background_name, table1_option_desc=None):
    """
    Determine how many bonds a background should have based on rules.
    
    Args:
        background_name: Name of the background (e.g., "Fieldwarden")
        table1_option_desc: Description of table1 option selected (for Outrider)
    
    Returns:
        int: Number of bonds this background should have (1 or 2)
    """
    backgrounds = load_backgrounds()
    
    if background_name not in backgrounds:
        return 1  # Default case
    
    background = backgrounds[background_name]
    
    # Check if background description mentions second bond
    if "Roll a second time on the Bonds table" in background.get('background_description', ''):
        return 2
    
    # Check table1 options for Outrider and similar backgrounds
    if table1_option_desc and "roll a second time on the Bonds table" in table1_option_desc:
        return 2
    
    return 1
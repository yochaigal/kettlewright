from app.models import db, User, Character, Party
from app.lib import load_backgrounds, load_traits, load_bonds, load_omens
import random
import json
import re
from flask import render_template

NO_ARMOR = 'No upper body protection, no helmet nor shield'

# Retrieve character data
def get_character(character_id):
    character = Character.query.filter_by(id=character_id).first()
    return character


def item_text(item):
    name = item['name']
    tags = []
    for t in item['tags']:
        if t == 'bonus defense':
            continue
        if t == 'uses':
            tags.append(str(item['uses'])+ ' uses')
            continue
        if t == "charges":
            c = item['charges']
            if "max_charges" in item:
                mc = item['max_charges'] 
            else:
                mc = c
            tags.append(str(c)+ '/'+ str(mc)+ ' charges')
            continue
        if t == '1 Armor' or t == '2 Armor' or t == '3 Armor':
            v = t
            if 'bonus defense' in item['tags']:
                v = '+'+v
            if not v in tags:
                tags.append(v)
            continue
        tags.append(t)        
    result = name
    if len(tags) > 0:
        result = result + ' ('+', '.join(tags)+')'
    return result



class TraitValue:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        
def traits_text(age, traits):
    return 'You are ' + str(age) + ' years old. You have a '+ traits[0].value + ' '+traits[0].name + ', '+ traits[1].value + ' ' + traits[1].name + ', and '+ traits[2].value + ' ' + traits[2].name+'. Your '+ traits[3].name +' is '+ traits[3].value + ', your ' + traits[4].name+' '+ traits[4].value+'. You have '+ traits[5].value+ ' ' + traits[5].name+'. You are ' + traits[6].value+' and '+ traits[7].value+'.'
        
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
        
    def other_items(self):
        result = []
        for it in self.items:
            if "1 Armor" in it["tags"] or  "2 Armor" in it["tags"] or "3 Armor" in it["tags"]:
                continue
            weapon = False
            for tag in it["tags"]:
                dice_match = re.findall(r'^d(\d+)(?:\s*\+\s*d(\d+))?$', tag)
                if len(dice_match) > 0:
                    weapon = True
                    break
            if weapon == True:
                continue
            result.append(item_text(it))
        return ", ".join(result)
    
    def armor_items(self):
        result = []
        for it in self.items:
            v = ''
            if "1 Armor" in it["tags"]:
                v = '1'
            elif "2 Armor" in it["tags"]:
                v = '2'
            elif "3 Armor" in it["tags"]:
                v = '3'            
            if "bonus defense" in it['tags'] and v != '':
                v = '+'+v
            if v != '':
                result.append(item_text(it))        
        return ", ".join(result)

    def weapon_items(self):
        result = []
        for it in self.items:
            dices = []
            for tag in it["tags"]:
                dice_match = re.findall(r'^d(\d+)(?:\s*\+\s*d(\d+))?$', tag)            
                for x in dice_match:
                    for y in x:
                        if y != "":
                            dices.append('d'+y)
            if len(dices) > 0:
                result.append(item_text(it))
        return ", ".join(result)
    
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
        r['background'] = self.background_name
        r['bonds'] = self.bond['description']
        r['containers'] = self.containers
        r['deprived'] = False
        r['description'] = self.description
        r['dexterity'] = self.attributes.dex
        r['dexterity_max'] = self.attributes.dex
        r['gold'] = self.gold
        r['hp'] = self.attributes.hp
        r['hp_max'] = self.attributes.hp
        r['items'] = self.items 
        r['name'] = self.name
        r['notes'] = self.table1.question+"\n"+self.table1.option['description']+'\n'+self.table2.question+'\n'+self.table2.option['description']
        r['omens'] = self.omen
        r['scars'] = ''
        r['strength'] = self.attributes.str
        r['strength_max'] = self.attributes.str
        r['traits'] = traits_text(self.age, self.traits)
        r['willpower'] = self.attributes.wil
        r['willpower_max'] = self.attributes.wil
        r['image_url'] = "default-portrait.webp"
        return r


def generate_character(external):
    genchar = GeneratedCharacter()
    
    bkgs = load_backgrounds()
    keys = []
    for k in bkgs:
        keys.append(k)
    selected = keys[random.randint(0,len(keys)-1)]
    genchar.background = bkgs[selected]
    genchar.description = genchar.background['background_description']
    genchar.background_name = selected
    
    genchar.name = genchar.background['names'][random.randint(0,len(genchar.background['names'])-1)]
    
    bonds = load_bonds()
    genchar.bond = bonds[random.randint(0, len(bonds)-1)]
    
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
            
    if 'items' in genchar.bond:
        for it in genchar.bond['items']:
            if not 'tags' in it:
                it['tags'] = []
            items.append(it)
            
    filtered = []
    check = {}
    for it in items:
        if not it['name'] in check:
            check[it['name']] = True
            filtered.append(it)
    genchar.items = filtered
    
    genchar.attributes = AttrsValue()
    
    genchar.attributes.hp=random.randint(1,6)
    genchar.attributes.str=random.randint(3,18)
    genchar.attributes.dex=random.randint(3,18)
    genchar.attributes.wil=random.randint(3,18)
    genchar.attributes.armor = genchar.armor()
    if genchar.attributes.armor == 0:
        genchar.attributes.armor = NO_ARMOR
         
    traits = load_traits()
    for key in traits:
        val = traits[key][random.randint(0, len(traits[key])-1)]
        genchar.traits.append(TraitValue(key, val))
        
    genchar.age = random.randint(2, 40) + 10
    genchar.gold = random.randint(3,18)
    if 'gold' in genchar.bond and genchar.bond['gold'] != '':
         genchar.gold += int(genchar.bond['gold'])
    
    genchar.slots = genchar.used_slots()
    
    genchar.armor_desc = genchar.armor_items()
    genchar.weapon_desc = genchar.weapon_items()
    genchar.items_desc = genchar.other_items()
    
    
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
            
    genchar.container_desc = genchar.container_items()

    json_data = json.dumps(genchar.toJSON())
    
    return render_template("partial/tools/pcgen_text.html",character=genchar, json_data=json_data, external=external)
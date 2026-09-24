import json
import re
import uuid
from app.lib.data import safeint
from app.models import db, Party, Character
from app.models.character import item_armor_value
from app.lib import sdv
from flask_babel import _
from flask import abort

FATIGUE_NAME = "Fatigue"
CARRYING_NAME = "Carrying"
non_editable_items = [FATIGUE_NAME]

def bring_fatigue_to_end(item):
    if item["name"] == FATIGUE_NAME:
        return "zzzzzzzzzzzzz"
    if item["name"].startswith(CARRYING_NAME):
        return "zzzzzzzzzz"
    else:
        return item["name"]
    

class Inventory:
    # character can be a player character or a party
    def __init__(self, character):
        self.character = character
        self.parse(character)
        self.select(0)
        self.itemsWithRolls = True        
        
    def setItemsWithRolls(self, value):
        self.itemsWithRolls = value
        
    def parse(self, character):
        containers = []
        if character.containers:
            containers = json.loads(character.containers)
        cdict = {}
        for c in containers:
            if not "items" in c:
                c["items"] = []
            cdict[c["id"]] = c
        items = json.loads(character.items)
        for i in items:
            if not "location" in i or not int(i["location"]) in cdict:
                continue
            c = cdict[int(i["location"])]
            if c == None:
                print("Unknown container for item",i)
                continue
            i["is_empty"] = False
            c["items"].append(i)
        containers.sort(key=lambda x: x["id"])
        for c in containers:
            if "items" in c:
                c["items"].sort(key=bring_fatigue_to_end)
        self.containers = containers
        
    def slot_layout(self):
        from app.lib.inventory_slots import arrange_slots
        return arrange_slots(self.selected_container['items'], self.selected_container['slots'])

    def pin_slots(self, container_id):
        """Keep legacy items in their displayed slots before changing the list."""
        if not isinstance(self.character, Character):
            return
        from app.lib.inventory_slots import arrange_slots
        container = self.get_container(container_id)
        if container is None:
            return
        positions = arrange_slots(container['items'], container['slots'])['positions']
        items = json.loads(self.character.items)
        for item in items:
            if item['location'] == int(container_id) and str(item['id']) in positions:
                item['slot'] = positions[str(item['id'])]
        self.character.items = json.dumps(items)

    def place_item(self, item_id, slot, commit=True):
        from app.lib.inventory_slots import arrange_slots, item_size
        item = self.get_item(item_id)
        if item is None:
            abort(404)
        container = self.get_container(item['location'])
        size = item_size(item)
        if not size or not 0 <= slot <= int(container['slots']) - size:
            abort(400, description='The item does not fit in these slots.')
        if size == 2:
            slot -= slot % 2
        current = arrange_slots(container['items'], container['slots'])
        items = json.loads(self.character.items)
        for entry in items:
            if entry['location'] == item['location'] and item_size(entry):
                entry['slot'] = current['positions'][str(entry['id'])]
                if str(entry['id']) == str(item_id):
                    entry['slot'] = slot
        arranged = arrange_slots([entry for entry in items if entry['location'] == item['location']],
                                 container['slots'], first_id=item_id)
        if current['used'] <= int(container['slots']) and any(row['overflow'] for row in arranged['rows']):
            abort(400, description='The item does not fit in these slots.')
        for entry in items:
            if entry['location'] == item['location'] and item_size(entry):
                entry['slot'] = arranged['positions'][str(entry['id'])]
        self.character.items = json.dumps(items)
        if commit:
            db.session.commit()
        self.parse(self.character)
        self.select(item['location'])

    # count slots for a container
    def container_slots(self, container):
        slots = 0
        for it in container["items"]:
            if not "tags" in it:
                continue
            if "bulky" in it["tags"]:
                slots += 2
                continue
            if "petty" in it["tags"]:
                continue
            slots += 1
        return slots
        
    # decorate items and containers for display        
    def decorate(self):
        for c in self.containers:
            curr_slots = self.container_slots(c)
            c["title"] = c["name"] + " ("+str(curr_slots)+"/"+str(c["slots"])+")"
            if curr_slots >= int(c["slots"]):
                c["encumbered"] = True
            else:
                c["encumbered"] = False
            for it in c["items"]:
                self.decorate_item(it)                
            while len(c["items"]) < int(c["slots"]): # fill empty slots
                c["items"].append({ "name":"", "is_empty":True, "editable": False })
            
        
    # decorate single item
    def decorate_item(self, item):
        title = _(item["name"])
        item["blocker"] = False
        item["editable"] = True
        item["removable"] = True
        
        if item["name"] in non_editable_items or "carrying" in item:
            item["editable"] = False                       
            
        if "description" in item and item["description"] == "-":
            item["description"] = ""
            
        if "carrying" in item:
            item["removable"] = False           
            
        if "carrying" in item or item["name"] == FATIGUE_NAME:
            item["blocker"] = True
            
        item["dice"] = []
        # tags
        if "tags" in item and len(item["tags"]) > 0:
            title += " ("
            tt = []
            bf = False
            if "bonus defense" in item["tags"]:
                bf = True
            for tag in item["tags"]:
                # extract dice info
                dice_match = re.findall(r'^d(\d+)(?:\s*\+\s*d(\d+))?$', tag)                
                dices = []
                if self.itemsWithRolls:
                    for x in dice_match:
                        for y in x:
                            if y != "":
                                item["dice"].append(int(y))
                # annotate tags                            
                if tag == "bulky" or tag == "petty":
                    tt.append("<i>"+_(tag)+"</i>")
                elif tag == "uses" and "uses" in item:
                    if item["uses"] == 1:
                        tt.append(_("1 use"))
                    else:
                        tt.append(str(item["uses"])+" "+_("uses"))
                elif tag == "charges" and "charges" in item and "max_charges" in item:
                    tt.append(str(item["charges"])+"/"+str(item["max_charges"])+" "+_("charges"))
                elif "1 Armor" in tag or "2 Armor" in tag or "3 Armor" in tag:
                    if bf:
                        tt.append("+"+_(tag))
                    else:
                        tt.append(_(tag))
                else:
                    if tag != "bonus defense":
                        tt.append(_(tag))
            title += ", ".join(tt)
            title += ") "                    
        if any(tag in ("1 Armor", "2 Armor", "3 Armor") for tag in item.get("tags", [])):
            if not item.get("armor_active", item.get("name") != "Sloth-Tarp"):
                title += " — " + _("Armor inactive")
        item["title"] = title
        return item
            
    # select active container
    def select(self, id):
        for c in self.containers:
            if int(id) == c["id"]:
                c["is_selected"] = True
                self.selected_container = c
            else:
                c["is_selected"] = False
                
    # delete item
    def delete_item(self,container_id,item_id):
        idx = 0
        items = json.loads(self.character.items)        
        deleted = None
        for it in items:
            if it["id"] == str(item_id) and it["location"] == int(container_id):
                deleted = items.pop(idx)
                break
            idx += 1
        self.character.items = json.dumps(items)
        if deleted != None and "carrying" in deleted and "location" in deleted:
            containers = self.remove_carried_by(deleted["location"])
            self.character.containers = json.dumps(containers)
        db.session.commit()
        self.parse(self.character)
        
    # get container
    def get_container(self, container_id):
        conts = self.containers
        cnt = None
        for c in conts:
            if c["id"] == int(container_id):
                cnt = c
                break
        return cnt
    
    def get_containers_wo_items(self):
        conts = self.containers
        result = []
        for c in conts:
            result.append({"id": c['id'], "name": c['name'], "slots": c['slots']})
        return result
        
    # get items for container:
    def get_items_for_container(self, container_id, decorated):
        result = []
        cnt = self.get_container(container_id)
        if cnt == None:
            return result
        items = json.loads(self.character.items)
        for it in items:
            if it["location"] == int(container_id):
                if decorated:
                    result.append(self.decorate_item(it))
                else:
                    result.append(it)
        return result
    
    # generate new item id
    def generate_item_id(self):
        return uuid.uuid4().hex
        # items = json.loads(self.character.items)
        # max = 0
        # for it in items:
        #     if max <= it["id"]:
        #         max = it["id"]
        # max += 1
        # return max
    
    # generate new container id
    def generate_container_id(self):
        cnts = json.loads(self.character.containers)
        max = 0
        for it in cnts:
            if max <= it["id"]:
                max = it["id"]
        max += 1
        return max
        
    # add fatigue
    def add_fatigue(self, container_id):
        idx = 0        
        cont_items = self.get_items_for_container(container_id, False)
        cnt = self.get_container(container_id)
        if cnt == None:
            return
        if self.container_slots(cnt) >= cnt["slots"]:
            return
        items = json.loads(self.character.items)                
        new_id = self.generate_item_id()
        items.append({"id": new_id, "name": FATIGUE_NAME, "editable": False, "location": int(container_id),"tags":[]})
        self.character.items = json.dumps(items)
        db.session.commit()
        self.parse(self.character)
        
    # get containers other than selected
    def get_other_containers(self, container_id):
        result = []
        for c in self.containers:
            if c["id"] != int(container_id):
                result.append(c)
        return result
    
    # remove carrying tag from items
    def remove_carrying(self, container_id):
        result = []
        items = json.loads(self.character.items)
        for it in items:
            if not "carrying" in it or int(it["carrying"]) != int(container_id):
                result.append(it)            
        return result
    
    # add carrying tag
    def add_carrying(self, carried_by, container_id, name, amount):
        items = json.loads(self.character.items)  
        new_id = self.generate_item_id()
        for i in range(amount):
            new_item = {"id": new_id+"_"+str(i), "name": "Carrying "+name, "editable": False, "location": int(carried_by),"tags":[], "carrying":int(container_id)}
            items.append(new_item)
        return items
    
    # remove carried by
    def remove_carried_by(self, carried_by):
        containers = json.loads(self.character.containers)
        for c in containers:
            if "carried_by" in c and int(c["carried_by"]) == int(carried_by):
                del c["carried_by"]
                if "load" in c:
                    del c["load"]
        return containers
        
    
    # update container data
    def update_container(self, container_id, name, slots, carried_by, load):
        cnt = self.get_container(container_id)
        cnt["name"] = name
        cnt["slots"] = int(slots)
        cnt['items'] = [] # clean items, because they will be parsed later
        
        has_carried = carried_by != None and carried_by != "" and load != "" and load != None and int(load) != 0
        if has_carried:
            cnt["carried_by"] = carried_by
            cnt["load"] = load
        else:
            if "carried_by" in cnt:
                del cnt["carried_by"]
            # if "load" in cnt:
            #     del cnt["load"]
            
        containers = json.loads(self.character.containers)
        result = []
        for c in containers:
            if c["id"] != int(container_id):
                result.append(c)
        result.append(cnt)
        
        if has_carried:
            items = self.add_carrying(carried_by,container_id, name, int(load))
            self.character.items = json.dumps(items)
        else:
            items =  self.remove_carrying(container_id)
            self.character.items = json.dumps(items)
            
        self.character.containers = json.dumps(result)
        db.session.commit()
        self.parse(self.character)
        
    # move items to other container
    def move_items(self, from_container, to_container):
        items = json.loads(self.character.items)
        for it in items:
            if int(it["location"]) == int(from_container):
                it["location"] = int(to_container)
        self.character.items = json.dumps(items)
        db.session.commit()
        self.parse(self.character)
        
    # remove items from container
    def remove_items(self, container_id):
        items = json.loads(self.character.items)
        result = []
        for it in items:
            if it["location"] != int(container_id):
                result.append(it)
        self.character.items = json.dumps(result)
        db.session.commit()
        self.parse(self.character)
        
    # delete container
    def delete_container(self, container_id, move_to):
        result = []
        containers = json.loads(self.character.containers)
        for c in containers:
            if c["id"] != int(container_id):
                result.append(c)
        self.character.containers = json.dumps(result)
        items = json.loads(self.character.items)
        result = []
        for it in items:
            if "carrying" in it and it["carrying"] == int(container_id):
                continue
            result.append(it)
        self.character.items = json.dumps(result)
        db.session.commit()
        self.parse(self.character)                        
        if move_to != None and move_to != "":
            self.move_items(container_id, move_to)
        else:
            self.remove_items(container_id)

    
    # add container
    def add_container(self, name, slots, carried_by, load):
        new_id = self.generate_container_id()
        containers = json.loads(self.character.containers)
        obj = {"name": name, "slots": int(slots), "id": new_id}
        has_carried = carried_by != None and carried_by != "" and load != "" and load != None and int(load) != 0
        if has_carried:
            obj["carried_by"] = carried_by
            obj["load"] = load
            for i in range(int(load)):
                items = self.add_carrying(carried_by,new_id, name, int(load))
            self.character.items = json.dumps(items)
        containers.append(obj)
        self.character.containers = json.dumps(containers)                        
        db.session.commit()
        self.parse(self.character)
        return new_id
    
    # get item by id
    def get_item(self, item_id):
        items = json.loads(self.character.items)
        for it in items:
            if it["id"] == str(item_id):
                return it
        return None
    
    # create item
    def create_item(self, name, tags, uses, charges, max_charges, container, description, armor_active=None, commit=True):
        cnt = self.get_container(container)
        if cnt == None:
            return None
        from app.lib.inventory_slots import item_size
        size = item_size({'tags': tags.split(',') if tags else []})
        if size and self.container_slots(cnt) + size > int(cnt['slots']):
            return None
        self.pin_slots(container)
        new_id = self.generate_item_id()
        items = json.loads(self.character.items)
        items.append({"id":new_id,"name":"","tags":[],"location":0,"description":""})
        self.character.items = json.dumps(items)
        return self.update_item(new_id,name, tags, uses, charges, max_charges, container, description, armor_active=armor_active, commit=commit)
        
    
    # update item
    def update_item(self, item_id, name, tags, uses, charges, max_charges, container, description, armor_active=None, commit=True):
        item = self.get_item(item_id)
        if item == None:
            return
        self.pin_slots(item['location'])
        if item['location'] != int(container):
            self.pin_slots(container)
        item = self.get_item(item_id)
        item["name"] = name
        if tags != "":
            item["tags"] = tags.split(",")
        else:
            item["tags"] = []
        if not any(tag in item["tags"] for tag in ("1 Armor", "2 Armor", "3 Armor")):
            item["armor_active"] = False
        elif armor_active is not None:
            item["armor_active"] = armor_active
        if "uses" in item["tags"]:
            item['max_uses'] = max(item.get('max_uses', item.get('uses', 0)), int(uses))
            item["uses"] = int(uses)
        else:
            if "uses" in item:
                del item["uses"]
            item.pop('max_uses', None)
        if "charges" in item["tags"]:
            item["charges"] = safeint(charges)
            item["max_charges"] = safeint(max_charges)
        else:
            if "charges" in item:
                del item["charges"]
            if "max_charges" in item:
                del item["max_charges"]
        item["location"] = int(container)
        item["description"] = description
        items = json.loads(self.character.items)
        result = []
        for it in items:
            if it["id"] != str(item_id):
                result.append(it)
        result.append(item)
        self.character.items = json.dumps(result)
        if commit:
            db.session.commit()
        self.parse(self.character)
        return item
    
    # change item amount
    def change_amount(self, item_id, action, prop):
        item = self.get_item(item_id)
        if item == None:
            return None
        if not prop in item:
            print("cannot find",prop,"in item",item["name"])
            return
        val = item[prop]
        if action == "plus":
            val += 1
        elif action == "minus":
            val -= 1
        if val < 0:
            val = 0
        if prop == "charges" and val > item["max_charges"]:
            val = item["max_charges"]            
        if prop == 'uses':
            item['max_uses'] = max(item.get('max_uses', item[prop]), item[prop], val)
        item[prop] = val
        items = json.loads(self.character.items)
        result = []
        for it in items:
            if it["id"] != str(item_id):
                result.append(it)
        result.append(item)
        self.character.items = json.dumps(result)
        db.session.commit()
        self.parse(self.character)
        return item
    
    def transfer_item(self, item_id, recipient, container_id=0):
        """Validate both inventories before moving an item in one transaction."""
        item = self.get_item(item_id)
        if item is None:
            abort(404)
        if "carrying" in item:
            abort(400, description="Carrying markers cannot be transferred.")
        target = Inventory(recipient)
        container = target.get_container(container_id)
        if container is None:
            abort(400, description="Destination container does not exist.")
        tags = item.get("tags") or []
        slots = 0 if "petty" in tags else 2 if "bulky" in tags else 1
        if target.container_slots(container) + slots > int(container['slots']):
            abort(400, description="Destination container has insufficient free slots.")
        source_items = json.loads(self.character.items)
        target_items = json.loads(recipient.items or '[]')
        if any(str(existing['id']) == str(item_id) for existing in target_items):
            abort(409, description="Item already exists in the destination.")
        item['location'] = int(container_id)
        self.character.items = json.dumps([it for it in source_items if str(it['id']) != str(item_id)])
        recipient.items = json.dumps(target_items + [item])
        db.session.commit()
        self.parse(self.character)
        return item

    # move item to selected party container
    def move_item_to_party(self, item_id, container_id=0):
        party = db.session.get(Party, self.character.party_id) if self.character.party_id else None
        if not party or self.character.id not in json.loads(party.members or '[]'):
            abort(400, description="Character does not belong to this party.")
        return self.transfer_item(item_id, party, container_id)

    # remove items from party storage
    def remove_items_from_party(self, char_items):
        party = Party.query.filter_by(id=self.character.party_id).first()
        if not party:
            return
        keys = []
        for it in char_items:
            key = str(it["id"])+"~"+it["name"]
            keys.append(key)
        items = json.loads(party.items)
        result = []
        for it in items:
            k = str(it["id"])+"~"+it["name"]
            if not k in keys: 
                result.append(it)
        party.items = json.dumps(result)
        db.session.commit()
        
    # move item from party storage to a current member's main inventory
    def move_item_to_user(self, item_id, user_id):
        character = db.session.get(Character, user_id)
        if (not character or character.party_id != self.character.id
                or character.id not in json.loads(self.character.members or '[]')):
            abort(400, description="Destination character does not belong to this party.")
        return self.transfer_item(item_id, character, 0)

    # remove items from characters
    def remove_items_from_characters(self, char_items):
        party = Party.query.filter_by(id=self.character.id).first()
        if not party:
            return
        keys = []
        for it in char_items:
            key = str(it["id"])+"~"+it["name"]
            keys.append(key)
        members_list = json.loads(
            party.members) if party.members and party.members.strip() else []
        for member_id in members_list:
            character = Character.query.filter_by(id=member_id).first()
            if character:
                items = json.loads(character.items)
                result = []
                for it in items:
                    k = str(it["id"])+"~"+it["name"]
                    if not k in keys: 
                        result.append(it)
                character.items = json.dumps(result)
                db.session.commit()        
                
    def compute_armor(self):
        return min(3, sum(item_armor_value(item) for item in self.get_items_for_container(0, False)))

    def print(self):
        print(self.containers)

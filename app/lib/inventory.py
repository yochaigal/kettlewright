import json
import re
from app.models import db, Party

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
    def __init__(self, character):
        self.character = character
        self.parse(character)
        self.select(0)
        
    def parse(self, character):
        containers = json.loads(character.containers)
        cdict = {}
        for c in containers:
            if not "items" in c:
                c["items"] = []
            cdict[c["id"]] = c
        items = json.loads(character.items)
        for i in items:
            if not int(i["location"]) in cdict:
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
        
    # count slots for a container
    def container_slots(self, container):
        slots = 0
        for it in container["items"]:
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
        title = item["name"]
        item["blocker"] = False
        item["editable"] = True
        item["removable"] = True
        
        if item["name"] in non_editable_items or "carrying" in item:
            item["editable"] = False                       
            
        if "carrying" in item:
            item["removable"] = False           
            
        if "carrying" in item or item["name"] == FATIGUE_NAME:
            item["blocker"] = True
            
        item["dice"] = []
        # tags
        if len(item["tags"]) > 0:
            title += " ("
            tt = []
            bf = False
            if "bonus defense" in item["tags"]:
                bf = True
            for tag in item["tags"]:
                # extract dice info
                dice_match = re.findall(r'^d(\d+)(?:\s*\+\s*d(\d+))?$', tag)                
                dices = []
                for x in dice_match:
                    for y in x:
                        if y != "":
                            item["dice"].append(int(y))
                # annotate tags                            
                if tag == "bulky" or tag == "petty":
                    tt.append("<i>"+tag+"</i>")
                elif tag == "uses":
                    if item["uses"] == 1:
                        tt.append("1 use")
                    else:
                        tt.append(str(item["uses"])+" uses")
                elif tag == "charges":
                    tt.append(str(item["charges"])+"/"+str(item["max_charges"])+" charges")
                elif "1 Armor" in tag or "2 Armor" in tag or "3 Armor" in tag:
                    if bf:
                        tt.append("+"+tag)
                    else:
                        tt.append(tag)
                else:
                    if tag != "bonus defense":
                        tt.append(tag)
            title += ", ".join(tt)
            title += ") "                    
        item["title"] = title
            
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
            if it["id"] == int(item_id) and it["location"] == int(container_id):
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
        
    # get items for container:
    def get_items_for_container(self, container_id):
        result = []
        cnt = self.get_container(container_id)
        if cnt == None:
            return result
        items = json.loads(self.character.items)
        for it in items:
            if it["location"] == int(container_id):
                result.append(it)
        return result
    
    # generate new item id
    def generate_item_id(self):
        items = json.loads(self.character.items)
        max = 0
        for it in items:
            if max <= it["id"]:
                max = it["id"]
        max += 1
        return max
    
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
        cont_items = self.get_items_for_container(container_id)
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
            new_item = {"id": new_id+i, "name": "Carrying "+name, "editable": False, "location": int(carried_by),"tags":[], "carrying":int(container_id)}
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
        self.character.items = json.dumps(items)
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
            if it["id"] == int(item_id):
                return it
        return None
    
    # create item
    def create_item(self, name, tags, uses, charges, max_charges, container, description):
        cnt = self.get_container(container)
        if cnt == None:
            return
        if self.container_slots(cnt) >= cnt["slots"]:
            return
        new_id = self.generate_item_id()
        items = json.loads(self.character.items)
        items.append({"id":new_id,"name":"",tags:[],"location":0,"description":""})
        self.character.items = json.dumps(items)
        return self.update_item(new_id,name, tags, uses, charges, max_charges, container, description)
        
    
    # update item
    def update_item(self, item_id, name, tags, uses, charges, max_charges, container, description):
        item = self.get_item(item_id)
        if item == None:
            return
        item["name"] = name
        if tags != "":
            item["tags"] = tags.split(",")
        else:
            item["tags"] = []
        if "uses" in item["tags"]:
            item["uses"] = int(uses)
        else:
            if "uses" in item:
                del item["uses"]
        if "charges" in item["tags"]:
            item["charges"] = int(charges)
            item["max_charges"] = int(max_charges)
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
            if it["id"] != int(item_id):
                result.append(it)
        result.append(item)
        self.character.items = json.dumps(result)
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
        item[prop] = val
        items = json.loads(self.character.items)
        result = []
        for it in items:
            if it["id"] != int(item_id):
                result.append(it)
        result.append(item)
        self.character.items = json.dumps(result)
        db.session.commit()
        self.parse(self.character)
        return item
    
    # move item to party storage
    def move_item_to_party(self, item_id):
        item = self.get_item(item_id)
        if item == None:
            return
        party = Party.query.filter_by(id=self.character.party_id).first()
        if not party:
            return
        self.delete_item(item["location"], item_id)
        items = json.loads(party.items)
        items.append(item)
        party.items = json.dumps(items)
        db.session.commit()
        return item        
    
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
                    
    def print(self):
        print(self.containers)
                
            
    
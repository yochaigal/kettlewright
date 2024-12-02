import json
import re
from app.models import db

def bring_fatigue_to_end(item):
    if item["name"] == "Fatigue":
        return "zzzzzzzzzzzzz"
    else:
        return item["name"]
    
FATIGUE_NAME = "Fatigue"
non_editable_items = [FATIGUE_NAME]

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
        
    # decorate items and containers for display        
    def decorate(self):
        for c in self.containers:
            c["title"] = c["name"] + " ("+str(len(c["items"]))+"/"+str(c["slots"])+")"
            if len(c["items"]) >= int(c["slots"]):
                c["encumbered"] = True
            else:
                c["encumbered"] = False
            for it in c["items"]:
                self.decorate_item(it, c)
            while len(c["items"]) < int(c["slots"]): # fill empty slots
                c["items"].append({ "name":"", "is_empty":True, "editable": False })
    
    # decorate single item
    def decorate_item(self, item, container):
        title = item["name"]
        if item["name"] in non_editable_items or "carrying" in item:
            item["editable"] = False
        else:
            item["editable"] = True
        if len(item["tags"]) > 0:
            title += " ("
            tt = []
            bf = False
            if "bonus defense" in item["tags"]:
                bf = True
            for tag in item["tags"]:
                # extract dice info
                dice_match = re.findall("^d(\d+)(?:\s*\+\s*d(\d+))?$", tag)                
                dices = []
                for x in dice_match:
                    for y in x:
                        if y != "":
                            dices.append(int(y))
                item["dice"] = dices 
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
            title += ",".join(tt)
            title += ") "
                    
        item["title"] = title
            
    # select active container
    def select(self, id):
        for c in self.containers:
            if id == c["id"]:
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
        conts = json.loads(self.character.containers)
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
        if len(cont_items) >= cnt["slots"]:
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
    def add_carrying(self, carried_by, container_id, name):
        items = json.loads(self.character.items)  
        found = False
        for it in items:
            if "carrying" in it and int(it["carrying"]) == int(container_id):
                found = True
        if found:
            return items
        new_id = self.generate_item_id()
        items.append({"id": new_id, "name": "Carrying "+name, "editable": False, "location": int(carried_by),"tags":[], "carrying":int(container_id)})
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
            if "load" in cnt:
                del cnt["load"]
            
        containers = json.loads(self.character.containers)
        result = []
        for c in containers:
            if c["id"] != int(container_id):
                result.append(c)
        result.append(cnt)
        if has_carried:
            items = self.add_carrying(carried_by,container_id, name)
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
            items = self.add_carrying(carried_by,new_id, name)
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
            
    def print(self):
        print(self.containers)
                
            
    
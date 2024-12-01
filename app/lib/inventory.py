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
        self.containers = json.loads(character.containers)
        for c in self.containers:
            if not "items" in c:
                c["items"] = []
        items = json.loads(character.items)
        for i in items:
            c = self.containers[int(i["location"])]
            if c == None:
                print("Unknown container for item",i)
            i["is_empty"] = False
            c["items"].append(i)
        self.containers.sort(key=lambda x: x["id"])
        for c in self.containers:
            if "items" in c:
                c["items"].sort(key=bring_fatigue_to_end)
        
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
        if item["name"] in non_editable_items:
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
        for it in items:
            if it["id"] == int(item_id) and it["location"] == int(container_id):
                items.pop(idx)
                break
            idx += 1
        self.character.items = json.dumps(items)
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
        items.append({"name": FATIGUE_NAME, "editable": False, "location": int(container_id),"tags":[]})
        self.character.items = json.dumps(items)
        db.session.commit()
        self.parse(self.character)
            
    def print(self):
        print(self.containers)
                
            
    
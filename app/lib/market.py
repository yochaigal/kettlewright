import json
from app.models import db, Character
from app.lib import load_market

class Market:
    def __init__(self):
        self.market = load_market()
        self.filter = ""
        self.categories = [] #empty means all
        
    def set_categories(self, cats):
        self.categories = cats
        
    def set_filter(self, filter):
        self.filter = filter          
        
    def get_market_items(self):
        items = []
        for it in self.market:
            if len(self.categories) > 0 and not it["category"] in self.categories:
                continue
            if self.filter != "" and it["name"].find(self.filter) == -1:
                continue
            items.append(it)
        return items
    
    def find_item_by_name(self, name):
        for it in self.market:
            if it["name"] == name:
                return it
        return None
    
    def buy(self, items):
        result = []
        for name in items:
            it = self.find_item_by_name(name)
            if it == None:
                continue
            item = {"name":name, "tags":[], "uses":0, "max_uses":0, "charges":0, "max_charges":0, "description":""}
            if "tags" in it:
                item["tags"] = it["tags"]
            if "uses" in it["tags"]:
                item["uses"] = it["uses"]
            if "charges" in it["tags"]:
                item["charges"] = it["charges"]
                item["max_charges"] = it["charges"]
            if "description" in it:
                item["description"] = it["description"]
            result.append(item)
        return result
    
    
        
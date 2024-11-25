import os
import app 
import json
from .paths import app_static_path

def load_scars():
    result = {}
    scars_file_path = os.path.join(app_static_path(), 'json', 'scars.json')
    with open(scars_file_path, 'r') as file:
        scars_data = json.load(file)
    for s in scars_data["Scars"]:
        desc = s['description']
        name = s["name"]
        result[name] = desc
    return result
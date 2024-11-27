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

def load_images():
    image_folder = os.path.join(app_static_path(), 'images', 'portraits')
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.webp')]
    return image_files

def load_omens():
    result = []
    omens_file_path = os.path.join(app_static_path(), 'json', 'omens.json')
    with open(omens_file_path, 'r') as file:
        omens_data = json.load(file)
    for s in omens_data["Omens"]:
        desc = s['description']
        result.append(desc)
    return result

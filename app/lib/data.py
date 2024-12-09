import os
import app 
import json
from .paths import app_static_path
from app.models import db, User, Party, Character

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


def load_market():
    result = []
    market_file_path = os.path.join(app_static_path(), 'json', 'marketplace.json')
    with open(market_file_path, 'r') as file:
        market_data = json.load(file)
    result = []
    for cat in market_data:
        for name in market_data[cat]:
            item = market_data[cat][name]
            item["category"] = cat
            item["name"] = name
            result.append(item)
    return result

# Retrieve character data
def get_char_data(username, url_name):
    user = User.query.filter_by(username=username).first_or_404()
    character = Character.query.filter_by(
        owner=user.id, url_name=url_name).first_or_404()
    return user, character


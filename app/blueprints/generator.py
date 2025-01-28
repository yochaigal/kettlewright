# Multipurpose generator blueprint

from flask import Blueprint, render_template, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import *
from unidecode import unidecode
from flask_babel import lazy_gettext as _l, _


generator = Blueprint('generator', __name__)

def parse_character(data):
    c = Character()
    c.armor = str(data['armor'])
    c.background = data['background']
    c.bonds = data['bonds']
    c.containers = json.dumps(data['containers'])
    c.custom_image = False
    c.custom_name = ''
    c.deprived = False
    c.description = data['description']
    c.dexterity = data['dexterity']
    c.dexterity_max = data['dexterity_max']
    c.gold = data['gold']
    c.hp = data['hp']
    c.hp_max = data['hp_max']
    c.image_url = ''
    c.items = json.dumps(data['items'])
    c.name = data['name']
    c.notes = data['notes']
    c.omens = data['omens']
    c.scars = ''
    c.strength = data['strength']
    c.strength_max = data['strength_max']
    c.traits = data['traits']
    c.willpower = data['willpower']
    c.willpower_max = data['willpower_max']
    return c
    


# Route: generate random character
@generator.route('/gen/character', methods=['GET'])
def character():
    background = request.args.get('background')
    genchar, json_data  = generate_character(background)
    darkmode = False
    dmode = request.args.get('darkmode')
    if dmode != None and dmode.upper() == 'TRUE':
        darkmode = True
    
    out = request.args.get('output')
    if out and out == 'json':
        response = make_response(json_data)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    render =  render_template("partial/tools/pcgen_text.html",character=genchar, json_data=json_data, darkmode=darkmode)
    response = make_response(render)
    response.headers["HX-Trigger-After-Settle"] = "show-print"
    return response

# Route: clear pc generator value
@generator.route('/gen/character/clear', methods=['GET'])
def character_clear():
    return render_template('partial/tools/pcgen.html',pcgen_value="")

# Route: print generated character
@generator.route('/gen/character/print', methods=['POST'])
def character_print():
    data = request.form
    if not data or not "json_data" in data or data['json_data'] == None or data['json_data'] == '':
        print('No character data', data)
        return make_response('')
    character = parse_character(json.loads(data['json_data']))
    inventory = Inventory(character)
    
    render = render_template('main/character_print.html', character=character, items_json=json.dumps(character.items), 
                           containers_json=json.dumps(character.containers), party=None, inventory=inventory, from_generator=True)
    response = make_response(render)
    response.headers["HX-Trigger-After-Settle"] = "do-print"
    return response
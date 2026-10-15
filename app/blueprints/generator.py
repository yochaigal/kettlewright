# Multipurpose generator blueprint

from flask import Blueprint, render_template, url_for, request, flash, session, make_response, Response, abort, redirect
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
    from app.lib.data import load_images
    portrait = data.get('image_url', '')
    c.image_url = portrait if portrait in load_images(include_categories=True) else ''
    c.items = json.dumps(data['items'])
    c.name = data['name']
    c.notes = data['notes']
    from app.models.character import BACKGROUND_FIELDS
    for field in BACKGROUND_FIELDS:
        setattr(c, field, data.get(field, ''))
    c.omens = data['omens']
    c.scars = ''
    c.strength = data['strength']
    c.strength_max = data['strength_max']
    c.traits = data['traits']
    c.willpower = data['willpower']
    c.willpower_max = data['willpower_max']
    from app.lib.companions import import_pet
    c.pets.extend(import_pet(pet) for pet in data.get('pets', []))
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
    
    if request.args.get('view') == 'sheet':
        from random import choice
        from app.lib.data import load_images
        from app.lib.generated_character import sign_snapshot
        snapshot = json.loads(json_data)
        snapshot['image_url'] = choice([name for name in load_images(include_categories=True) if name.startswith('humanoid/')])
        json_data = json.dumps(snapshot)
        preview = parse_character(snapshot)
        inventories = []
        for container in json.loads(preview.containers):
            inventory = Inventory(preview)
            inventory.select(container['id'])
            inventory.decorate()
            inventories.append((container['id'], inventory))
        render = render_template('partial/tools/pcgen_sheet.html', character=preview,
            json_data=json_data, inventory=inventories[0][1], preview_inventories=inventories,
            generated_preview=True, generated_snapshot=sign_snapshot(snapshot), generated_character=genchar, is_owner=False, username='', url_name='', party=None,
            portrait_src=url_for('static', filename='images/portraits/' + preview.image_url))
    else:
        render = render_template("partial/tools/pcgen_text.html",character=genchar, json_data=json_data, darkmode=darkmode)
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

@generator.post('/gen/character/save/<kind>')
@login_required
def save_character(kind):
    from flask_wtf import FlaskForm
    from itsdangerous import BadSignature
    from app.models import Campaign, ContentEntry
    from app.lib.generated_character import read_snapshot, as_party_monster, character_markdown
    from app.lib.feature_access import user_features_enabled
    request.max_content_length = 256 * 1024
    if kind not in ('monster', 'npc'):
        abort(404)
    if kind == 'npc' and not user_features_enabled():
        abort(404)
    if not FlaskForm().validate_on_submit():
        abort(400, 'Invalid CSRF token.')
    try:
        snapshot = read_snapshot(request.form.get('snapshot', ''))
        target_id = int(request.form.get('target_id', ''))
    except (BadSignature, ValueError, KeyError, TypeError):
        abort(400, 'Invalid or expired character preview. Generate a new character.')
    if kind == 'monster':
        target = db.get_or_404(Party, target_id)
        if target.owner != current_user.id:
            abort(403)
        try:
            result = as_party_monster(target, snapshot)
        except ValueError as error:
            db.session.rollback()
            abort(400, str(error))
        db.session.add(result)
        db.session.commit()
        return redirect(url_for('companions.sheet', companion_id=result.id))
    target = db.get_or_404(Campaign, target_id)
    if target.owner_id != current_user.id:
        abort(403)
    from app.lib.campaigns import content_value
    portrait = url_for('static', filename='images/portraits/' + snapshot['image_url'], _external=True)
    body = f"![{_('Portrait')}]({portrait})\n\n" + character_markdown(snapshot)
    result = ContentEntry(owner_id=current_user.id, campaign=target, category='npc',
                          title=snapshot['name'], body=content_value(body))
    db.session.add(result)
    db.session.commit()
    return redirect(url_for('campaigns.edit_entry', entry_id=result.id))

# Character creation blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import *
from unidecode import unidecode
from flask_babel import _
import urllib.parse

character_create = Blueprint('character_create', __name__)

# Route: edit new character portrait
@character_create.route('/charcreo/portrait', methods=['GET'])
def charedit_inplace_portrait():
    portrait_src = request.args.get('src')
    images = load_images()
    custom_image = request.args.get("custom_image")
    portrait_src = urllib.parse.quote_plus(portrait_src)
    return render_template('partial/charcreo/portrait.html', images=images, portrait_src=portrait_src, custom_image=custom_image)

# Route: edit new character portrait - cancel
@character_create.route('/charcreo/portrait/cancel', methods=['GET'])
def charcreo_portrait_cancel():
    portrait_src = ""
    ps = request.args.get("src")
    if ps != None and ps != "":
        portrait_src = ps
    portrait_src = urllib.parse.quote_plus(portrait_src)
    custom_image = request.args.get("custom_image")
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image)          

# Route: edit new character portrait - save
@character_create.route('/charcreo/portrait/save', methods=['POST'])
def charcreo_portrait_save():
    data = request.form
    custom_url = data['custom-url']
    selected_portrait = data['selected-portrait']
    portrait_src = "/static/images/portraits/default-portrait.webp"
    if custom_url != None and custom_url != "":
        if not is_url_image(custom_url):
            print("Bad image url!!!", custom_url)
        else:
            portrait_src = custom_url
            custom_image = True
    elif selected_portrait != "" and selected_portrait != None:
            portrait_src = "/static/images/portraits/"+selected_portrait
            custom_image = False
    portrait_src = urllib.parse.quote_plus(portrait_src)
    return render_template('partial/charcreo/portrait_img.html', portrait_src = portrait_src, custom_image=custom_image)        


# Route - select background
@character_create.route('/charcreo/select-background', methods=['POST'])
def charcreo_select_background():
    data = request.form
    form = CharacterForm()
    bkgs = load_backgrounds()
    if data['background'] != 'Custom':
        background = bkgs[data['background']]
        form.custom_background.process_data("")
    else:
        background=None
    return render_template('partial/charcreo/background.html', form=form, background=background)
    
# Route - roll background
@character_create.route('/charcreo/roll-background', methods=['POST'])
def charcreo_roll_background():
    form = CharacterForm()
    bkgs = load_backgrounds()
    name, background = roll_dict(bkgs)
    form.background.process_data(name)
    form.custom_background.process_data("")
    return render_template('partial/charcreo/background.html', form=form, background=background)
    
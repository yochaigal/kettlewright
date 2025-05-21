from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.lib import *
from app.models import db, User, Character, Party
from app.forms import *
import json
from flask_babel import _

tools = Blueprint('tools', __name__)


def generate_custom_monster():
    
    return ""

# Route: random monster
@tools.route('/gen/monster', methods=['POST'])
def gen_monster():
    data = request.form
    old_result = data['old-result']
    monster_type = data['monster-select']
    monsters = load_monsters()
    if monster_type == 'custom':
        m = generate_custom_monster()
        render = render_template('partial/tools/random_monster.html', monster=m)
    elif monster_type == 'reaction':
        roll_result = roll_list(monsters['Reaction Roll'])
        render = render_template('partial/tools/reaction_roll.html',roll=roll_result)
    else:
        m = roll_list(monsters['Random Monster'])
        render = render_template('partial/tools/random_monster.html', monster=m)
    new_result = old_result + render
    if monster_type == 'reaction':
        final_render = render_template('partial/tools/reaction_roll_oob.html', roll=roll_result, old_result = old_result,  new_result = new_result)
    else:
        final_render = render_template('partial/tools/random_monster_oob.html', monster=m, old_result = old_result,  new_result = new_result)
    response = make_response(final_render)
    response.headers["HX-Trigger-After-Settle"] = "show-monster-actions"
    return response

# Route: clear monster data
@tools.route('/gen/monster/clear', methods=['GET'])
def clear_monster():
    final_render = render_template('partial/tools/clear_monster.html')
    response = make_response(final_render)
    response.headers["HX-Trigger-After-Settle"] = "hide-monster-actions"
    return response

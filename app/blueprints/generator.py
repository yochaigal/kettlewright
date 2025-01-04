# Multipurpose generator blueprint

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from flask_login import login_required, current_user
from app.models import db, User, Character, Party
from app.forms import *
from app.main import sanitize_data
from app.lib import *
from unidecode import unidecode


generator = Blueprint('generator', __name__)


# Route: generate random character
@generator.route('/gen/character', methods=['POST'])
def character():
    val = '<p>'+generate_character()+'</p>'
    return render_template('partial/tools/pcgen.html',pcgen_value=val)

# Route: clear pc generator value
@generator.route('/gen/character/clear', methods=['GET'])
def character_clear():
    return render_template('partial/tools/pcgen.html',pcgen_value="")
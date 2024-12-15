from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from app.lib import get_char_data, load_market, Market, Inventory
from app.models import db, User, Character, Party
import json

party = Blueprint('party', __name__)


def get_party_data(username, party_id):
    user = User.query.filter_by(username=username).first_or_404()
    party = Party.query.filter_by(id=party_id).first()
    return user, party

# Route: redirect to character view
@party.route('/party/show-user/<username>/<url_name>', methods=['GET'])
def party_show_user(username, url_name):
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name+"/"
    return response


# Route: edit party
@party.route('/party/<username>/<party_id>/edit', methods=['GET'])
def party_edit(username, party_id):
    partyobj, user = get_party_data(username, party_id)    
    if partyobj == None:
        return 
    return render_template('main/party_edit.html', user=user, character=character, username=username, url_name=url_name, images=images)
   

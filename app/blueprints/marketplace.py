from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from app.lib import get_char_data, load_market, Market, Inventory
from app.models import db, User, Character, Party
import json

marketplace = Blueprint('marketplace', __name__)


# Route: show marketplace dialog for a user and character
@marketplace.route('/marketplace/<username>/<url_name>/<container_id>', methods=['GET'])
def marketplace_show(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    market = Market()
    inventory = Inventory(character)
    container = inventory.get_container(container_id)
    capacity = int(container["slots"])-int(inventory.container_slots(container))
    cats = request.args.get("categories")
    if cats != None and cats != "":
        market.set_categories(cats.split(","))
    else:
        market.set_categories([])
    filter = request.args.get("filter")
    if filter != None and filter != "":
        market.set_filter(filter)
    else:
        market.set_filter("")
    return render_template('partial/modal/marketplace.html', user=user, character=character, username=username, url_name=url_name, market=market, container=container, capacity=capacity)

# Route: buy items
@marketplace.route('/marketplace/<username>/<url_name>/<container_id>/buy', methods=['POST'])
def marketplace_buy(username, url_name, container_id):
    user, character = get_char_data(username, url_name)
    market = Market()
    inventory = Inventory(character)
    data = request.form
    if data["current-gold"] != None and data["current-gold"] != "":
        character.gold = int(data["current-gold"])
        db.session.commit()
    if data["current-cart"] != None and len(data["current-cart"]) > 0:
        items = market.buy(json.loads(data["current-cart"]))
        for it in items:
            inventory.create_item(it["name"], ",".join(it["tags"]), it["uses"], it["charges"], it["max_charges"],container_id,it["description"])
    inventory.select(0)
    inventory.decorate()
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name+"/"
    return response
    
    
# Route: cancel buying
@marketplace.route('/marketplace/<username>/<url_name>/cancel', methods=['GET'])
def marketplace_cancel(username, url_name):
    response = make_response("Redirect")
    response.headers["HX-Redirect"] = "/users/"+username+"/characters/"+url_name+"/"
    return response    
    
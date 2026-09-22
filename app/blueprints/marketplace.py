from flask_login import login_required
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, Response
from app.lib import get_char_data, load_market, Market, Inventory
from app.models import db, User, Character, Party
import json
from flask_babel import _

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


def get_shared_market_inventory(party_id, container_id):
    from flask import abort
    from flask_login import current_user
    party = db.session.get(Party, party_id)
    if party is None:
        abort(404)
    members = json.loads(party.members or '[]')
    member = Character.query.filter(Character.id.in_(members), Character.party_id == party.id,
                                    Character.owner == current_user.id).first()
    if party.owner != current_user.id and member is None:
        abort(403)
    inventory = Inventory(party)
    container = inventory.get_container(container_id)
    if container is None:
        abort(404)
    return party, inventory, container


@marketplace.route('/marketplace/party/<int:party_id>/<int:container_id>', methods=['GET', 'POST'])
@login_required
def marketplace_party(party_id, container_id):
    import uuid
    party, inventory, container = get_shared_market_inventory(party_id, container_id)
    market = Market()
    message = None
    error = None
    if request.method == 'POST':
        name = request.form.get('item', '')
        catalog_item = market.find_item_by_name(name)
        if catalog_item is None:
            error = _('Item not found in the marketplace.')
        else:
            item = market.buy([name])[0]
            slots = 0 if 'petty' in item['tags'] else 2 if 'bulky' in item['tags'] else 1
            if inventory.container_slots(container) + slots > int(container['slots']):
                error = _('Not enough space in this container.')
            else:
                item.update(id=uuid.uuid4().hex, location=container_id)
                party.items = json.dumps(json.loads(party.items or '[]') + [item])
                db.session.commit()
                inventory = Inventory(party)
                container = inventory.get_container(container_id)
                message = _('%(item)s added.', item=_(name))
    search = request.values.get('filter', '').strip()
    items = [item for item in market.get_market_items() if search.casefold() in item['name'].casefold()]
    return render_template('partial/modal/marketplace_party.html', party=party, container=container,
                           items=items, search=search, message=message, error=error,
                           capacity=int(container['slots']) - inventory.container_slots(container))

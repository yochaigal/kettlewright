"""Player-owned dropping and pickup through the shared party ground container."""
from flask import Blueprint, abort, make_response, render_template, request
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from werkzeug.exceptions import HTTPException

from app.lib.character_rolls import character_party
from app.lib.ground_items import drop_item, drop_container, ground_items, owned_members, pickup_item
from app.lib.inventory import Inventory
from app.models import Character, Party, User, db

ground = Blueprint('ground', __name__)


def render_ground(party, error=None):
    characters = owned_members(party, current_user.id)
    if not characters and party.owner != current_user.id:
        abort(403)
    template = 'partial/partyview/ground.html' if request.headers.get('HX-Request') else 'main/ground.html'
    inventory = Inventory(party)
    inventory.decorate()
    response = make_response(render_template(template, party=party, ground_items=ground_items(party),
        characters=characters, inventory=inventory, form=FlaskForm(), error=error))
    response.headers['Cache-Control'] = 'no-store'
    return response


@ground.get('/party/<int:party_id>/ground')
@login_required
def view(party_id):
    return render_ground(db.get_or_404(Party, party_id))


@ground.post('/party/<int:party_id>/ground/<item_id>/pickup')
@login_required
def pickup(party_id, item_id):
    if not FlaskForm().validate_on_submit():
        abort(400)
    party = db.get_or_404(Party, party_id)
    characters = owned_members(party, current_user.id)
    character = next((c for c in characters if str(c.id) == request.form.get('character')), None)
    if character is None:
        abort(403)
    error = None
    try:
        with db.session.begin_nested():
            pickup_item(character.id, current_user.id, party.id, item_id)
        db.session.commit()
    except HTTPException as exc:
        error = exc.description
    return render_ground(party, error)


@ground.route('/characters/<int:character_id>/drop/<kind>/<object_id>', methods=['GET', 'POST'])
@login_required
def drop(character_id, kind, object_id):
    character = db.get_or_404(Character, character_id)
    if character.owner != current_user.id:
        abort(403)
    party = character_party(character)
    if party is None:
        abort(400, description='Your character must belong to a party to drop items.')
    inventory = Inventory(character)
    if kind == 'item':
        entry = inventory.get_item(object_id)
    elif kind == 'container' and object_id.isdecimal():
        entry = inventory.get_container(int(object_id))
        if int(object_id) == 0:
            abort(400, description='The main inventory cannot be dropped.')
    else:
        abort(404)
    if entry is None:
        abort(404)
    if kind == 'item' and ('carrying' in entry or entry['name'] == 'Fatigue'):
        abort(400, description='Fatigue and carrying markers cannot be dropped.')
    error = None
    if request.method == 'POST':
        if not FlaskForm().validate_on_submit():
            abort(400)
        try:
            with db.session.begin_nested():
                action = drop_item if kind == 'item' else drop_container
                action(character.id, current_user.id, party.id, object_id, request.form.get('place'))
            db.session.commit()
        except HTTPException as exc:
            error = exc.description
        else:
            inventory = Inventory(character)
            inventory.select(entry['location'] if kind == 'item' else 0)
            inventory.decorate()
            owner = db.session.get(User, character.owner)
            response = make_response(render_template('partial/charedit/inventory.html',
                user=owner, character=character, username=owner.username, url_name=character.url_name,
                inventory=inventory, is_owner=True))
            response.headers['HX-Trigger'] = 'refresh-stats'
            return response
    response = make_response(render_template('partial/modal/drop.html', character=character,
        entry=entry, kind=kind, object_id=object_id, form=FlaskForm(), error=error))
    if error:
        response.headers['HX-Retarget'] = '#modal-anchor'
    response.headers['Cache-Control'] = 'no-store'
    return response

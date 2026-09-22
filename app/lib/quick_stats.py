from flask import abort, jsonify, request
from flask_babel import _
from flask_wtf import FlaskForm

from app.models import db


def save_current_stat(character):
    """Save one current stat after the caller has checked edit permission."""
    if not FlaskForm().validate_on_submit():
        abort(400)
    field = request.form.get('stat')
    if field not in ('hp', 'strength', 'dexterity', 'willpower'):
        abort(400)
    try:
        value = int(request.form['value'])
    except (KeyError, TypeError, ValueError):
        abort(400)
    maximum = getattr(character, field + '_max') or 0
    if not 0 <= value <= maximum:
        return jsonify(error=_('Enter a value between 0 and %(maximum)s.', maximum=maximum)), 400
    setattr(character, field, value)
    db.session.commit()
    return '', 204

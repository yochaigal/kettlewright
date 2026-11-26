from kettlewright import system
from flask import abort, jsonify, request
from flask_babel import _
from flask_wtf import FlaskForm

from app.models import db


def save_current_stat(character):
    """Save one current stat after the caller has checked edit permission.

    character is a Character or Companion: its game system (kettlewright, #487) says which stats there are, and
    get_stat/set_stat keep each in its column or, for a stat without one, in its system_stats."""
    if not FlaskForm().validate_on_submit():
        abort(400)
    field = request.form.get('stat')
    if field not in system().stat_keys:
        abort(400)
    try:
        value = int(request.form['value'])
    except (KeyError, TypeError, ValueError):
        abort(400)
    maximum = character.get_stat(field + '_max', 0) or 0
    if not 0 <= value <= maximum:
        return jsonify(error=_('Enter a value between 0 and %(maximum)s.', maximum=maximum)), 400
    character.set_stat(field, value)
    db.session.commit()
    return '', 204


def save_character_stat(character):
    """Sheet controls; the caller checks owner/Warden edit permission."""
    rules = system()
    field = request.form.get('stat')
    if field in rules.stat_keys:
        return save_current_stat(character)
    if not FlaskForm().validate_on_submit():
        abort(400)
    maxima = tuple(key + '_max' for key in rules.stat_keys)
    conditions = rules.condition_keys
    if field not in (*maxima, *conditions, 'gold'):
        abort(400)
    try:
        value = int(request.form['value'])
    except (KeyError, TypeError, ValueError):
        abort(400)
    maximum = 1 if field in conditions else 9999 if field == 'gold' else 99
    if not 0 <= value <= maximum:
        return jsonify(error=_('Enter a value between 0 and %(maximum)s.', maximum=maximum)), 400
    character.set_stat(field, bool(value) if field in conditions else value)
    if field in maxima:
        current = field.removesuffix('_max')
        character.set_stat(current, min(character.get_stat(current, 0) or 0, value))
    db.session.commit()
    return '', 204

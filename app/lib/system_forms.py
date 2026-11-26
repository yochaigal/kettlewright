"""Character forms for a game system (kettlewright, #487).

app/forms.py declares Cairn's stat fields one by one, with their own labels and validators. The instance's system's
other stats (and conditions) get generated fields: with_system_stats(form_class) is the form class with an
IntegerField for each stat and its maximum, and a BooleanField for each condition, that the class doesn't declare.
The stats and conditions a form saves come from the same system (stat_fields, condition_fields).
"""
from wtforms import BooleanField, IntegerField
from wtforms.validators import InputRequired

from kettlewright import system


def stat_fields():
    """Every stat field and its maximum, in the sheet's order: strength_max, strength, ... hp_max, hp."""
    return [field for stat in system().sheet_stats for field in (stat.key + '_max', stat.key)]


def condition_fields():
    return list(system().condition_keys)


_FORMS = {}


def with_system_stats(form_class):
    """form_class, plus fields for the system's stats and conditions that it doesn't declare (made once)."""
    rules = system()
    key = (form_class, rules.key)
    if key not in _FORMS:
        _FORMS[key] = _build(form_class, rules)
    return _FORMS[key]


def _build(form_class, rules):
    extra = {}
    for stat in rules.stats:
        for field, label in ((stat.key, stat.name), (stat.key + '_max', f'{stat.name} Max')):
            if not hasattr(form_class, field):
                extra[field] = IntegerField(label, validators=[InputRequired()])
    for condition in rules.conditions:
        if not hasattr(form_class, condition.key):
            extra[condition.key] = BooleanField(condition.label)
    if not extra:
        return form_class
    return type(f'{form_class.__name__}{rules.key.title()}', (form_class,), extra)

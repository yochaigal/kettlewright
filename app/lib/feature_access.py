"""Explicit rollout audiences; these checks never replace resource permissions."""
import os
import re

from flask import abort, current_app
from flask_login import current_user


def init_feature_access(app):
    for key in ('FEATURE_TEST_USER_IDS', 'FEATURE_TEST_PARTY_IDS'):
        values = re.split(r'[,\s]+', os.environ.get(key, '').strip())
        if any(value and (not re.fullmatch(r'[0-9]+', value) or int(value) < 1)
               for value in values):
            raise ValueError(f'{key} must contain positive integer IDs separated by commas or whitespace.')
        app.config[key] = frozenset(int(value) for value in values if value)
    app.jinja_env.globals.update(
        user_features_enabled=user_features_enabled,
        party_features_enabled=party_features_enabled,
    )


def user_features_enabled():
    return (current_user.is_authenticated
            and current_user.id in current_app.config.get('FEATURE_TEST_USER_IDS', ()))


def party_features_enabled(party_id):
    return party_id in current_app.config.get('FEATURE_TEST_PARTY_IDS', ())


def require_party_features(party_id):
    if not party_features_enabled(party_id):
        abort(404)

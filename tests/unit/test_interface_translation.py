import json

import pytest
from flask_babel import force_locale

from app.models import Character, User, db


@pytest.mark.parametrize('locale', ['en', 'ru', 'uk'])
def test_marketplace_renders_with_deferred_client_message_parameters(app_with_babel, locale):
    # #given: the Marketplace route accepts a valid owner and Main container.
    with app_with_babel.app_context():
        user = User(username='market-labels', email='market-labels@example.test')
        db.session.add(user)
        db.session.flush()
        character = Character(name='Market', background='Test', owner=user.id,
            owner_username=user.username, url_name='market', gold=200, items='[]',
            containers=json.dumps([{'id': 0, 'name': 'Main', 'slots': 10}]))
        db.session.add(character)
        db.session.commit()
    with app_with_babel.test_client() as client, force_locale(locale):
        # #when
        response = client.get(f'/marketplace/market-labels/market/0?lang={locale}')
    # #then
    assert response.status_code == 200

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


@pytest.mark.parametrize('locale', ['ru', 'uk', 'de', 'es', 'pl', 'pt_BR'])
def test_client_labels_preserve_parameters_and_tools_page_renders(app_with_babel, locale):
    import re
    from flask_babel import Babel
    Babel(app_with_babel, locale_selector=lambda: locale)
    with app_with_babel.test_client() as client, force_locale(locale):
        page = client.get(f'/about?lang={locale}')
        tools = client.get(f'/tools/?lang={locale}')
    assert page.status_code == tools.status_code == 200
    labels = json.loads(re.search(r'<script id="interface-labels"[^>]*>(.*?)</script>',
                                 page.get_data(as_text=True), re.S)[1])
    key = 'Item name must be between 1 and %(maximum)s characters'
    assert labels[key] != key
    assert '%(maximum)s' in labels[key]
    assert labels['Add Container'] != 'Add Container'

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


@pytest.mark.parametrize('locale, label, generator_term', [
    ('ru', 'Гоблиноиды', 'Лужайка'), ('uk', 'Гобліноїди', 'Мурава')])
def test_green_portrait_category_does_not_use_generator_term(app_with_babel, locale, label, generator_term):
    from flask import render_template_string
    # #given: "Green" is also a generator name term with a different meaning.
    with app_with_babel.test_request_context(), force_locale(locale):
        # #when
        html = render_template_string("{% include 'partial/portrait_catalog.html' %}",
            images=['green/green1.png'])
    # #then
    assert label in html
    assert generator_term not in html


@pytest.mark.parametrize('locale', ['ru', 'uk', 'de', 'es', 'pl', 'pt_BR'])
def test_portrait_category_labels_are_translated(app_with_babel, locale):
    import re
    from flask import render_template_string
    # #given: one portrait in every catalog category.
    categories = ['aqua', 'beast', 'brute', 'coldblooded', 'demonic', 'fairy', 'green',
        'human-npcs-for-itmod', 'humanoid', 'insect', 'large', 'monster', 'other', 'statues', 'undead']
    images = ['character.png'] + [f'{category}/portrait.png' for category in categories]
    with app_with_babel.test_request_context():
        with force_locale('en'):
            english = render_template_string("{% include 'partial/portrait_catalog.html' %}", images=images)
        with force_locale(locale):
            # #when
            html = render_template_string("{% include 'partial/portrait_catalog.html' %}", images=images)
    # #then
    labels = lambda page: re.findall(r'>([^<>\n]+)</button>', page)
    assert len(labels(html)) == len(categories) + 1
    assert set(labels(html)).isdisjoint(labels(english))


def test_unchanged_translated_item_text_keeps_english_source(app_with_babel):
    from app.lib import Inventory
    description = ('Its scream frightens away all who hear it (save WIL or flee). '
                   'Recharge: Capture the final breath of a dying warrior.')
    # #given: a stored item whose editor shows the Russian name and description.
    with app_with_babel.test_request_context(), force_locale('ru'):
        character = Character(name='Test', background='Test', items='[]',
                              containers='[{"id": 0, "name": "Main", "slots": 10}]')
        db.session.add(character)
        inventory = Inventory(character)
        item = inventory.create_item('Death-Whistle', 'charges', '', '1', '1', 0, description)
        # #when: the form comes back unchanged, with browser line endings.
        saved = inventory.update_item(item['id'], 'Смерть-свисток', 'charges', '', '1', '1', 0,
            'Его звук пугает всех, кто его слышит (спасбросок ВОЛ или бегство). '
            'Перезарядка: уловите последний вздох умирающего воина.')
        # #then
        assert (saved['name'], saved['description']) == ('Death-Whistle', description)
        # #when: the player renames the item.
        renamed = inventory.update_item(item['id'], 'Мой свисток', 'charges', '', '1', '1', 0, 'Свой текст\r\n')
        # #then
        assert (renamed['name'], renamed['description']) == ('Мой свисток', 'Свой текст\n')

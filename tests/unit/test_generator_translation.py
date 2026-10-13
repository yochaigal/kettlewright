import json
import re
from pathlib import Path

import pytest
from flask_babel import _, force_locale
from flask import render_template, render_template_string

from app.main import translate_events_data
from app.lib.companions import catalog, pet_data
from app.lib.char_utils import item_text
from app.lib.inventory import Inventory
from app.models import Character


DATA = Path(__file__).resolve().parents[2] / 'app/static/json/generators'


@pytest.fixture
def generator_data():
    data = {}
    for filename in ('dungeons', 'forests', 'realm', 'names', 'npcs', 'spellbooks', 'custom-monster'):
        data.update(json.loads((DATA / f'{filename}.json').read_text()))
    return data


def test_russian_generators_keep_terms_in_their_source_context(app_with_babel, generator_data):
    # #given: Cairn's Russian spell, NPC, faction and naming tables.
    data = generator_data
    ruler_index = data['Realm']['Names']['RulerTypes'].index('Realm')
    teleport_index = next(i for i, book in enumerate(data['Spellbooks']) if book['name'] == 'Teleport')
    with app_with_babel.app_context(), force_locale('ru'):
        # #when
        translated = translate_events_data(data)
        # #then
        assert (
            _('Heart'),
            translated['Spellbooks'][teleport_index]['name'],
            translated['Dungeon']['POIs']['Special']['Feature'][18],
            translated['NPCGenerator']['NPCNames']['Names'][35],
            _('Realm'),
            translated['Realm']['Names']['RulerTypes'][ruler_index],
            _('Cautious'),
            translated['NPCGenerator']['NPCTraits']['Virtues'][0],
            translated['Realm']['Theme']['Factions']['FactionTraits']['Trait1'][0],
            translated['Forest']['Properties']['SpiritTraits']['Virtue'][18],
            translated['Dungeon']['POIs']['Lore']['RoomType'][15],
            translated['Names']['Adjectives'][7],
            translated['NPCGenerator']['NPCBackgrounds'][13],
        ) == (
            'Сердце', 'Телепортация', 'Телепортирует', 'Шрауд',
            'Регион', 'Царство', 'Осторожность', 'Осторожный',
            'Осторожные', 'Надежный', 'Конюшня', 'Горький', 'Мистик',
        )


def test_context_lookup_falls_back_for_english_generators(app_with_babel, generator_data):
    # #given
    data = generator_data
    with app_with_babel.app_context(), force_locale('en'):
        # #when
        translated = translate_events_data(data)
    # #then
    assert translated == data


def test_russian_generators_preserve_lookup_markers(app_with_babel, generator_data):
    # #given: these markers are read by the client-side generators.
    data = generator_data
    with app_with_babel.app_context(), force_locale('ru'):
        # #when
        translated = translate_events_data(data)
    # #then
    assert (
        translated['Dungeon']['POIs']['DungeonDieDropTable'],
        translated['Forest']['Trails']['Path'],
        translated['Realm']['Topography']['Difficulty'],
    ) == (
        ['Monster', 'Lore', 'Lore', 'Special', 'Trap', 'Trap'],
        ['Standard', 'Hidden', 'Conditional'],
        ['Easy', 'Easy', 'Easy', 'Tough', 'Tough', 'Perilous'],
    )


def test_pet_without_notes_stays_empty_in_russian(app_with_babel):
    # #given: an ordinary horse has no special notes.
    horse = catalog('pet')['Horse']
    with app_with_babel.app_context(), force_locale('ru'):
        # #when
        result = pet_data(horse, Character(name='Rider'))
    # #then
    assert result['notes'] == ''


def test_russian_equipment_label_keeps_marketplace_identity(app_with_babel):
    # #given: the Russian Marketplace calls its portable trap a "Капкан".
    equipment = {'name': 'Trap', 'tags': ['d6 STR']}
    with app_with_babel.test_request_context('/?lang=ru'), force_locale('ru'):
        # #when
        html = render_template('partial/modal/item_library.html', library=[equipment])
    # #then
    option = re.search(r'<option value="([^"]+)" data-item=\'([^\']+)\'', html)
    assert (option[1], json.loads(option[2])['name']) == ('Капкан', 'Trap')


def test_context_lookup_preserves_existing_ukrainian_translations(app_with_babel, generator_data):
    # #given: dungeon features and NPC traits retain their Ukrainian forms.
    with app_with_babel.app_context(), force_locale('uk'):
        # #when
        data = translate_events_data(generator_data)
    # #then
    assert (
        data['Dungeon']['POIs']['Special']['Feature'][18],
        data['NPCGenerator']['NPCTraits']['Virtues'][0],
    ) == ('Телепортує', 'Обережний')


def test_ukrainian_spell_titles_keep_their_published_names(app_with_babel, generator_data):
    # #given: Ukrainian Cairn, physical pages 35 and 39, names these spells.
    data = generator_data
    vision_index = next(i for i, book in enumerate(data['Spellbooks']) if book['name'] == 'Vision')
    teleport_index = next(i for i, book in enumerate(data['Spellbooks']) if book['name'] == 'Teleport')
    target_index = data['Custom Monster']['MonsterAbilities']['Target'].index('Vision')
    with app_with_babel.app_context(), force_locale('uk'):
        # #when
        translated = translate_events_data(data)
    # #then
    assert (
        translated['Spellbooks'][vision_index]['name'],
        translated['Spellbooks'][teleport_index]['name'],
        translated['Custom Monster']['MonsterAbilities']['Target'][target_index],
        translated['Dungeon']['POIs']['Special']['Feature'][18],
    ) == ('Видіння', 'Телепортація', 'Зір', 'Телепортує')


def test_ukrainian_marketplace_item_keeps_its_catalog_identity(app_with_babel):
    # #given: Ukrainian Cairn, physical page 20, names the Marketplace item.
    equipment = {'name': 'Air bladder', 'tags': []}
    with app_with_babel.test_request_context('/?lang=uk'), force_locale('uk'):
        # #when
        html = render_template('partial/modal/item_library.html', library=[equipment])
    # #then
    option = re.search(r'<option value="([^"]+)" data-item=\'([^\']+)\'', html)
    assert (option[1], json.loads(option[2])['name']) == ('Повітряний міхур', 'Air bladder')


def test_dungeon_features_keep_their_grammatical_form(app_with_babel, generator_data):
    # #given: feature effects use verbs; dungeon conditions use neuter adjectives.
    with app_with_babel.app_context(), force_locale('ru'):
        # #when
        data = translate_events_data(generator_data)
    # #then
    assert (
        data['Dungeon']['POIs']['Special']['Feature'][9],
        data['Realm']['PointsOfInterest']['Dungeons']['Feature'][6],
    ) == ('Создает иллюзию', 'Кристаллическое')


def test_empty_text_stays_empty_when_rendered_in_russian(app_with_babel):
    # #given
    with app_with_babel.test_request_context('/?lang=ru'), force_locale('ru'):
        # #when
        html = render_template_string('{{ description | tr }}', description='')
    # #then
    assert html == ''


def test_purchased_trap_uses_equipment_name_in_inventory(app_with_babel):
    # #given: purchasing keeps the English equipment key in stored inventory.
    item = {'name': 'Trap', 'tags': ['d6 STR']}
    with app_with_babel.app_context(), force_locale('ru'):
        # #when
        title = item_text(item)
    # #then
    assert title == 'Капкан (к6 СИЛ)'


def test_decorated_inventory_uses_equipment_name_and_keeps_stored_key(app_with_babel):
    # #given: the character sheet receives an English-keyed Marketplace item.
    character = Character(name='Rider', items=json.dumps([
        {'id': 'trap', 'name': 'Trap', 'tags': ['d6 STR'], 'location': 0},
    ]), containers='[{"id":0,"name":"Main","slots":10}]')
    with app_with_babel.app_context(), force_locale('ru'):
        inventory = Inventory(character)
        # #when
        inventory.decorate()
        item = inventory.selected_container['items'][0]
    # #then
    assert (item['name'], item['title'].strip()) == ('Trap', 'Капкан (к6 СИЛ)')


def test_russian_book_equipment_and_trait_contexts(app_with_babel):
    from app.lib.translations import translate_term
    from app.lib.generator_labels import generator_labels
    with app_with_babel.app_context(), force_locale('ru'):
        labels = generator_labels()
        # Player pp. 10-11 and 17: the same word has different table forms.
        assert translate_term('Oily', 'character trait: Hair') == 'Сальные'
        assert translate_term('Oily', 'character trait: Skin') == 'Жирная'
        assert translate_term('Soiled', 'character trait: Clothing') == 'Засаленная'
        assert _('Caltrops') == 'Калтропы'
        assert labels['Trap'] == 'Ловушка'
        assert labels['equipment:Trap'] == 'Капкан'


def test_russian_book_spell_and_relic_names(app_with_babel, generator_data):
    with app_with_babel.app_context(), force_locale('ru'):
        spells = {book['name'] for book in translate_events_data(generator_data)['Spellbooks']}
        # Warden pp. 134-147, including previously inconsistent spell titles.
        assert {'Управление погодой', 'Телепортация'} <= spells
        assert _('Mace of the Kingslayer') == 'Булава цареубийцы'
        assert _('Lightsucker Candle') == 'Свеча-светопоглотитель'
        assert _('Cobblehounds') == 'Каменная гончая'


def test_campaign_tables_use_request_language_without_translating_identity_keys(app_with_babel):
    from app.models import User, db
    from flask_babel import Babel
    Babel(app_with_babel, locale_selector=lambda: 'ru')
    app_with_babel.config['FEATURE_TEST_USER_IDS'] = {1}
    with app_with_babel.app_context():
        db.session.add(User(id=1, username='translation-reader'))
        db.session.commit()
    with app_with_babel.test_client() as client:
        with client.session_transaction() as session:
            session['_user_id'] = '1'
            session['_fresh'] = True
        with force_locale('ru'):
            response = client.get('/articles/tables?lang=ru')
            maps = client.get('/maps/tables?lang=ru')
    assert response.status_code == maps.status_code == 200
    data = response.json
    topography = data['Realm']['Topography']
    assert 'Forests' not in topography['Terrain']['Tough']['Terrain']
    assert topography['TerrainKeys']['Леса'] == 'Forests'
    assert data['Forest']['Trails']['Path'] == ['Standard', 'Hidden', 'Conditional']
    assert data['Equipment']['Gear']['Caltrops']['cost'] == 10
    assert maps.json['Realm'] == data['Realm']

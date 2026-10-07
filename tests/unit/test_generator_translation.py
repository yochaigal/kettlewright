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
    for filename in ('dungeons', 'forests', 'realm', 'names', 'npcs', 'spellbooks'):
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
            'Королевство', 'Царство', 'Осторожность', 'Осторожный',
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
    # #given: the existing Ukrainian catalog has ordinary translations only.
    with app_with_babel.app_context(), force_locale('uk'):
        # #when
        data = translate_events_data(generator_data)
    # #then
    assert (
        data['Dungeon']['POIs']['Special']['Feature'][18],
        data['NPCGenerator']['NPCTraits']['Virtues'][0],
    ) == ('Телепортує', 'Обережний')


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

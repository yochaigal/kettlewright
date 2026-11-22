"""Character card resources follow main-inventory capacity and HP rules."""
import json

import pytest

from app.models import Character


def character_with(items, containers=None, **kwargs):
    return Character(items=json.dumps(items), containers=json.dumps(containers or []),
                     hp=4, hp_max=6, **kwargs)


@pytest.mark.parametrize('items, containers, expected', [
    ([], [], 10),
    ([{'tags': [], 'location': 0}], [], 9),
    ([{'tags': ['bulky'], 'location': 0}], [], 8),
    ([{'tags': ['petty'], 'location': 0}], [], 10),
    ([{'tags': [], 'location': 1}], [{'id': 1, 'slots': 20}], 10),
    ([{'tags': [], 'location': 0}] * 10, [], 0),
    ([{'tags': [], 'location': 0}] * 11, [], 0),
    ([{'tags': [], 'location': 0}], [{'id': 0, 'slots': 6}], 5),
    ([], [{'id': 0, 'slots': '12'}, {'id': 1, 'slots': 20}], 12),
])
def test_main_inventory_free_slots(items, containers, expected):
    assert character_with(items, containers).freeMainSlots() == expected


@pytest.mark.parametrize('gold, expected', [(None, 9), (99, 9), (100, 8), (5000, 8)])
def test_coins_from_100gp_take_one_main_slot(gold, expected):
    assert character_with([{'tags': [], 'location': 0}], gold=gold).freeMainSlots() == expected


def test_empty_legacy_inventory():
    assert Character(items=None, containers=None).freeMainSlots() == 10


@pytest.mark.parametrize('items, panicked, expected_hp, expected_slots', [
    ([], False, '4/6', '10 slots free'),
    ([{'tags': [], 'location': 0}] * 9, False, '4/6', '1 slot free'),
    ([{'tags': [], 'location': 0}] * 10, False, '0/6', '0 slots free'),
    ([], True, '0/6', '10 slots free'),
])
def test_character_card_resources(app_with_babel, items, panicked, expected_hp, expected_slots):
    from flask import render_template

    character = character_with(items, name='Card Test', background='Fungal Forager',
                               panicked=panicked)
    with app_with_babel.test_request_context('/'):
        html = render_template('main/characters.html', characters=[character])
    current, maximum = expected_hp.split('/')
    assert f'<dt>HP</dt><dd>{current}<small>/{maximum}</small></dd>' in html
    assert f'>{expected_slots}</p>' in html


def test_nine_items_and_100gp_fill_the_main_inventory(app_with_babel):
    from flask import render_template

    character = character_with([{'tags': [], 'location': 0}] * 9, name='Rich', background='Fungal Forager', gold=100)
    with app_with_babel.test_request_context('/'):
        html = render_template('main/characters.html', characters=[character])
    assert '<dt>HP</dt><dd>0<small>/6</small></dd>' in html and '>0 slots free</p>' in html

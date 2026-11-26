"""Server-side rolls on the Tools tables, for the public API.

Mirrors generateResult() in static/src/js/content_generators.js for the simple
tables, so a roll has the same {title, category, fields} shape in both places.
Realm, Dungeon, Forest and the other worldbuilding generators stay in the browser.
"""
import json
import os
import random

from kettlewright import system


def load_tables(translated=True):
    data = system().content.load('events')  # The system's Warden tables (kettlewright).
    if translated:
        from app.main import translate_events_data
        data = translate_events_data(data)
    return data


def _event(name):
    def roll(data, rng, params):
        return {'title': name, 'category': 'note', 'fields': rng.choice(data[name])}
    return roll


def _weather(data, rng, params):
    seasons = list(data['Weather']['Types'])
    season = params.get('season') or rng.choice(seasons)
    match = next((s for s in seasons if s.casefold() == season.casefold()), None)
    if match is None:
        raise ValueError(f"Unknown season '{season}'. Use one of: {', '.join(seasons)}.")
    kind = rng.choice(data['Weather']['Types'][match])
    return {'title': 'Weather', 'category': 'weather',
            'fields': {'Season': match, 'Type': kind, **data['Weather']['Difficulty'][kind]}}


def _reaction(data, rng, params):
    # 2d6 on an 11-row table (2–12), as in the Tools page.
    return {'title': 'Reaction Roll', 'category': 'note',
            'fields': {'Reaction': data['Reaction Roll'][rng.randint(0, 5) + rng.randint(0, 5)]}}


def _random_monster(data, rng, params):
    monster = rng.choice(data['Random Monster'])
    return {'title': monster['Name'], 'category': 'bestiary', 'fields': monster}


def _custom_monster(data, rng, params):
    m = data['Custom Monster']
    return {'title': 'Custom Monster', 'category': 'bestiary', 'fields': {
        'Physique': rng.choice(m['MonsterAppearance']['Physique']),
        'Feature': rng.choice(m['MonsterAppearance']['Feature']),
        'Quirks': rng.choice(m['MonsterTraits']['Quirks']),
        'Weakness': rng.choice(m['MonsterTraits']['Weakness']),
        'Attack': rng.choice(m['MonsterAttacks']['Type']),
        'Critical Damage': rng.choice(m['MonsterAttacks']['CriticalDamage']),
        'Ability': rng.choice(m['MonsterAbilities']['Ability']),
        'Target': rng.choice(m['MonsterAbilities']['Target']),
    }}


def _item(source, category):
    def roll(data, rng, params):
        item = rng.choice(data[source])
        return {'title': item['name'], 'category': category, 'fields': dict(item)}
    return roll


# API name -> (description, roller)
ROLLS = {
    'dungeon-events': ('Dungeon Events', _event('Dungeon Events')),
    'wilderness-events': ('Wilderness Events', _event('Wilderness Events')),
    'weather': ('Weather; optional ?season=Spring|Summer|Fall|Winter', _weather),
    'reaction': ('Reaction Roll (2d6)', _reaction),
    'random-monster': ('Random Monster', _random_monster),
    'custom-monster': ('Custom Monster', _custom_monster),
    'relic': ('Relics', _item('Relics', 'relic')),
    'spellbook': ('Spellbooks', _item('Spellbooks', 'spellbook')),
}


def roll(table, params=None, rng=None, data=None):
    """Roll on one table. Raises KeyError for an unknown table, ValueError for a bad parameter."""
    _description, roller = ROLLS[table]
    return roller(data if data is not None else load_tables(), rng or random, params or {})

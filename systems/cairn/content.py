"""Cairn's tables, by name: files under systems/cairn/content (rules.content.load(name)).

Tables not named here are '<name>.json' (traits, bonds, omens, scars, barebones, marketplace, monsters,
hirelings, pets). backgrounds/ and generators/ hold one file per table, consolidated when the app starts.
"""

TABLES = {
    'backgrounds': 'backgrounds/background_data.json',
    'monster-portraits': 'monster-portraits.json',
    'events': 'generators/event_data.json',
    'spellbooks': 'generators/spellbooks.json',
}

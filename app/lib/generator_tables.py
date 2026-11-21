"""The generator tables, translated: everything for articles, or the subset maps need."""
import json
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / 'static' / 'json' / 'generators'
TABLE_FILES = ('dungeons', 'forests', 'realm', 'factions', 'npcs', 'names', 'bestiary',
               'custom-monster', 'reliquary', 'spellbooks', 'dungeon-events', 'wilderness-events')
MAP_TABLES = ('Dungeon', 'Forest', 'Realm', 'NPCGenerator', 'Names')


def generator_tables(maps_only=False):
    from app.main import translate_events_data
    data = {}
    for name in TABLE_FILES:
        data.update(json.loads((FOLDER / f'{name}.json').read_text()))
    data['Equipment'] = json.loads((FOLDER.parent / 'marketplace.json').read_text())
    if maps_only:
        data = {key: data[key] for key in MAP_TABLES}
    return translate_events_data(data)

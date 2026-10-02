"""Shared article types, including typed map points and setting seed branches."""
import re

CATEGORIES = {
    'realm': 'Realm', 'people': 'People', 'culture': 'Culture', 'resources': 'Resources',
    'npc': 'NPC', 'faction': 'Faction', 'faction_type': 'Faction types',
    'faction_trait': 'Faction traits', 'advantage': 'Advantages', 'agenda': 'Agendas',
    'topography': 'Topography', 'terrain': 'Terrain', 'landmark': 'Landmark', 'water': 'Water', 'weather': 'Weather',
    'pois': 'POIs', 'settlement': 'Settlement', 'waypoint': 'Waypoint',
    'curiosity': 'Curiosity', 'lair': 'Lair', 'dungeon': 'Dungeon', 'forest': 'Forest',
    'paths': 'Paths', 'path': 'Path', 'room': 'Dungeon room',
    'monster': 'Monster encounter', 'ruins': 'Ruins', 'shelter': 'Shelter',
    'hazard': 'Hazard', 'trap': 'Trap', 'special': 'Special',
    'overview': 'Overview', 'lore': 'Lore', 'relic': 'Relics', 'note': 'Notes',
    'bestiary': 'Bestiary', 'item': 'Items', 'spellbook': 'Spellbooks',
    'map': 'Geography', 'custom': 'Custom',
}
# Two-level authoring picker. Stored article types remain the leaf values.
CATEGORY_GROUPS = {
    'Realm': ('realm',),
    'People': ('people', 'culture', 'resources', 'npc'),
    'Factions': ('faction', 'faction_type', 'faction_trait', 'advantage', 'agenda'),
    'Topography': ('topography', 'terrain', 'landmark', 'water', 'weather', 'forest'),
    'POIs': ('pois', 'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon'),
    'Paths': ('paths', 'path'),
    'Dungeon contents': ('room', 'lore', 'trap', 'special'),
    'Forest contents': ('ruins', 'shelter', 'hazard'),
    'Creatures': ('bestiary', 'monster'),
    'Items': ('item', 'relic', 'spellbook'),
    'Notes': ('note', 'custom'),
}
POINT_TYPES = {'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon', 'forest',
               'terrain', 'landmark', 'water', 'room', 'monster', 'ruins', 'shelter', 'hazard',
               'trap', 'special', 'lore', 'custom'}


def legacy_point_type(title):
    """Only classify explicit generated prefixes; preserve unknown user content."""
    match = re.match(r'^(?:\d+\.\s*)?(?:Heart\s*[·:]\s*)?([A-Za-z]+):', title or '', re.I)
    kind = match.group(1).lower() if match else 'custom'
    return kind if kind in POINT_TYPES else 'custom'

# A canvas belongs to an article; it is never another article type.
ARTICLE_MAP_KINDS = {key: key if key in ('realm', 'forest', 'dungeon') else 'freeform'
                     for key in ('realm', 'topography', 'terrain', 'water', 'forest',
                                 'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon',
                                 'room', 'ruins', 'shelter')}
CATEGORY_ROOTS = {'Realm': 'realm', 'People': 'people', 'Factions': 'faction',
                  'Topography': 'topography', 'POIs': 'pois', 'Paths': 'paths',
                  'Items': 'item', 'Notes': 'note'}

"""Shared article types, including typed map points and setting seed branches."""
import re
from app.lib.translations import N_

CATEGORIES = {
    'realm': N_('Realm'), 'people': N_('People'), 'culture': N_('Culture'), 'resources': N_('Resources'),
    'npc': N_('NPC'), 'faction': N_('Faction'), 'faction_type': N_('Faction types'),
    'faction_trait': N_('Faction traits'), 'advantage': N_('Advantages'), 'agenda': N_('Agendas'),
    'topography': N_('Topography'), 'terrain': N_('Terrain'), 'landmark': N_('Landmark'), 'water': N_('Water'), 'weather': N_('Weather'),
    'pois': N_('POIs'), 'settlement': N_('Settlement'), 'waypoint': N_('Waypoint'),
    'curiosity': N_('Curiosity'), 'lair': N_('Lair'), 'dungeon': N_('Dungeon'), 'forest': N_('Forest'),
    'paths': N_('Paths'), 'path': N_('Path'), 'room': N_('Dungeon room'),
    'monster': N_('Monster encounter'), 'ruins': N_('Ruins'), 'shelter': N_('Shelter'),
    'hazard': N_('Hazard'), 'trap': N_('Trap'), 'special': N_('Special'),
    'overview': N_('Overview'), 'lore': N_('Lore'), 'relic': N_('Relics'), 'note': N_('Notes'),
    'bestiary': N_('Bestiary'), 'item': N_('Items'), 'spellbook': N_('Spellbooks'),
    'map': N_('Geography'), 'custom': N_('Custom'),
}
# Two-level authoring picker. Stored article types remain the leaf values.
CATEGORY_GROUPS = {
    'Realm': ('realm',),
    'People': ('people', 'culture', 'resources', 'npc'),
    'Factions': ('faction', 'faction_type', 'faction_trait', 'advantage', 'agenda'),
    'Topography': ('topography', 'terrain', 'landmark', 'water', 'weather', 'forest'),
    'POIs': ('pois', 'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon'),
    'Paths': ('paths', 'path'),
    'Dungeon': ('room', 'lore', 'trap', 'special'),
    'Forest': ('ruins', 'shelter', 'hazard'),
    N_('Creatures'): ('bestiary', 'monster'),
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

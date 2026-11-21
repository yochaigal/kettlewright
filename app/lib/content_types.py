"""Shared article types, including typed map points and setting seed branches."""
import re
from app.lib.translations import N_

# Party notes are articles written on a party page for that party only. They never
# appear in Campaigns: not in any list, link picker, wiki or editor there.
PARTY_NOTE = 'party_note'

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
    'overview': N_('Overview'), 'lore': N_('Lore'), 'note': N_('Notes'),
    'bestiary': N_('Bestiary'),
    'map': N_('Geography'), 'custom': N_('Custom'),
    # A pin's note on a map: part of the map, never listed with the articles.
    'map_note': N_('Map note'),
}
MAP_NOTE = 'map_note'
# Two-level authoring picker. Stored article types remain the leaf values.
CATEGORY_GROUPS = {
    'Realm': ('realm',),
    'People': ('people', 'culture', 'resources', 'npc'),
    'Factions': ('faction', 'faction_type', 'faction_trait', 'advantage', 'agenda'),
    'Topography': ('topography', 'terrain', 'landmark', 'water', 'weather'),
    'POIs': ('pois', 'settlement', 'waypoint', 'curiosity', 'lair'),
    'Paths': ('paths', 'path'),
    'Dungeon': ('dungeon', 'room', 'lore', 'trap', 'special'),
    'Forest': ('forest', 'ruins', 'shelter', 'hazard'),
    N_('Creatures'): ('bestiary', 'monster'),
    'Notes': ('note', 'custom'),
}
POINT_TYPES = {'settlement', 'waypoint', 'curiosity', 'lair', 'dungeon', 'forest',
               'terrain', 'landmark', 'water', 'room', 'monster', 'ruins', 'shelter', 'hazard',
               'trap', 'special', 'lore', 'custom', 'map_note'}


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
                  'Notes': 'note'}
# Items, relics and spellbooks are not articles any more (#476): they are a module's items
# (app/lib/module_items.py). Articles of these old types became Notes (migration 511a01), and
# files of these types are imported as Notes.
FORMER_ITEM_TYPES = ('item', 'relic', 'spellbook')

# Authoring containment. A missing parent always permits a standalone article.
# General library articles (notes, custom content) are unrestricted.
ARTICLE_PARENT_TYPES = {
    'realm': (), 'people': ('realm',),
    'culture': ('people',), 'resources': ('people',), 'npc': ('people', 'faction'),
    'faction': ('realm', 'faction'),
    'faction_type': ('faction',), 'faction_trait': ('faction',),
    'advantage': ('faction',), 'agenda': ('faction',),
    'topography': ('realm',), 'terrain': ('topography',),
    'landmark': ('terrain',), 'water': ('terrain', 'topography'), 'weather': ('terrain',),
    'pois': ('realm',),
    'settlement': ('pois',), 'waypoint': ('pois',), 'curiosity': ('pois',), 'lair': ('pois',),
    'dungeon': ('pois', 'forest'), 'forest': ('terrain',),
    'paths': ('realm', 'dungeon', 'forest'), 'path': ('paths',),
    'room': ('dungeon',), 'lore': ('dungeon',), 'trap': ('dungeon',), 'special': ('dungeon',),
    'monster': ('dungeon', 'forest', 'bestiary'),
    'ruins': ('forest',), 'shelter': ('forest',), 'hazard': ('forest',),
}


def accepts_article_parent(category, parent):
    allowed = ARTICLE_PARENT_TYPES.get(category)
    if allowed is None:
        return True
    if parent.category not in allowed:
        return False
    # POIs are the region's container, not an arbitrary article with that label.
    return parent.category != 'pois' or bool(parent.parent and parent.parent.category == 'realm')

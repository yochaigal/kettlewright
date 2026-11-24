"""Cairn artwork on empty pages and the 404 (experiment, off unless CAIRN_ART is set).

The art belongs to Cairn Press and its artists: cairnrpg.com licenses Cairn's text under CC-BY-SA 4.0,
not its art. So nothing here ships turned on until Cairn Press says it may, and the images load from
cairnrpg.com rather than being copied into the app. Every piece is shown with its credit.

All of it is black ink on white or on transparent, so it sits on the page in light mode and turns to soft
grey in dark mode. Silhouettes come from the Player's Guide; the ink drawings ("ink") from the adventures.
Each piece is used in one place only.
"""

SITE = 'https://cairnrpg.com/assets/redesign/'
ADVENTURES = 'https://cairnrpg.com/adventures/first-party/img/'
PLAYERS_GUIDE = "Cairn Player's Guide, Cairn Press"
CAS_1 = 'CAS-1: Trouble in Twin Lakes, Cairn Press'
CAS_2 = 'CAS-2: Rise of the Blood Olms, Cairn Press'
CAS_3 = 'CAS-3: The Feast of Tegny Wood, Cairn Press'

ART = {
    # No characters yet: a rider setting out.
    'rider': {'src': SITE + 'step-character-creation-horse.png', 'credit': PLAYERS_GUIDE},
    # No campaigns yet: a standing stone, a cairn.
    'stone': {'src': ADVENTURES + 'cas-1/Stoneblock.webp', 'ink': True, 'credit': CAS_1},
    # No parties yet: a tree and its roots, holding together. A back cover with the tree at its top, so the
    # picture is framed to the tree.
    'roots': {'src': ADVENTURES + 'cas-2/BloodOlm_Backcover.webp', 'ink': True, 'frame': 'cairn-art-roots',
              'credit': CAS_2},
    # A party with no members yet: the Bartermoot camp, waiting for travelers.
    'camp': {'src': ADVENTURES + 'cas-3/Bartermoot.webp', 'ink': True, 'frame': 'cairn-art-wide', 'credit': CAS_3},
    # A party with no monsters: the Chitin Knight.
    'monster': {'src': ADVENTURES + 'cas-3/ChitinKnight.webp', 'ink': True, 'credit': CAS_3},
    # A party with no maps revealed: the region map, still to be explored.
    'map': {'src': ADVENTURES + 'cas-1/CAS1_Map_v2.webp', 'ink': True, 'credit': CAS_1},
    # A party wiki with nothing revealed: a lone tree.
    'tree': {'src': ADVENTURES + 'cas-3/Bloodygrove.webp', 'ink': True, 'credit': CAS_3},
    # Page not found: a bird over the woods.
    'bird': {'src': SITE + 'step-procedures-bird.png', 'credit': PLAYERS_GUIDE},
}

"""The game systems Kettlewright can play, outside the engine's core: an instance plays one of them (#487).

GAME_SYSTEM (in .env) names the one; Cairn when it is not set. The engine imports only that package
(kettlewright.registry.load), which registers its GameSystem. Each system is a package here:

    system/
    ├── __init__.py      this file
    └── cairn/           Cairn, second edition: the system Kettlewright was built for
        ├── __init__.py  registers it
        ├── system.py    its stats, conditions, inventory and rules, as data
        ├── items.py     its item vocabulary: sizes, armor tags, tag groups, Fatigue
        ├── content.py   its tables' names; content/ holds them
        ├── templates/   its template pieces and pages
        ├── web/         its web plug-in: creation and the PDF sheets
        └── README.md

A new system: add a package with the same shape; GAME_SYSTEM=<its folder's name> plays it.
"""

# The system an instance plays when GAME_SYSTEM is not set.
DEFAULT = 'cairn'

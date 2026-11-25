"""Kettlewright's game systems, outside the engine's core (#487).

Each system is a package here: it defines its GameSystem (stats, conditions, inventory, rules), its item
vocabulary and its tables, and registers itself when imported. The engine loads this package on first use
(kettlewright.registry.load), so the core never imports a system by name.

    systems/
    ├── __init__.py      this file: imports each system and names the default one
    └── cairn/           Cairn, second edition: the system Kettlewright was built for
        ├── __init__.py  registers it
        ├── system.py    its stats, conditions, inventory and rules, as data
        ├── items.py     its item vocabulary: sizes, armor tags, tag groups, Fatigue
        ├── content.py   its tables' names; content/ holds them
        ├── templates/   its template pieces and pages
        ├── web/         its web plug-in: creation and the PDF sheets
        └── README.md

A new system: add a package with the same shape and import it below.
"""
from kettlewright.registry import set_default

from systems import cairn  # noqa: F401  (registers Cairn)

# Every campaign, party and character plays this one unless code creates it with another.
DEFAULT = cairn.CAIRN.key
set_default(DEFAULT)

# Game systems

Kettlewright was built for Cairn 2e, and Cairn is the only system it plays today. Issue
[#487](https://github.com/yochaigal/kettlewright/issues/487) asks for other systems one day. This document
describes how the code is laid out for that: a system-agnostic engine (the **`kettlewright`** package), the systems themselves in
their own packages (**systems/**), and how the app asks them for rules instead of writing Cairn's into each page.

None of this shows in the app. Every campaign, party and character plays Cairn; nothing offers a choice.

## Layout

```
kettlewright/           the engine: no system of its own, no Flask, database or translation imports
├── __init__.py         the public API
├── core.py             Stat, Condition, Inventory, GameSystem: the building blocks and default rules
├── registry.py         the registered systems, the default one, and loading the system packages
└── README.md

systems/                the game systems, outside the engine
├── __init__.py         imports each system package and names the default system
└── cairn/              Cairn, second edition
    ├── __init__.py     registers Cairn with the engine
    ├── system.py       Cairn's GameSystem: stats, conditions, inventory, rules
    ├── items.py        its item vocabulary: sizes, armor tags, Fatigue
    ├── content.py      its tables for character creation
    └── README.md

app/                    Kettlewright: asks the engine for rules
├── models/game_system.py   the game_system a campaign, party or character plays, fixed at creation
├── models/game_stats.py    stats without a column of their own (system_stats)
├── lib/system_forms.py     character forms with a system's stats
└── static/src/js/game_system.js   the page's system, for scripts
```

The engine finds the system packages on first use (`kettlewright.registry.load`): the module names in `KETTLEWRIGHT_SYSTEMS`
(comma-separated), or `systems`. Each package registers its systems when imported; `systems/__init__.py`
names the default one. The engine never imports a system by name.

## What a system says

A system is a frozen dataclass that subclasses `kettlewright.GameSystem`:

| Part | Cairn | Used for |
|---|---|---|
| `hit_points`, `attributes` (`Stat`) | HP; STR, DEX, WIL | Sheets, rolls, the whiteboard, exports, forms |
| `Stat.save`, `save_die`, `save_succeeds()` | d20 under the attribute | Saves on the sheet and the whiteboard |
| `Stat.roll`, `roll_stat()` | 3d6 attributes, 1d6 HP | Character creation, the generators, hirelings |
| `conditions` (`Condition`) | Deprived, Panicked, Dead | Sheets, the stat controls, exports, Discord |
| `inventory` (`Inventory`) | 10 slots; petty 0, bulky 2; coins from 100gp | Slots everywhere, ground items, the Marketplace |
| `item_armor()`, `armor_max`, `armor_value()` | Armor tags, at most 3 | Armor on sheets and companions |
| `effective_hp()` | 0 when overloaded or Panicked | HP on sheets, rosters and the whiteboard |
| `can_recover()` | Not while Deprived | Rest |
| `fatigue` | an item named Fatigue | Adding Fatigue, Make Camp, the PDF |
| `item_tags` | bulky, petty, uses, d6, 1 Armor... | Reading items back from Markdown |
| `sheet_sections` | Description, Traits, Bonds, Omens, Scars, Notes | Markdown exports |
| `content` | backgrounds, traits, bonds, omens, scars | Creation tables (files under `app/static/json`) |

Labels (`'STR'`, `'Deprived'`) are English msgids, marked with `N_()` in the system's package; `babel.cfg`
extracts `systems/**.py`, and the app translates them where it shows them.

## How the app plays a system

### Each record keeps the system it was created with

`campaigns`, `parties` and `characters` have a `game_system` column (migration `487a02`):

- A campaign gets the default system; a party, its campaign's (or the default one without a campaign); a
  character, its party's when it is created for one (join code), or the default one.
- From then on it never changes: a flush that changes a saved row's `game_system` raises `GameSystemChanged`
  (`app/models/game_system.py`). A party that leaves its campaign, or a character that leaves its party, keeps it.
- A party only joins a campaign of its own system (all three ways a party joins one refuse with 400), and a
  character only joins a party of its own (its join code is no party for it; `add_character_to_party` refuses).
- Only code creates a campaign with another system: `create_campaign(owner_id, name, game_system='...')`.

`campaign.rules`, `party.rules`, `character.rules` and `companion.rules` (its party's, or its owner's for a pet)
return the system. An unknown key falls back to the default one.

### Stats without a column

Cairn's stats are columns on characters and companions. A stat another system adds is kept in their
`system_stats` JSON column (migration `487a01`):

```python
character.get_stat('luck')        # a column, or system_stats
character.set_stat('luck', 8)
character.stat_values()           # {'hp': [4, 4], 'strength': [10, 10], 'luck': [7, 9]}
character.luck                    # also works, so templates read it like a column
character.export_data()['luck']   # exports list it like the others
```

### Where the rules are read

- **Python**: models (HP, armor, slots), the inventory class (`Inventory(owner).rules`), saves and rolls,
  the stat controls, the whiteboard's stats, roll actors and saves, party rosters, monsters (stat lines,
  new monsters, hirelings), Markdown and PDF exports, Discord commands, rest and Make Camp, the Marketplace.
  Each uses the record's `rules`; code without a record (creation without a party, the generators, imports
  that don't say) uses `kettlewright.system()`, the default one.
- **Forms**: `app/forms.py` declares the default system's stat fields one by one (their labels and validators
  are kept as they were). `with_system_stats(FormClass, rules)` adds fields for another system's stats and
  conditions; the edit form saves them with `set_stat`.
- **Templates**: `rules_for(record)` is a record's system (the default one for anything else) and
  `game_system` the default one. Stat lists in templates loop over them.
- **Scripts**: each page has `<script id="game-system" type="application/json">` with the default system's
  stats (English abbreviation and translated label) and conditions; `game_system.js` reads it (Cairn without
  a page, as in the tests).

## Adding a system

1. Add a package beside `systems/cairn` with the same shape: a `GameSystem` subclass (stats with their
   creation dice, conditions, inventory, item vocabulary, sheet sections, tables) and an `__init__.py` that
   calls `kettlewright.register(...)`.
2. Import it in `systems/__init__.py`.
3. Mark its labels with `N_()` and add their translations.
4. Create a campaign with it in code (`create_campaign(..., game_system='key')`).

`tests/unit/test_kettlewright.py` defines a made-up system (Lucky: STR and Luck, Luck stored in `system_stats`,
saves rolled over, no Fatigue, Deprived still recovers) and runs it through a campaign, its party and a
character: the sheet, the edit form, the stat controls, the whiteboard, a save, Markdown, hirelings, rest and
the monster parser.

## Still Cairn's

These parts of the app still assume Cairn, and a second system needs them:

- **Layouts**: the character page, the printed sheet and its PDF form, the compact Discord sheet and the
  party cards are laid out for HP, three attributes, Armor and ten slots.
- **Content**: backgrounds (2e and the Barebones d100), traits, bonds, omens, scars, the bestiary, hirelings,
  pets, Marketplace items, the generators' tables and the CAS modules are Cairn's files. A system names its
  tables (`content`), but they are still read from `app/static/json`.
- **Creation procedures**: 2e creation (background, its tables, bond, omen, age, gold) and Barebones are
  Cairn's steps. The system gives the dice and tables, not the steps.
- **Scripts and Discord registration**: the page's system block and the `/kw` command choices are the default
  system's (Discord registers commands once for the whole app); a command reads the character's own system.
- **JSON import**: reads the default system's stats; it doesn't carry `game_system` or `system_stats` yet.
- **Rules not modelled**: damage (HP, then a STR save, then critical damage), the reaction roll, Die of
  Fate, the wilderness and dungeon tables, the Warden's dice.

# Game systems

Kettlewright was built for Cairn 2e, and Cairn is the only system it plays today. Issue
[#487](https://github.com/yochaigal/kettlewright/issues/487) asks for other systems one day. This document
describes how the code is laid out for that: a system-agnostic engine (the **`kettlewright`** package, with a
half in the browser), the systems themselves in their own packages (**`system/`**), and how the app asks the
engine for rules instead of writing Cairn's into each page and script.

**One system per instance.** Whoever runs Kettlewright picks the system before starting it, with an environment
variable, and everything the instance stores plays it:

```
GAME_SYSTEM=cairn      # in .env: a folder in system/; Cairn when it is not set
```

Another system means a fork (or another deployment) with another `GAME_SYSTEM`. Nothing in the app offers a
choice, and no campaign, party or character records a system of its own.

## The design in one paragraph

A system is **data**: its stats, conditions and what they do, inventory, armor, saves, item tags, Warden rolls
and tables. The engine applies the same generic rules to that data twice, on the server
(`kettlewright/core.py`) and in the browser (`kettlewright/static/kettlewright.js`, from the page's copy of the
data), so a rule is written once and the two halves can't drift apart. What can't be data, a system writes
once in Python and, if pages need it, once in JavaScript (`registerRules`). What is a system's own presentation
(its wording, its sheet, its creation pages) lives in the system's package, and the app reaches it through the
engine, never by importing the system. The engine loads only the system `GAME_SYSTEM` names.

## Layout

```
kettlewright/                 the engine: no system of its own
├── __init__.py               the public API
├── core.py                   Stat, Condition (and its effects), Inventory, Armor, WardenRoll, GameSystem:
│                             a system's data and the generic rules that read it; manifest() for the browser
├── content.py                Content: a system's tables, read from its package
├── registry.py               the instance's system: GAME_SYSTEM, loading its package
├── web.py                    the engine in a Flask app (its only Flask-aware module): files, templates, the
│                             page's copy of the system, its plug-in
├── static/kettlewright.js    the browser engine, imported as '#kettlewright'
├── templates/kettlewright/   generic template pieces, for a system without its own
└── README.md

system/                       the game systems, outside the engine; an instance plays one
├── __init__.py               names the DEFAULT one (cairn), for an instance without GAME_SYSTEM
└── cairn/                    Cairn, second edition
    ├── __init__.py           registers Cairn with the engine
    ├── system.py             Cairn's GameSystem: all data
    ├── items.py              its item vocabulary: sizes, armor tags, tag groups, Fatigue
    ├── content.py            its table names
    ├── content/              its tables (backgrounds, traits, bonds, omens, scars, Barebones, Marketplace,
    │                         bestiary, hirelings, pets, the Warden's generators)
    ├── templates/            its template pieces (cairn/...) and its creation and generator pages
    ├── web/                  its web plug-in: creation (2e, Barebones, the quick generator), the PDF sheets
    └── README.md

app/                          Kettlewright: asks the engine
├── models/game_stats.py      stats without a column of their own (system_stats)
└── lib/system_forms.py       character forms with the system's stats
```

### Who may import whom

```
app  ──────────►  kettlewright (core, web)  ◄──────────  system/<key>   (pure: rules, data, templates)
 ▲                        │
 │                        └── loads, by module name ──►  system/<key>/web   (may use the app)
 └──────────────────────────────────────────────────────────────┘
```

- The engine's core imports nothing of the app, Flask or the database (`test_the_engine_stands_alone…`), and never
  names a system (`test_the_core_has_no_system…`, `test_the_browser_engine_has_no_system_of_its_own`).
- A system's package is plain Python too, except its `web/` plug-in, which may use the app.
- The app never imports `system` (`test_the_app_reaches_cairn_only_through_the_engine`): it asks the engine for the
  instance's system (`kettlewright.system()`), and reaches its web parts through `kettlewright.web.plugin()`.

## What a system says

A system is a frozen dataclass that subclasses `kettlewright.GameSystem`. Cairn's whole definition is data:

| Part | Cairn | Used for |
|---|---|---|
| `hit_points`, `attributes` (`Stat`) | HP; STR, DEX, WIL | Sheets, rolls, the whiteboard, exports, forms |
| `Stat.save`, `save_die`, `save_under` | d20 under the attribute | Saves on the sheet, the whiteboard, the Warden's dice |
| `Stat.roll` | 3d6 attributes, 1d6 HP | Creation, the generators, hirelings |
| `conditions` (`Condition`, with `effects`) | Deprived (`no_recovery`), Panicked (`zero_hp`, `weak_attacks`), Dead (`out_of_play`) | HP, rest, Make Camp, attacks, who can act, badges |
| `weak_die` | 4 | An attack's die under `weak_attacks` |
| `inventory` (`Inventory`) | 10 slots, full means 0 HP; petty 0, bulky 2; coins from 100gp | Slots everywhere, the Marketplace, the board |
| `armor` (`Armor`) | 1–3 Armor tags, at most 3; Sloth-Tarp needs activating; bonus defense | Armor on sheets and companions, item tags |
| `item_tag_groups`, `item_tags` | bulky/petty, uses/charges, d4–d12, armor; blast, bonus defense | The item editors, Markdown, Discord |
| `fatigue` | an item named Fatigue | Adding and clearing Fatigue, Make Camp |
| `warden_rolls` (`WardenRoll`) | Reaction Roll (2d6: Hostile…Helpful), Die of Fate (d6) | The Warden's dice, Discord |
| `sheet_sections` | Description, Traits, Bonds, Omens, Scars, Notes | Markdown exports |
| `wording` | "Deprived, no HP recovered: …" | Rest and Make Camp reports (else the engine's `WORDING`) |
| `home`, `tables` | `system/cairn`, its table names | `rules.content.load('traits')` |
| `web` | `'system.cairn.web'` | Its web plug-in (below) |

The rules (`effective_hp`, `can_recover`, `attack_die`, `armor_value`, `save_succeeds`, `item_size`…) read this data.
A system whose rule can't be said as data overrides the method, and registers the same rule for pages in
JavaScript. Labels are English msgids marked with `N_()`; `babel.cfg` extracts `kettlewright/**.py`,
`system/**.py`, their templates and `system/**/content/**.json`.

The app reads the system's tables (backgrounds, traits, bonds, omens, scars, the Marketplace, the bestiary,
hirelings, pets, the Warden's generators) from its `content/`: a system ships its own.

## The browser engine

Every page carries the system as data: `{{ kettlewright_manifest() }}` writes
`<script id="game-system" type="application/json">` from `GameSystem.manifest()`, labels translated.

Scripts import the engine as `'#kettlewright'`:

```js
import {itemSize, slotsUsed, effectiveHp, armorValue, saveDie, conditionsWith, ZERO_HP} from '#kettlewright';
```

- On pages, `{{ kettlewright_importmap() }}` maps it (before any module script); the whiteboard adds it to its own
  import map.
- In the Discord Activity, where no import map is allowed, `app/lib/activity.py` rewrites the import.
- In Node, `package.json`'s `imports` maps it to the file.

It has no system of its own: without a page it plays the plainest rules, and tests give it one with `useSystem()`.
`tests/js/support/cairn.mjs` loads Cairn from `tests/js/support/cairn-system.json`, which
`test_the_js_tests_play_cairn_as_the_server_sends_it` keeps in step with `system/cairn` (its docstring has the
command that regenerates it).

A system's rule that data can't say: its `static/rules.js` calls
`registerRules('<key>', {itemSize(item, base) {...}})`; the engine loads it before any module that imports it runs.

## Templates

App templates read the system (`game_system`) instead of naming Cairn's stats and conditions. Where a page has the
system's own wording or layout, it includes a **piece**:

```jinja
{% include system_template('help/monster_format.html') %}
```

which is `system/<key>/templates/<key>/help/monster_format.html` if the system has it, else the engine's generic
`kettlewright/templates/kettlewright/help/monster_format.html`. Cairn's pieces:

| Piece | What it is |
|---|---|
| `charview/zero_hp_reason.html` | Why HP counts as 0: a full inventory, or Panic |
| `help/monster_format.html` | The monster import's stat line (HP, Armor, STR, DEX, WIL) |
| `help/discord_sheet_commands.html` | Discord's `/kw stat`, `condition` and `fatigue` |
| `partyview/rest_hint.html` | Resting in a dungeon |
| `item/tag_buttons.html` | The item editors' tag buttons, in Cairn's rows |

A system's own pages (Cairn's creation and generator pages) are in its `templates/` too, under their usual names.

## A system's web plug-in

A system that names a module in `web` gets its `init_app(app)` called when the app starts, to register its pages.
The app asks it, through `kettlewright.web.plugin()`, for:

| Function | Cairn |
|---|---|
| `creation_page(method)` | 2e (`/new_character/`) or Barebones creation |
| `random_character(background)` | The quick generator, for `/api/v1/characters/random` |
| `gear_packages()`, `barebones_data()` | Barebones packages and tables (Tools, the API, Markdown import) |
| `random_name(background)` | A hireling's name (without a plug-in, hirelings are named by their role) |
| `character_sheet(character, party, orientation)` | The PDF, drawn on Cairn's own sheets |

## How the app plays a system

### One system, chosen before the instance starts

`kettlewright.system()` is the system the instance plays: the package `GAME_SYSTEM` names in `system/`, or
`system/__init__.py`'s `DEFAULT` (`cairn`) without it. The engine imports that package on first use and nothing
else; an unknown name stops the app with `UnknownGameSystem` and the systems there are.

- Campaigns, parties and characters don't record a system (migration `487a03` dropped the `game_system` columns
  `487a02` had added): they all play the instance's. Any party joins any campaign, any character any party.
- A character's JSON export says its system (`"game_system": "cairn"`); importing a character of another system is
  refused. A file that doesn't say is taken as the instance's.
- Changing `GAME_SYSTEM` on an instance that has data is not supported: its characters keep the stats they have.
- Tests play another system with `kettlewright.use_system(rules)`.

### Stats without a column

Cairn's stats are columns on characters and companions. A stat another system adds is kept in their
`system_stats` JSON column (migration `487a01`), and JSON exports and imports carry it:

```python
character.get_stat('luck')        # a column, or system_stats
character.set_stat('luck', 8)
character.stat_values()           # {'hp': [4, 4], 'strength': [10, 10], 'luck': [7, 9]}
character.luck                    # also works, so templates read it like a column
```

### Discord

`/kw stat`, `/kw condition` and `/kw warden-roll` offer the system's stats, conditions and Warden rolls.

## Adding a system

1. Add a package beside `system/cairn` (its folder's name is its key): a `GameSystem` subclass with its data, its
   tables in `content/`, and an `__init__.py` that calls `kettlewright.register(...)`.
2. Mark its labels with `N_()` and add their translations.
3. Add template pieces where the engine's generic ones don't say it right, and a `web/` plug-in for its creation
   pages and PDF sheet.
4. Run an instance with `GAME_SYSTEM=<key>`.

`tests/unit/test_kettlewright.py` defines a made-up system (Lucky: STR and Luck, Luck stored in `system_stats`,
saves rolled over, no Fatigue, no web plug-in), plays it with `use_system`, and runs a campaign, its party and a
character through it: the sheet, the edit form, the stat controls, the whiteboard, a save, Markdown, JSON import,
hirelings, rest and the monster parser. It also starts Python with `GAME_SYSTEM` set to check which system loads.
`tests/js/kettlewright_engine.test.mjs` runs the browser engine's rules for Cairn, the plainest rules, a page's own
system and a system's JavaScript rule.

## Still Cairn's, on purpose

- **Cairn's stats are columns** (`strength`, `deprived`…). Every read and write goes through `get_stat`/`set_stat`,
  so they are an implementation detail; moving them into `system_stats` would cost a data migration and typed
  columns for nothing a second system needs.
- **The character forms** (`app/forms.py`) declare Cairn's stat fields one by one, for their labels and validators;
  `with_system_stats` adds another system's.
- **Editions**: `Character.edition` (2e or Barebones) and `Party.official_barebones` are in the data model, so the app
  knows Cairn has two ways of creating characters, and asks Cairn's plug-in for them.
- **The JSON import form** (`CharacterJSONForm`) has Cairn's stat columns; another system's page sends 0 for those
  it doesn't have.
- **Content the whole app shows**: the portrait art (`app/static/images`) is Cairn's; the translations of every
  system are in `app/translations`.

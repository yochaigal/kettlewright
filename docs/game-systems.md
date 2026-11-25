# Game systems

Kettlewright was built for Cairn 2e, and Cairn is the only system it plays today. Issue
[#487](https://github.com/yochaigal/kettlewright/issues/487) asks for other systems one day. This document
describes how the code is laid out for that: a system-agnostic engine (the **`kettlewright`** package, with a
half in the browser), the systems themselves in their own packages (**`systems/`**), and how the app asks them
for rules instead of writing Cairn's into each page and script.

None of this shows in the app. Every campaign, party and character plays Cairn; nothing offers a choice.

## The design in one paragraph

A system is **data**: its stats, conditions and what they do, inventory, armor, saves, item tags, Warden rolls
and tables. The engine applies the same generic rules to that data twice, on the server
(`kettlewright/core.py`) and in the browser (`kettlewright/static/kettlewright.js`, from the page's copy of the
data), so a rule is written once and the two halves can't drift apart. What can't be data, a system writes
once in Python and, if pages need it, once in JavaScript (`registerRules`). What is a system's own presentation
(its wording, its sheet, its creation pages) lives in the system's package, and the app reaches it through the
engine, never by importing the system.

## Layout

```
kettlewright/                 the engine: no system of its own
├── __init__.py               the public API
├── core.py                   Stat, Condition (and its effects), Inventory, Armor, WardenRoll, GameSystem:
│                             a system's data and the generic rules that read it; manifest() for the browser
├── content.py                Content: a system's tables, read from its package
├── registry.py               the registered systems, the default one, loading the system packages
├── web.py                    the engine in a Flask app (its only Flask-aware module): files, templates, the
│                             page's system, system plug-ins
├── static/kettlewright.js    the browser engine, imported as '#kettlewright'
├── templates/kettlewright/   generic template pieces, for a system without its own
└── README.md

systems/                      the game systems, outside the engine
├── __init__.py               imports each system package and names the default system
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
├── models/game_system.py     the game_system a campaign, party or character plays, fixed at creation
├── models/game_stats.py      stats without a column of their own (system_stats)
└── lib/system_forms.py       character forms with a system's stats
```

### Who may import whom

```
app  ──────────►  kettlewright (core, web)  ◄──────────  systems/<key>   (pure: rules, data, templates)
 ▲                        │
 │                        └── loads, by module name ──►  systems/<key>/web   (may use the app)
 └──────────────────────────────────────────────────────────────┘
```

- The engine's core imports nothing of the app, Flask or the database (`test_the_engine_stands_alone…`), and never
  names a system (`test_the_core_has_no_system…`, `test_the_browser_engine_has_no_system_of_its_own`).
- A system's package is plain Python too, except its `web/` plug-in, which may use the app.
- The app never imports `systems` (`test_the_app_reaches_cairn_only_through_the_engine`): it asks a record for its
  `rules`, and reaches a system's web parts through `kettlewright.web.plugin(rules)`.

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
| `home`, `tables` | `systems/cairn`, its table names | `rules.content.load('traits')` |
| `web` | `'systems.cairn.web'` | Its web plug-in (below) |

The rules (`effective_hp`, `can_recover`, `attack_die`, `armor_value`, `save_succeeds`, `item_size`…) read this data.
A system whose rule can't be said as data overrides the method, and registers the same rule for pages in
JavaScript. Labels are English msgids marked with `N_()`; `babel.cfg` extracts `kettlewright/**.py`,
`systems/**.py`, their templates and `systems/**/content/**.json`.

## The browser engine

Every page carries its system as data: `{{ kettlewright_manifest() }}` writes
`<script id="game-system" type="application/json">` from `GameSystem.manifest()`, labels translated. It is the
system of the page's character, companion, party or campaign, else the default one; the whiteboard has its party's.

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
`test_the_js_tests_play_cairn_as_the_server_sends_it` keeps in step with `systems/cairn` (its docstring has the
command that regenerates it).

A system's rule that data can't say: its `static/rules.js` calls
`registerRules('<key>', {itemSize(item, base) {...}})`; the engine loads it before any module that imports it runs.

## Templates

App templates read rules (`rules_for(character)`, `game_system`) instead of naming Cairn's stats and conditions.
Where a page has a system's own wording or layout, it includes a **piece**:

```jinja
{% include system_template('help/monster_format.html', party) %}
```

which is `systems/<key>/templates/<key>/help/monster_format.html` if the system has it, else the engine's generic
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
The app asks it, through `kettlewright.web.plugin(rules)`, for:

| Function | Cairn |
|---|---|
| `creation_page(method)` | 2e (`/new_character/`) or Barebones creation |
| `random_character(background)` | The quick generator, for `/api/v1/characters/random` |
| `gear_packages()`, `barebones_data()` | Barebones packages and tables (Tools, the API, Markdown import) |
| `random_name(background)` | A hireling's name |
| `character_sheet(character, party, orientation)` | The PDF, drawn on Cairn's own sheets |

## How the app plays a system

### Each record keeps the system it was created with

`campaigns`, `parties` and `characters` have a `game_system` column (migration `487a02`):

- A campaign gets the default system; a party, its campaign's (or the default one without a campaign); a
  character, its party's when it is created for one (join code), the file's when imported from JSON (if the app
  plays it), or the default one.
- From then on it never changes: a flush that changes a saved row's `game_system` raises `GameSystemChanged`
  (`app/models/game_system.py`). A party that leaves its campaign, or a character that leaves its party, keeps it.
- A party only joins a campaign of its own system, and a character only joins a party of its own.
- Only code creates a campaign with another system: `create_campaign(owner_id, name, game_system='...')`.

`campaign.rules`, `party.rules`, `character.rules` and `companion.rules` return the system; an unknown key falls
back to the default one. `rules.active_conditions(record)` reads which of its conditions a record has on.

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

Discord registers the commands once for the whole app, so `/kw stat`, `/kw condition` and `/kw warden-roll` offer
every registered system's stats, conditions and Warden rolls; a command reads the character's (or party's) own.

## Adding a system

1. Add a package beside `systems/cairn`: a `GameSystem` subclass with its data, its tables in `content/`, and an
   `__init__.py` that calls `kettlewright.register(...)`. Import it in `systems/__init__.py`.
2. Mark its labels with `N_()` and add their translations.
3. Add template pieces where the engine's generic ones don't say it right, and a `web/` plug-in for its creation
   pages and PDF sheet.
4. Create a campaign with it in code (`create_campaign(..., game_system='key')`).

`tests/unit/test_kettlewright.py` defines a made-up system (Lucky: STR and Luck, Luck stored in `system_stats`,
saves rolled over, no Fatigue, no web plug-in) and runs it through a campaign, its party and a character: the sheet,
the edit form, the stat controls, the whiteboard, a save, Markdown, JSON import, hirelings, rest and the monster
parser. `tests/js/kettlewright_engine.test.mjs` runs the browser engine's rules for Cairn, the plainest rules, a
page's own system and a system's JavaScript rule.

## Still Cairn's, on purpose

- **Cairn's stats are columns** (`strength`, `deprived`…). Every read and write goes through `get_stat`/`set_stat`,
  so they are an implementation detail; moving them into `system_stats` would cost a data migration and typed
  columns for nothing a second system needs.
- **The character forms** (`app/forms.py`) declare Cairn's stat fields one by one, for their labels and validators;
  `with_system_stats` adds another system's.
- **Editions**: `Character.edition` (2e or Barebones) and `Party.official_barebones` are in the data model, so the app
  knows Cairn has two ways of creating characters, and asks Cairn's plug-in for them.
- **Content the whole app shows**: the Tools page's generators and the portrait art (`app/static/images`) are Cairn's
  but shared by every page; the translations of every system are in `app/translations`.

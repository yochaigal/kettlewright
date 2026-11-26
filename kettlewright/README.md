# The Kettlewright engine

`kettlewright` is the game-system engine the app runs on ([#487](https://github.com/yochaigal/kettlewright/issues/487)).
It is system-agnostic: it defines what a game system is, applies a system's rules (in Python here, and in the browser
in `static/kettlewright.js`), and loads the one system an instance plays (`GAME_SYSTEM`), from its package in
[`system/`](../system).
See [docs/game-systems.md](../docs/game-systems.md) for the design and how the app uses it.

## Files

| File | What it holds |
|---|---|
| `core.py` | `Stat`, `Condition` (and its `EFFECTS`), `Inventory`, `Armor`, `WardenRoll`, `GameSystem`: a system's data and the generic rules that read it; `manifest()` for the browser |
| `content.py` | `Content`: a system's tables, read from its package |
| `registry.py` | `system()`, `load()`, `register`, `configured_key()`, `available()`, `use_system()`, `UnknownGameSystem` |
| `web.py` | `init_app(app)`, the only Flask-aware module: the engine's and the system's files and templates, the page's copy of the system, `plugin()` |
| `static/kettlewright.js` | The browser engine, imported as `'#kettlewright'`: the same rules over the page's system |
| `templates/kettlewright/` | Generic template pieces, for a system without its own |
| `__init__.py` | The public API |

## The API

```python
from kettlewright import system, ZERO_HP

rules = system()                       # the system the instance plays (GAME_SYSTEM)
rules.stat_keys                        # ('hp', 'strength', 'dexterity', 'willpower')
rules.abbr('dexterity')                # 'DEX'
rules.save_succeeds(roll=7, score=12)  # Cairn: roll under
rules.roll_stat('hp')                  # a new character's HP
rules.inventory.item_size(item)        # slots an item takes
rules.armor_value(items, base=0)
rules.active_conditions(character)     # ('panicked',)
rules.conditions_with(ZERO_HP)         # ('panicked',) in Cairn
rules.effective_hp(hp, occupied_slots, conditions)
rules.can_recover(conditions)
rules.attack_die(conditions)           # 4 while Panicked in Cairn, else None
rules.warden_roll('reaction').outcome(7)   # 'Curious'
rules.words('rest_blocked')            # the system's wording, or the engine's
rules.content.load('traits')           # a table, parsed
rules.manifest()                       # all of it as data, for the browser
```

```js
import {itemSize, occupiedMainSlots, effectiveHp, armorValue, saveDie, useSystem} from '#kettlewright';
```

## The instance's system

An instance plays one system. `GAME_SYSTEM` (an environment variable, in `.env`) names its package in `system/`;
without it, the one `system/__init__.py` names as `DEFAULT` (`cairn`). On first use, `load()` imports
`system.<GAME_SYSTEM>`, whose `__init__.py` calls `register(...)`; an unknown name raises `UnknownGameSystem` with
the systems there are (`available()`). Another system means another `GAME_SYSTEM` and a restart.

`use_system(rules)` plays another system for a while, as a context manager: for tests and tools.

## Defaults

`GameSystem`'s defaults are the plainest reading of each rule, so a system only says what differs: saves roll under
a d20, every item takes one slot, no armor and no armor cap, conditions do nothing, HP is what the sheet says, rest
always recovers, there is no Fatigue and no Warden roll. The browser engine plays the same defaults without a system.

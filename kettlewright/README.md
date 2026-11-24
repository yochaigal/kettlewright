# The Kettlewright engine

`kettlewright` is the game-system engine the app runs on ([#487](https://github.com/yochaigal/kettlewright/issues/487)).
It is system-agnostic: it defines what a game system is and keeps the registered ones, and the systems
themselves live outside it, in [`systems/`](../systems). Plain Python: no Flask, database or translation imports.

See [docs/game-systems.md](../docs/game-systems.md) for how the app uses it.

## Files

| File | What it holds |
|---|---|
| `core.py` | `Stat`, `Condition`, `Inventory` and `GameSystem`: the parts of a system and its default rules |
| `registry.py` | `register`, `system(key)`, `system_or_default(key)`, `default_key()`, `load()` |
| `__init__.py` | The public API |

## The API

```python
from kettlewright import system, register

rules = system()                       # the default system
rules = system('cairn')                # by key; KeyError if unknown
rules.stat_keys                        # ('hp', 'strength', 'dexterity', 'willpower')
rules.sheet_stats                      # the attributes, then HP: the order of the printed sheet
rules.abbr('dexterity')                # 'DEX'
rules.save_succeeds(roll=7, score=12)  # Cairn: roll under
rules.stat('strength').dice            # '3d6'
rules.roll_stat('hp')                  # a new character's HP
rules.inventory.item_size(item)        # slots an item takes
rules.inventory.occupied_main_slots(items, gold)
rules.armor_value(items, base=0)
rules.effective_hp(hp, occupied_slots, conditions)
rules.can_recover(conditions)
rules.fatigue                          # the Fatigue item's name, or None
rules.content_path('traits')           # a creation table's file
```

## Loading systems

On first use, `load()` imports the packages named in `KETTLEWRIGHT_SYSTEMS` (comma-separated), or `systems`. Each
package registers its systems when imported (`register(...)`) and may set the default (`set_default(key)`);
without one, the first registered system is the default.

## Defaults

`GameSystem`'s defaults are the plainest reading of each rule, so a system only overrides what differs:
saves roll under, every item takes one slot, no armor and no armor cap, HP is what the sheet says, rest always
recovers, and there is no Fatigue.

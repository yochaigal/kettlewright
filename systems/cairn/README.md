# Cairn

[Cairn](https://cairnrpg.com), second edition: the system Kettlewright was built for, and its default one.
See [docs/game-systems.md](../../docs/game-systems.md) for how systems fit into Kettlewright.

| File | What it holds |
|---|---|
| `system.py` | `Cairn`, its `GameSystem`: HP and STR, DEX and WIL (3d6, HP 1d6), saves as a d20 under the attribute, Deprived, Panicked and Dead, ten slots, armor up to 3, 0 HP when overloaded or Panicked, no recovery while Deprived, and its sheet sections |
| `items.py` | Its item vocabulary: petty (no slot) and bulky (two slots), the armor tags and the Sloth-Tarp's activation, Fatigue, and every tag an item can carry |
| `content.py` | Its tables for character creation: backgrounds, traits, bonds, omens and scars (files under `app/static/json`) |
| `__init__.py` | Registers `CAIRN` with the engine |

Labels are marked with `N_()`, so `pybabel extract` finds them; the translations are in `app/translations`.

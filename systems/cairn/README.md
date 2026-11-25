# Cairn

[Cairn](https://cairnrpg.com), second edition: the system Kettlewright was built for, and its default one.
See [docs/game-systems.md](../../docs/game-systems.md) for how systems fit into Kettlewright.

| Path | What it holds |
|---|---|
| `system.py` | `Cairn`, its `GameSystem`, all data: HP and STR, DEX and WIL (3d6, HP 1d6), saves as a d20 under the attribute, Deprived (no recovery), Panicked (0 HP, d4 attacks) and Dead (out of play), ten slots (full means 0 HP), armor up to 3, the Reaction Roll and Die of Fate, its sheet sections and its wording |
| `items.py` | Its item vocabulary: petty (no slot) and bulky (two slots), the armor tags, the Sloth-Tarp's activation and bonus defense, the tag groups, Fatigue |
| `content.py`, `content/` | Its tables: backgrounds, traits, bonds, omens, scars, Barebones, the Marketplace, the bestiary, hirelings, pets and the Warden's generators |
| `templates/cairn/` | Its template pieces: why HP is 0, the monster format, the Discord commands, resting, the item tag buttons |
| `templates/` | Its creation and quick generator pages |
| `web/` | Its web plug-in: 2e and Barebones creation, the quick generator, the PDF sheets (`pdf_templates/`) |
| `__init__.py` | Registers `CAIRN` with the engine |

Labels are marked with `N_()`, so `pybabel extract` finds them; the translations are in `app/translations`.
Everything here but `web/` is plain Python; `web/` uses the app, and the app reaches it only through the engine.

"""The Kettlewright engine: the game-system engine Kettlewright runs on (#487).

A game system (kettlewright.core.GameSystem) says what a character sheet holds (HP, attributes, conditions,
inventory) and the rules that read it (saves, armor, slots, when HP drops to zero). the app asks the engine
for these instead of writing a system's rules into each page. the engine's core is system-agnostic: the systems
themselves live in packages outside it (systems/cairn for Cairn), found on first use. Plain Python: no Flask,
database or translation imports.

    from kettlewright import system
    rules = system()            # the default system
    rules.attribute_keys        # ('strength', 'dexterity', 'willpower') in Cairn
    rules.save_succeeds(7, 12)  # True
"""
from kettlewright.core import Condition, GameSystem, Inventory, Stat
from kettlewright.registry import SYSTEMS, default_key, load, register, set_default, system, system_or_default

__all__ = ['Condition', 'GameSystem', 'Inventory', 'Stat', 'SYSTEMS', 'default_key', 'load', 'register',
           'set_default', 'system', 'system_or_default']

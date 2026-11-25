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
from kettlewright.content import Content
from kettlewright.core import (EFFECTS, NO_RECOVERY, OUT_OF_PLAY, WEAK_ATTACKS, ZERO_HP, Armor, Condition, GameSystem,
                               Inventory, Stat, WardenRoll)
from kettlewright.registry import SYSTEMS, default_key, load, register, set_default, system, system_or_default

__all__ = ['Armor', 'Condition', 'Content', 'GameSystem', 'Inventory', 'Stat', 'WardenRoll',
           'EFFECTS', 'NO_RECOVERY', 'OUT_OF_PLAY', 'WEAK_ATTACKS', 'ZERO_HP',
           'SYSTEMS', 'default_key', 'load', 'register', 'set_default', 'system', 'system_or_default']

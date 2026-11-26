"""The Kettlewright engine: the game-system engine Kettlewright runs on (#487).

A game system (kettlewright.core.GameSystem) says what a character sheet holds (HP, attributes, conditions,
inventory) and the rules that read it (saves, armor, slots, when HP drops to zero). The app asks the engine
for these instead of writing a system's rules into each page. The engine's core is system-agnostic: the systems
themselves live in packages outside it (system/cairn for Cairn), and an instance plays the one GAME_SYSTEM names.
Plain Python: no Flask, database or translation imports, except kettlewright.web (the engine in a Flask app), which
nothing here imports.
The browser half is static/kettlewright.js.

    from kettlewright import system
    rules = system()            # the instance's system (GAME_SYSTEM; Cairn by default)
    rules.attribute_keys        # ('strength', 'dexterity', 'willpower') in Cairn
    rules.save_succeeds(7, 12)  # True
"""
from kettlewright.content import Content
from kettlewright.core import (EFFECTS, NO_RECOVERY, OUT_OF_PLAY, WEAK_ATTACKS, ZERO_HP, Armor, Condition, GameSystem,
                               Inventory, Stat, WardenRoll)
from kettlewright.registry import UnknownGameSystem, available, configured_key, load, register, system, use_system

__all__ = ['Armor', 'Condition', 'Content', 'GameSystem', 'Inventory', 'Stat', 'WardenRoll',
           'EFFECTS', 'NO_RECOVERY', 'OUT_OF_PLAY', 'WEAK_ATTACKS', 'ZERO_HP',
           'UnknownGameSystem', 'available', 'configured_key', 'load', 'register', 'system', 'use_system']

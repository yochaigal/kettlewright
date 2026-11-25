"""Cairn's game system: its stats, conditions, inventory and rules, as data the engine reads."""
from dataclasses import dataclass, field
from pathlib import Path

from kettlewright.core import (NO_RECOVERY, OUT_OF_PLAY, WEAK_ATTACKS, ZERO_HP, Armor, Condition, GameSystem,
                               Inventory, Stat, WardenRoll)
from systems.cairn import items
from systems.cairn.content import TABLES
from systems.cairn.items import N_


@dataclass(frozen=True)
class Cairn(GameSystem):
    key: str = 'cairn'
    name: str = 'Cairn'
    # A new character rolls 3d6 for each attribute and 1d6 for HP. Saves roll a d20 under the attribute.
    hit_points: Stat = Stat('hp', N_('HP'), N_('Hit Protection'), roll=(1, 6))
    attributes: tuple = (
        Stat('strength', N_('STR'), N_('Strength'), save=True, roll=(3, 6)),
        Stat('dexterity', N_('DEX'), N_('Dexterity'), save=True, roll=(3, 6)),
        Stat('willpower', N_('WIL'), N_('Willpower'), save=True, roll=(3, 6)),
    )
    # Deprived: rest restores nothing. Panicked: 0 HP, and attacks roll a d4. Dead: out of play.
    conditions: tuple = (
        Condition('deprived', N_('Deprived'), frozenset({NO_RECOVERY})),
        Condition('panicked', N_('Panicked'), frozenset({ZERO_HP, WEAK_ATTACKS})),
        Condition('dead', N_('Dead'), frozenset({OUT_OF_PLAY})),
    )
    # Ten slots, and a full inventory means 0 HP. "A bag of coins worth less than 100gp is petty": from 100gp
    # it takes one slot of the main inventory, however much there is (#507).
    inventory: Inventory = field(default_factory=lambda: Inventory(
        main_slots=10, sizes=items.SIZES, gold_slot_from=100, full_means_zero_hp=True))
    armor: Armor = field(default_factory=lambda: Armor(
        tags=items.ARMOR_TAGS, maximum=items.ARMOR_MAX, needs_activating=items.NEEDS_ACTIVATING))
    save_die: int = 20
    weak_die: int = 4
    item_tag_groups: tuple = items.TAG_GROUPS
    item_tags: tuple = items.TAGS
    fatigue: str = items.FATIGUE
    sheet_sections: tuple = (('description', N_('Description')), ('traits', N_('Traits')), ('bonds', N_('Bonds')),
                             ('omens', N_('Omens')), ('scars', N_('Scars')), ('notes', N_('Notes')))
    # The Warden's rolls: the Reaction Roll (2d6) and the Die of Fate (d6).
    warden_rolls: tuple = (
        WardenRoll('reaction', N_('Reaction Roll'), (6, 6), '2d6',
                   ((2, N_('Hostile')), (5, N_('Wary')), (8, N_('Curious')), (11, N_('Kind')), (12, N_('Helpful')))),
        WardenRoll('fate', N_('Die of Fate'), (6,), 'd6'),
    )
    home: str = str(Path(__file__).parent)
    tables: dict = field(default_factory=lambda: dict(TABLES))


CAIRN = Cairn()

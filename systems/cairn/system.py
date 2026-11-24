"""Cairn's game system: its stats, conditions, inventory and the rules that read them."""
from dataclasses import dataclass, field

from kettlewright.core import Condition, GameSystem, Inventory, Stat
from systems.cairn import items
from systems.cairn.content import CONTENT
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
    conditions: tuple = (
        Condition('deprived', N_('Deprived')),
        Condition('panicked', N_('Panicked')),
        Condition('dead', N_('Dead')),
    )
    # Ten slots; "a bag of coins worth less than 100gp is petty", and from 100gp it takes one slot of the
    # main inventory, however much there is (#507).
    inventory: Inventory = field(default_factory=lambda: Inventory(main_slots=10, sizes=items.SIZES, gold_slot_from=100))
    armor_max: int = items.ARMOR_MAX
    save_die: int = 20
    content: dict = field(default_factory=lambda: dict(CONTENT))
    item_tags: tuple = items.TAGS
    fatigue: str = items.FATIGUE
    sheet_sections: tuple = (('description', N_('Description')), ('traits', N_('Traits')), ('bonds', N_('Bonds')),
                             ('omens', N_('Omens')), ('scars', N_('Scars')), ('notes', N_('Notes')))

    def item_armor(self, item):
        return items.item_armor(item)

    def can_recover(self, conditions):
        """Deprived characters recover nothing from rest."""
        return 'deprived' not in conditions

    def effective_hp(self, hp, occupied_main_slots, conditions):
        """A character with a full inventory (ten slots or more) or Panicked has 0 HP."""
        if occupied_main_slots >= self.inventory.main_slots or 'panicked' in conditions:
            return 0
        return hp


CAIRN = Cairn()

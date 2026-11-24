"""The building blocks of a game system: its stats, conditions, inventory and the rules that use them.

Plain Python, with no Flask, database or translation import, so a system can be read, tested and reused
on its own. Labels are English msgids: the app translates them where it shows them.
"""
import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Stat:
    """A number with a current and a maximum value on the sheet, like HP or an attribute.

    key is the sheet's field (and key + '_max' its maximum); abbr is its short label (e.g. 'STR'); save is
    whether it can be rolled against as a save; roll is the dice for a new character, (count, faces).
    """
    key: str
    abbr: str
    name: str
    save: bool = False
    roll: tuple | None = None

    @property
    def dice(self):
        """The creation dice as written on a sheet: '3d6', or 'd6' for one die."""
        if not self.roll:
            return ''
        count, faces = self.roll
        return f"{count if count > 1 else ''}d{faces}"


@dataclass(frozen=True)
class Condition:
    """An on/off state of a character, like Deprived."""
    key: str
    label: str


@dataclass(frozen=True)
class Inventory:
    """How a character carries things: one main inventory of slots, and how much room an item takes."""
    main_slots: int = 10
    # Item tags that change an item's size: a tag of size 0 takes no slot.
    sizes: tuple = ()
    # Coins worth at least this much take a slot of the main inventory (None: coins never do).
    gold_slot_from: int | None = None

    def item_size(self, item):
        tags = item.get('tags') or []
        for tag, size in self.sizes:
            if tag in tags:
                return size
        return 1

    def coins_take_a_slot(self, gold):
        return self.gold_slot_from is not None and (gold or 0) >= self.gold_slot_from

    def occupied_main_slots(self, items, gold=0):
        """Slots used in the main inventory (location 0), coins included."""
        return (1 if self.coins_take_a_slot(gold) else 0) + sum(
            self.item_size(item) for item in items if item.get('location') == 0)

    def main_capacity(self, containers):
        """The main inventory's size: its container's slots, or the system's default."""
        for container in containers:
            if container['id'] == 0:
                return int(container['slots'])
        return self.main_slots

    def default_containers(self):
        return [{'name': 'Main', 'slots': self.main_slots, 'id': 0}]


@dataclass(frozen=True)
class GameSystem:
    """A game system: what a character sheet holds and the rules that read it.

    A system subclasses this and overrides the rules that differ (how a save is rolled, what armor an
    item gives, when HP drops to zero). The defaults are the plainest reading of each rule.
    """
    key: str
    name: str
    hit_points: Stat
    attributes: tuple = ()
    conditions: tuple = ()
    inventory: Inventory = field(default_factory=Inventory)
    armor_max: int | None = None
    save_die: int = 20
    # The system's tables for character creation, by name: a path under the app's static/json folder.
    content: dict = field(default_factory=dict)
    # The item vocabulary: the tags an item can carry ('bulky', 'd6', '1 Armor'...).
    item_tags: tuple = ()
    # The sheet's text sections, in order, as (field, label): ('bonds', 'Bonds')...
    sheet_sections: tuple = ()
    # The name of the item that marks Fatigue in an inventory (it takes a slot), or None without Fatigue.
    fatigue: str | None = None

    # Stats, in the order the sheet shows them.

    @property
    def attribute_keys(self):
        return tuple(attribute.key for attribute in self.attributes)

    @property
    def stats(self):
        """HP, then the attributes."""
        return (self.hit_points, *self.attributes)

    @property
    def sheet_stats(self):
        """The attributes, then HP: the order of the printed character sheet and its exports."""
        return (*self.attributes, self.hit_points)

    @property
    def stat_keys(self):
        return tuple(stat.key for stat in self.stats)

    @property
    def save_keys(self):
        return tuple(attribute.key for attribute in self.attributes if attribute.save)

    @property
    def condition_keys(self):
        return tuple(condition.key for condition in self.conditions)

    def stat(self, key):
        return next((stat for stat in self.stats if stat.key == key), None)

    def abbr(self, key):
        """'strength' -> 'STR'."""
        return self.stat(key).abbr

    # Character creation.

    def creation_dice(self, key):
        """(count, faces) to roll this stat for a new character."""
        return self.stat(key).roll

    def roll_stat(self, key, rng=random):
        count, faces = self.creation_dice(key)
        return sum(rng.randint(1, faces) for _ in range(count))

    def content_path(self, name):
        """Where the system's table of this name lives, under static/json (e.g. 'traits.json')."""
        return self.content[name]

    # Rules.

    def save_succeeds(self, roll, score):
        """Roll under: a save succeeds when the die is at most the stat's current value."""
        return roll <= score

    def item_armor(self, item):
        return 0

    def armor_value(self, items, base=0):
        """Armor from the items (plus a creature's own, base), up to the system's maximum."""
        total = (base or 0) + sum(self.item_armor(item) for item in items)
        return total if self.armor_max is None else min(self.armor_max, total)

    def can_recover(self, conditions):
        """Whether rest restores HP for a character with these conditions; by default, always."""
        return True

    def effective_hp(self, hp, occupied_main_slots, conditions):
        """The HP that counts right now; by default, the sheet's."""
        return hp

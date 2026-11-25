"""The building blocks of a game system: what a character sheet holds, and the rules that read it.

A system is declared as data (its stats, conditions and their effects, inventory, armor, saves, item tags and
Warden rolls), and the engine applies the same generic rules to that data on the server (here) and in the
browser (static/kettlewright.js, from GameSystem.manifest()). A system with a rule the data can't say
overrides the method here and, for pages, registers the same rule in JavaScript (see docs/game-systems.md).

Plain Python, with no Flask, database or translation import, so a system can be read, tested and reused
on its own. Labels are English msgids: the app translates them where it shows them.
"""
import random
from dataclasses import dataclass, field
from pathlib import Path

from kettlewright.content import Content

# What an active condition does (Condition.effects). Generic, so the server and the browser can apply them.
ZERO_HP = 'zero_hp'            # HP counts as 0 while it lasts (Cairn: Panicked).
NO_RECOVERY = 'no_recovery'    # Rest restores nothing (Cairn: Deprived).
WEAK_ATTACKS = 'weak_attacks'  # Attacks roll the system's weak die instead of the weapon's (Cairn: Panicked, d4).
OUT_OF_PLAY = 'out_of_play'    # The character no longer acts: no rest, no camp (Cairn: Dead).
EFFECTS = (ZERO_HP, NO_RECOVERY, WEAK_ATTACKS, OUT_OF_PLAY)


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
    """An on/off state of a character, like Deprived, and what it does while active (EFFECTS)."""
    key: str
    label: str
    effects: frozenset = frozenset()


@dataclass(frozen=True)
class Inventory:
    """How a character carries things: one main inventory of slots, and how much room an item takes."""
    main_slots: int = 10
    # Item tags that change an item's size, in order of precedence: a tag of size 0 takes no slot.
    sizes: tuple = ()
    # Coins worth at least this much take a slot of the main inventory (None: coins never do).
    gold_slot_from: int | None = None
    # Whether a full main inventory makes HP count as 0.
    full_means_zero_hp: bool = False

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
class Armor:
    """Armor from items carried in the main inventory: the values of their armor tags, up to a maximum.

    Items named in needs_activating give armor only once activated (their armor_active flag); any other armor
    item counts unless switched off the same way.
    """
    tags: tuple = ()               # (('1 Armor', 1), ...)
    maximum: int | None = None
    needs_activating: tuple = ()   # Item names: ('Sloth-Tarp',) in Cairn.

    def item_armor(self, item):
        active = item.get('armor_active', item.get('name') not in self.needs_activating)
        if not active or item.get('location') != 0:
            return 0
        tags = item.get('tags') or []
        return sum(value for tag, value in self.tags if tag in tags)


@dataclass(frozen=True)
class WardenRoll:
    """A roll the Warden makes from the system's rules, like Cairn's Reaction Roll.

    dice: the faces of each die, e.g. (6, 6); notation: how the rules write it ('2d6'); outcomes: the total's
    meaning, as (highest total, label) in ascending order (empty: the total alone).
    """
    key: str
    label: str
    dice: tuple
    notation: str = ''
    outcomes: tuple = ()

    def outcome(self, total):
        return next((label for highest, label in self.outcomes if total <= highest), None)


@dataclass(frozen=True)
class GameSystem:
    """A game system: what a character sheet holds and the rules that read it.

    A system subclasses this and fills in its data. The rules below read that data; a system overrides one
    only when its rule can't be said as data. The defaults are the plainest reading of each rule.
    """
    key: str
    name: str
    hit_points: Stat
    attributes: tuple = ()
    conditions: tuple = ()
    inventory: Inventory = field(default_factory=Inventory)
    armor: Armor = field(default_factory=Armor)
    save_die: int = 20
    save_under: bool = True    # A save succeeds rolling at most the stat (False: at least the stat).
    weak_die: int | None = None  # The die attacks roll under WEAK_ATTACKS (4 in Cairn).
    # The item vocabulary: groups of tags of which an item has at most one ('bulky' or 'petty'...), then the rest.
    item_tag_groups: tuple = ()
    item_tags: tuple = ()
    # The sheet's text sections, in order, as (field, label): ('bonds', 'Bonds')...
    sheet_sections: tuple = ()
    # The name of the item that marks Fatigue in an inventory (it takes a slot), or None without Fatigue.
    fatigue: str | None = None
    warden_rolls: tuple = ()
    # Where the system's own files are: its tables (content/), templates (templates/) and scripts (static/).
    home: str | None = None
    # The system's tables, by name: file names under its content/ folder.
    tables: dict = field(default_factory=dict)
    # How a character of this system is created: (endpoint, label) of each way, the first one the default.
    creation: tuple = ()

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

    def condition(self, key):
        return next((condition for condition in self.conditions if condition.key == key), None)

    def conditions_with(self, effect):
        """The keys of the conditions that have this effect: ('panicked',) for ZERO_HP in Cairn."""
        return tuple(condition.key for condition in self.conditions if effect in condition.effects)

    def has_effect(self, conditions, effect):
        """Whether any of these active conditions (keys) has this effect."""
        return any(key in conditions for key in self.conditions_with(effect))

    # Character creation.

    def creation_dice(self, key):
        """(count, faces) to roll this stat for a new character."""
        return self.stat(key).roll

    def roll_stat(self, key, rng=random):
        count, faces = self.creation_dice(key)
        return sum(rng.randint(1, faces) for _ in range(count))

    @property
    def content(self):
        """The system's tables: content.load('traits'), content.path('traits')."""
        return Content(Path(self.home) / 'content' if self.home else None, self.tables)

    def content_path(self, name):
        """The file of the system's table of this name."""
        return self.content.path(name)

    # Rules.

    @property
    def armor_max(self):
        return self.armor.maximum

    def save_succeeds(self, roll, score):
        """Roll under (or over, with save_under False) the stat's current value."""
        return roll <= score if self.save_under else roll >= score

    def item_armor(self, item):
        return self.armor.item_armor(item)

    def armor_value(self, items, base=0):
        """Armor from the items (plus a creature's own, base), up to the system's maximum."""
        total = (base or 0) + sum(self.item_armor(item) for item in items)
        return total if self.armor.maximum is None else min(self.armor.maximum, total)

    def can_recover(self, conditions):
        """Whether rest restores HP for a character with these active conditions."""
        return not self.has_effect(conditions, NO_RECOVERY)

    def effective_hp(self, hp, occupied_main_slots, conditions):
        """The HP that counts right now: 0 with a full inventory (if the system says so) or a ZERO_HP condition."""
        if self.inventory.full_means_zero_hp and occupied_main_slots >= self.inventory.main_slots:
            return 0
        return 0 if self.has_effect(conditions, ZERO_HP) else hp

    def attack_die(self, conditions):
        """The die an attack rolls instead of the weapon's under these conditions, or None for the weapon's."""
        return self.weak_die if self.weak_die and self.has_effect(conditions, WEAK_ATTACKS) else None

    def warden_roll(self, key):
        return next((roll for roll in self.warden_rolls if roll.key == key), None)

    # The browser's copy.

    def manifest(self):
        """The system as data for the browser engine (static/kettlewright.js): everything its rules read.

        Labels are the English msgids; the web layer translates them (kettlewright.web)."""
        stat = lambda s, **extra: dict(key=s.key, abbr=s.abbr, name=s.name, **extra)
        return dict(
            key=self.key, name=self.name,
            hp=stat(self.hit_points),
            attributes=[stat(s, save=s.save) for s in self.attributes],
            conditions=[dict(key=c.key, label=c.label, effects=sorted(c.effects)) for c in self.conditions],
            inventory=dict(main_slots=self.inventory.main_slots, sizes=[list(s) for s in self.inventory.sizes],
                           gold_slot_from=self.inventory.gold_slot_from,
                           full_means_zero_hp=self.inventory.full_means_zero_hp),
            armor=dict(tags=[list(t) for t in self.armor.tags], maximum=self.armor.maximum,
                       needs_activating=list(self.armor.needs_activating)),
            save=dict(die=self.save_die, under=self.save_under),
            weak_die=self.weak_die,
            item_tag_groups=[list(group) for group in self.item_tag_groups],
            item_tags=list(self.item_tags),
            fatigue=self.fatigue,
        )

"""Cairn's item vocabulary: what an item's tags mean."""


def N_(text):
    """Marks a label for translation extraction (Babel's N_ keyword); the app translates it where shown."""
    return text


# Fatigue is an item of this name that takes a slot until the character makes camp.
FATIGUE = 'Fatigue'

# A petty item takes no slot and a bulky one two (petty wins over bulky); any other item takes one.
SIZES = (('petty', 0), ('bulky', 2))

# Armor an item gives while carried in the main inventory: the sum of its armor tags, at most 3. A Sloth-Tarp
# gives its armor only once activated (old ones had no flag).
ARMOR_TAGS = (('1 Armor', 1), ('2 Armor', 2), ('3 Armor', 3))
ARMOR_MAX = 3
NEEDS_ACTIVATING = ('Sloth-Tarp',)

# The tags an item can carry. An item has at most one of each group (the item editor toggles within a group).
TAG_GROUPS = (
    ('bulky', 'petty'),
    ('uses', 'charges'),
    ('d4', 'd6', 'd8', 'd10', 'd12'),
    tuple(tag for tag, _ in ARMOR_TAGS),
)
TAGS = ('bulky', 'petty', 'uses', 'charges', 'blast', 'bonus defense', 'd4', 'd6', 'd8', 'd10', 'd12',
        *(tag for tag, _ in ARMOR_TAGS))

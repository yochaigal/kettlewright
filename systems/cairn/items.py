"""Cairn's item vocabulary: what an item's tags mean."""


def N_(text):
    """Marks a label for translation extraction (Babel's N_ keyword); the app translates it where shown."""
    return text


# Fatigue is an item of this name that takes a slot until the character makes camp.
FATIGUE = 'Fatigue'

# A petty item takes no slot and a bulky one two (petty wins over bulky); any other item takes one.
SIZES = (('petty', 0), ('bulky', 2))

# Armor an item gives while carried in the main inventory: the sum of its armor tags.
ARMOR_TAGS = {'1 Armor': 1, '2 Armor': 2, '3 Armor': 3}
ARMOR_MAX = 3

# Every tag an item can carry: sizes, uses and charges, effects, damage dice, armor.
TAGS = ('bulky', 'petty', 'uses', 'charges', 'blast', 'bonus defense', 'd4', 'd6', 'd8', 'd10', 'd12',
        *ARMOR_TAGS)


def item_armor(item):
    """Armor from an item carried in the main inventory (location 0). Old Sloth-Tarps also require explicit
    activation (armor_active); ordinary armor stays active."""
    active = item.get('armor_active', item.get('name') != 'Sloth-Tarp')
    if not active or item.get('location') != 0:
        return 0
    tags = item.get('tags') or []
    return sum(value for tag, value in ARMOR_TAGS.items() if tag in tags)

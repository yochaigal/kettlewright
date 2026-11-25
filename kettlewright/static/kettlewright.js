// Kettlewright's game-system engine in the browser (#487): the same rules as kettlewright/core.py, over the same
// data. Pages carry their system in <script id="game-system" type="application/json"> (kettlewright.web,
// GameSystem.manifest()); scripts import this module as '#kettlewright' and ask it instead of writing a system's
// numbers and tags themselves. It has no system of its own: without a page (tests), useSystem() gives it one, and
// with neither it plays the plainest rules (GameSystem's defaults).
//
// A system whose rule can't be said as data overrides it in Python and, for pages, here: its static/rules.js
// calls registerRules('<key>', {itemSize(item, base) {...}}), and this module loads that script before any
// module that imports it runs (top-level await).

const PLAIN = {
  key: '', name: '',
  hp: {key: 'hp', abbr: 'HP', label: 'HP'},
  attributes: [],
  conditions: [],
  inventory: {main_slots: 10, sizes: [], gold_slot_from: null, full_means_zero_hp: false},
  armor: {tags: [], maximum: null, needs_activating: []},
  save: {die: 20, under: true},
  weak_die: null,
  item_tag_groups: [],
  item_tags: [],
  fatigue: null,
};

// What an active condition does (kettlewright/core.py EFFECTS).
export const ZERO_HP = 'zero_hp';
export const NO_RECOVERY = 'no_recovery';
export const WEAK_ATTACKS = 'weak_attacks';
export const OUT_OF_PLAY = 'out_of_play';

let explicit = null;
let cached = null, cachedText = null;
const overrides = {};

// The page's system (or the one useSystem() gave): the manifest, as data.
export function gameSystem() {
  if (explicit) return explicit;
  const text = globalThis.document?.getElementById?.('game-system')?.textContent;
  if (!text) return PLAIN;
  if (text !== cachedText) {
    try {cached = {...PLAIN, ...JSON.parse(text)}; cachedText = text;} catch (_) {return PLAIN;}
  }
  return cached;
}

// Play this system instead of the page's (tests; null goes back to the page's).
export function useSystem(manifest) {
  explicit = manifest ? {...PLAIN, ...manifest} : null;
}

// A system's rules that its data can't say: {ruleName(...args, base) {...}}, base being the generic rule.
export function registerRules(key, rules) {
  overrides[key] = {...overrides[key], ...rules};
}

function rule(name, generic) {
  return (...args) => {
    const own = overrides[gameSystem().key]?.[name];
    return own ? own(...args, generic) : generic(...args);
  };
}

// Stats: HP, then the attributes.

export function stats() {
  const system = gameSystem();
  return [system.hp, ...system.attributes];
}

export function statKeys() {
  return stats().map(stat => stat.key);
}

export function attributeKeys() {
  return gameSystem().attributes.map(attribute => attribute.key);
}

export function saveKeys() {
  return gameSystem().attributes.filter(attribute => attribute.save).map(attribute => attribute.key);
}

// The English abbreviation of a stat ('strength' -> 'STR'), or the key itself if the system has no such stat.
export function statAbbr(key) {
  return stats().find(stat => stat.key === key)?.abbr ?? key;
}

// Conditions.

export function conditionKeys() {
  return gameSystem().conditions.map(condition => condition.key);
}

export function conditionsWith(effect) {
  return gameSystem().conditions.filter(condition => condition.effects?.includes(effect)).map(condition => condition.key);
}

// Whether any of these active conditions (keys, or an object of key: true) has this effect.
export function hasEffect(conditions, effect) {
  const active = Array.isArray(conditions) ? conditions : Object.keys(conditions || {}).filter(key => conditions[key]);
  return conditionsWith(effect).some(key => active.includes(key));
}

// The inventory.

export function mainSlots() {
  return gameSystem().inventory.main_slots;
}

export function defaultContainers() {
  return [{name: 'Main', slots: mainSlots(), id: 0}];
}

// The tags that change an item's size ('petty', 'bulky' in Cairn), in order of precedence.
export function sizeTags() {
  return gameSystem().inventory.sizes.map(([tag]) => tag);
}

export const itemSize = rule('itemSize', (item) => {
  const tags = item?.tags || [];
  const size = gameSystem().inventory.sizes.find(([tag]) => tags.includes(tag));
  return size ? size[1] : 1;
});

export function coinsTakeASlot(gold) {
  const from = gameSystem().inventory.gold_slot_from;
  return from != null && (Number(gold) || 0) >= from;
}

// Slots the items in a container (the main inventory, 0, by default) take; items without tags take none, as the
// sheet has always counted them.
export function slotsUsed(items, containerId = 0) {
  return (items || []).filter(item => item.location === containerId && item.tags)
    .reduce((total, item) => total + itemSize(item), 0);
}

// The main inventory's slots in use, coins included (Inventory.occupied_main_slots).
export function occupiedMainSlots(items, gold = 0) {
  return (coinsTakeASlot(gold) ? 1 : 0) + (items || []).filter(item => item.location === 0)
    .reduce((total, item) => total + itemSize(item), 0);
}

export function fatigueName() {
  return gameSystem().fatigue;
}

export function isFatigue(item) {
  return Boolean(fatigueName()) && item?.name === fatigueName();
}

export function fatigueItem(location = 0) {
  return fatigueName() ? {name: fatigueName(), location, tags: []} : null;
}

// The item vocabulary: groups of tags of which an item has at most one, and every tag.

export function itemTagGroups() {
  return gameSystem().item_tag_groups;
}

export function itemTags() {
  return gameSystem().item_tags;
}

// Armor.

export function armorTags() {
  return gameSystem().armor.tags.map(([tag]) => tag);
}

export const itemArmor = rule('itemArmor', (item) => {
  const armor = gameSystem().armor;
  const active = item?.armor_active ?? !armor.needs_activating.includes(item?.name);
  if (!active || item?.location !== 0) return 0;
  const tags = item.tags || [];
  return armor.tags.filter(([tag]) => tags.includes(tag)).reduce((total, [, value]) => total + value, 0);
});

export function armorValue(items, base = 0) {
  const total = (Number(base) || 0) + (items || []).reduce((sum, item) => sum + itemArmor(item), 0);
  const maximum = gameSystem().armor.maximum;
  return maximum == null ? total : Math.min(maximum, total);
}

// Rules.

export function saveDie() {
  return gameSystem().save.die;
}

export const saveSucceeds = rule('saveSucceeds', (roll, score) =>
  gameSystem().save.under ? roll <= score : roll >= score);

export const effectiveHp = rule('effectiveHp', (hp, occupied, conditions) => {
  const {inventory} = gameSystem();
  if (inventory.full_means_zero_hp && occupied >= inventory.main_slots) return 0;
  return hasEffect(conditions, ZERO_HP) ? 0 : hp;
});

export const canRecover = rule('canRecover', (conditions) => !hasEffect(conditions, NO_RECOVERY));

// The die an attack rolls instead of the weapon's under these conditions, or null for the weapon's.
export const attackDie = rule('attackDie', (conditions) => {
  const die = gameSystem().weak_die;
  return die && hasEffect(conditions, WEAK_ATTACKS) ? die : null;
});

// A system's own rules, loaded before any module that imports this one runs.
const script = gameSystem().script;
if (script) {
  try {await import(script);} catch (error) {console.error('Could not load the game system\'s rules', error);}
}

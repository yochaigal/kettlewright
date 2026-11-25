// The browser engine (kettlewright/static/kettlewright.js, #487): the same rules as kettlewright/core.py, over the
// page's system. test_kettlewright.py runs the same cases in Python, so both halves agree.
import test from 'node:test';
import assert from 'node:assert/strict';
import {CAIRN} from './support/cairn.mjs';
import {
  armorTags, armorValue, attackDie, canRecover, coinsTakeASlot, conditionKeys, conditionsWith, defaultContainers,
  effectiveHp, fatigueItem, gameSystem, hasEffect, isFatigue, itemArmor, itemSize, itemTagGroups, mainSlots,
  occupiedMainSlots, registerRules, saveDie, saveKeys, saveSucceeds, sizeTags, slotsUsed, statAbbr, statKeys, stats,
  useSystem, ZERO_HP,
} from '#kettlewright';

const item = (tags = [], extra = {}) => ({tags, location: 0, ...extra});

function withSystem(manifest, fn) {
  useSystem(manifest);
  try {fn();} finally {useSystem(CAIRN);}
}

test('Cairn, as the server sends it: stats, saves and conditions', () => {
  assert.equal(gameSystem().key, 'cairn');
  assert.deepEqual(statKeys(), ['hp', 'strength', 'dexterity', 'willpower']);
  assert.deepEqual(saveKeys(), ['strength', 'dexterity', 'willpower']);
  assert.equal(statAbbr('dexterity'), 'DEX');
  assert.equal(statAbbr('armor'), 'armor');
  assert.deepEqual(conditionKeys(), ['deprived', 'panicked', 'dead']);
  assert.deepEqual(conditionsWith(ZERO_HP), ['panicked']);
  assert.equal(saveDie(), 20);
  assert.ok(saveSucceeds(12, 12) && !saveSucceeds(13, 12));
});

test("Cairn's slots: petty takes none, bulky two, coins from 100gp one", () => {
  assert.deepEqual([[], ['bulky'], ['petty'], ['petty', 'bulky']].map(tags => itemSize(item(tags))), [1, 2, 0, 0]);
  assert.deepEqual(sizeTags(), ['petty', 'bulky']);
  const carried = [item(), item(['bulky']), item(['petty']), item([], {location: 1})];
  assert.equal(occupiedMainSlots(carried), 3);
  assert.deepEqual([null, 99, 100, 5000].map(gold => occupiedMainSlots(carried, gold)), [3, 3, 4, 4]);
  assert.ok(coinsTakeASlot(100) && !coinsTakeASlot(99));
  assert.equal(slotsUsed(carried, 1), 1);
  assert.equal(slotsUsed([{location: 0}], 0), 0);  // No tags: the sheet never counted it.
  assert.equal(mainSlots(), 10);
  assert.deepEqual(defaultContainers(), [{name: 'Main', slots: 10, id: 0}]);
  assert.ok(isFatigue({name: 'Fatigue'}) && !isFatigue({name: 'Rope'}));
  assert.deepEqual(fatigueItem(), {name: 'Fatigue', location: 0, tags: []});
  assert.deepEqual(itemTagGroups()[0], ['bulky', 'petty']);
});

test("Cairn's armor and HP: at most 3 armor, 0 HP when full or Panicked, no rest while Deprived, d4 attacks", () => {
  assert.deepEqual(armorTags(), ['1 Armor', '2 Armor', '3 Armor']);
  assert.equal(armorValue([item(['1 Armor']), item(['2 Armor'])]), 3);
  assert.equal(armorValue([item(['2 Armor'], {location: 1})]), 0);
  assert.equal(itemArmor(item(['1 Armor'], {name: 'Sloth-Tarp'})), 0);
  assert.equal(itemArmor(item(['1 Armor'], {name: 'Sloth-Tarp', armor_active: true})), 1);
  assert.equal(armorValue([item(['1 Armor'])], 1), 2);
  assert.deepEqual([9, 10, 12].map(slots => effectiveHp(4, slots, [])), [4, 0, 0]);
  assert.equal(effectiveHp(4, 0, ['panicked']), 0);
  assert.equal(effectiveHp(4, 0, {deprived: true, panicked: false}), 4);
  assert.ok(!canRecover(['deprived']) && canRecover(['panicked']));
  assert.equal(attackDie(['panicked']), 4);
  assert.equal(attackDie([]), null);
  assert.ok(hasEffect({panicked: true}, ZERO_HP));
});

test('without a system the engine plays the plainest rules, and has no system of its own', () => {
  withSystem(null, () => {
    useSystem(null);
    assert.equal(gameSystem().key, '');
    assert.deepEqual(statKeys(), ['hp']);
    assert.equal(itemSize(item(['bulky'])), 1);
    assert.equal(armorValue([item(['1 Armor'])]), 0);
    assert.equal(effectiveHp(5, 99, ['anything']), 5);
    assert.equal(attackDie(['anything']), null);
    assert.equal(fatigueItem(), null);
  });
});

test('the page says which system it plays, with its own stats and labels', () => {
  const original = globalThis.document;
  const lucky = {key: 'lucky', hp: {key: 'hp', abbr: 'HP', label: 'PG'},
    attributes: [{key: 'strength', abbr: 'STR', label: 'FUE', save: true}, {key: 'luck', abbr: 'LCK', label: 'SUE', save: true}],
    conditions: [], save: {die: 20, under: false}};
  let text = JSON.stringify(lucky);
  globalThis.document = {getElementById: id => id === 'game-system' ? {textContent: text} : null};
  useSystem(null);
  try {
    assert.equal(gameSystem().key, 'lucky');
    assert.deepEqual(statKeys(), ['hp', 'strength', 'luck']);
    assert.deepEqual(stats().map(stat => stat.label), ['PG', 'FUE', 'SUE']);
    assert.ok(saveSucceeds(15, 12) && !saveSucceeds(3, 12));  // Lucky's saves roll over.
    assert.equal(mainSlots(), 10);  // What the page doesn't say is the plainest rule.
    text = '{not json';  // A broken block: the plainest rules, not another system's.
    assert.equal(gameSystem().key, '');
  } finally {
    globalThis.document = original;
    useSystem(CAIRN);
  }
});

test("a system's own rule in JavaScript, for what its data can't say", () => {
  withSystem({...CAIRN, key: 'heavy'}, () => {
    registerRules('heavy', {itemSize: (item, base) => (item.tags.includes('heavy') ? 3 : base(item))});
    assert.equal(itemSize(item(['heavy'])), 3);
    assert.equal(itemSize(item(['bulky'])), 2);  // The rest is the generic rule over its data.
    assert.equal(occupiedMainSlots([item(['heavy']), item()]), 4);
  });
  assert.equal(itemSize(item(['heavy'])), 1);  // Only that system's.
});

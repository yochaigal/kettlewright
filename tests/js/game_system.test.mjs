import test from 'node:test';
import assert from 'node:assert/strict';
import {gameSystem, stats, statKeys, statAbbr} from '../../app/static/src/js/game_system.js';

test('without a page the game system is Cairn (#487)', () => {
  assert.equal(gameSystem().key, 'cairn');
  assert.deepEqual(statKeys(), ['hp', 'strength', 'dexterity', 'willpower']);
  assert.equal(statAbbr('dexterity'), 'DEX');
  assert.equal(statAbbr('armor'), 'armor');
  assert.deepEqual(gameSystem().attributes.filter(stat => stat.save).map(stat => stat.key), ['strength', 'dexterity', 'willpower']);
});

test('the page says which system it plays, with its own stats and labels', () => {
  const original = globalThis.document;
  const lucky = {key: 'lucky', hp: {key: 'hp', abbr: 'HP', label: 'PG'},
    attributes: [{key: 'strength', abbr: 'STR', label: 'FUE', save: true}, {key: 'luck', abbr: 'LCK', label: 'SUE', save: true}],
    conditions: []};
  let text = JSON.stringify(lucky);
  globalThis.document = {getElementById: id => id === 'game-system' ? {textContent: text} : null};
  try {
    assert.equal(gameSystem().key, 'lucky');
    assert.deepEqual(statKeys(), ['hp', 'strength', 'luck']);
    assert.deepEqual(stats().map(stat => stat.label), ['PG', 'FUE', 'SUE']);
    assert.equal(statAbbr('luck'), 'LCK');
    text = '{not json';  // A broken block falls back to Cairn.
    assert.equal(gameSystem().key, 'cairn');
  } finally {
    globalThis.document = original;
  }
});

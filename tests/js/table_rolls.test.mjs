import test from 'node:test';
import assert from 'node:assert/strict';
import {tableDice, parseKey, rollDice, diceLabel} from '../../app/static/src/js/table_rolls.js';

const rows = (...lines) => lines.map(line => line.split('|').map(cell => cell.trim()));

test('a die in the header names the roll; each numbered row is one result', () => {
  const info = tableDice(rows('d4|Encounters|Signs', '1|Marius|…', '2|Mossling|…', '3|Infected Mossling|…', '4|Isobel|…'));
  assert.deepEqual(info.dice, {count: 1, sides: 4});
  assert.deepEqual(info.entries.map(entry => entry.index), [1, 2, 3, 4]);
  assert.equal(info.sideways, false);
  assert.equal(diceLabel(tableDice(rows('2d6|Result', '2-6|Low', '7|Mid', '8-12|High')).dice), '2d6');
});

test('a table without a die header reads the die from its numbers, first row included', () => {
  // The book's Dungeon Events table: its first row is the header.
  const info = tableDice(rows('**1**|Encounter|…', '**2**|Sign|…', '3|Environment|…', '4|Loss|…', '5|Exhaustion|…', '6|Quiet|…'));
  assert.deepEqual(info.dice, {count: 1, sides: 6});
  assert.deepEqual(info.entries.map(entry => entry.index), [0, 1, 2, 3, 4, 5]);
  assert.deepEqual(tableDice(rows('Roll|Item', '1-3|Rope', '4-6|Torch')).dice, {count: 1, sides: 6});
});

test('the Reactions table, laid out sideways, rolls 2d6 across its columns', () => {
  const info = tableDice(rows('2|3-5|6-8|9-11|12', 'Hostile|Wary|Curious|Kind|Helpful'));
  assert.deepEqual(info.dice, {count: 2, sides: 6});
  assert.equal(info.sideways, true);
  assert.deepEqual(info.entries.map(({min, max}) => [min, max]), [[2, 2], [3, 5], [6, 8], [9, 11], [12, 12]]);
});

test('tables that are not roll tables get no button', () => {
  assert.equal(tableDice(rows('Name|HP', 'Marius|9')), null);
  assert.equal(tableDice(rows('d6|Item', '1|A', '2|B', '3|C')), null);  // Gaps: 4-6 missing.
  assert.equal(tableDice(rows('d4|Item', '1|A', '2|B', '2|C', '4|D')), null);  // A repeated key.
  assert.equal(tableDice(rows('Year|Event', '1201|Founding', '1202|Fire')), null);
  assert.equal(tableDice([]), null);
});

test('keys and rolls', () => {
  assert.deepEqual(parseKey('3–5'), {min: 3, max: 5});
  assert.deepEqual(parseKey('**12**'), {min: 12, max: 12});
  assert.deepEqual(parseKey('00'), {min: 100, max: 100});
  assert.equal(parseKey('5-3'), null);
  assert.equal(rollDice({count: 2, sides: 6}, () => 0), 2);
  assert.equal(rollDice({count: 2, sides: 6}, () => 0.999), 12);
});

test('"On this page" marks the last heading scrolled past, or the first', async () => {
  const {currentHeading} = await import('../../app/static/src/js/wiki_toc.js');
  assert.equal(currentHeading([200, 900, 1600]), 0);
  assert.equal(currentHeading([-500, 40, 700]), 1);
  assert.equal(currentHeading([-2000, -1000, -10]), 2);
});

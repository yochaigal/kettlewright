import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// #470: the whiteboard's theme is set by a classic script before the first paint.
const source = readFileSync(new URL('../../app/static/src/js/maps/board_theme.js', import.meta.url), 'utf8');

function run(storage) {
  const classes = new Set();
  const body = {classList: {add: name => classes.add(name)}};
  vm.runInContext(source, vm.createContext({document: {body}, localStorage: storage}));
  return classes;
}

test('dark mode saved: the board starts dark', () => {
  assert.deepEqual([...run({getItem: key => key === 'darkMode' ? 'true' : null})], ['dark-mode']);
});

test('light, unset or blocked storage: the board stays light without errors', () => {
  assert.equal(run({getItem: () => 'false'}).size, 0);
  assert.equal(run({getItem: () => null}).size, 0);
  assert.equal(run({getItem: () => {throw new Error('blocked');}}).size, 0);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {createRollOsd} from '../../app/static/src/js/maps/board_roll_osd.js';

class Item {
  constructor(list) {this.list = list; this.classList = {add: name => {this.leaving = name === 'is-leaving';}};}
  addEventListener(name, fn) {this.click = fn;}
  remove() {const index = this.list.indexOf(this); if (index >= 0) this.list.splice(index, 1);}
}
function setup(options = {}) {
  const children = [], timers = [];
  let clock = 0;
  const container = {children, ownerDocument: {createElement: () => new Item(children)}, append: item => children.push(item),
    get firstElementChild() {return children[0];}};
  const osd = createRollOsd({container, format: (name, result) => `${name}: ${result}`, now: () => clock,
    schedule: fn => timers.push(fn), ...options});
  return {osd, children, texts: () => children.map(item => item.textContent), timers, advance(ms) {clock += ms;}};
}

test('shows other rolls straight away and drops the echo of your own', () => {
  const s = setup();
  s.osd.received('Pip rolled a 3 (d6)');
  assert.deepEqual(s.texts(), ['Pip rolled a 3 (d6)']);
  s.osd.hold();
  s.osd.release('Ada', '7 (d20)');
  s.osd.received('Ada rolled a 7 (d20)');  // The echo of your own roll.
  s.osd.own('Ada', '7 (d20)');
  assert.deepEqual(s.texts(), ['Pip rolled a 3 (d6)', 'Ada: 7 (d20)']);
  s.osd.received('Ada rolled a 7 (d20)');  // The same result again is a new roll.
  assert.equal(s.texts().length, 3);
});

test('results that arrive during your roll wait for it, so the echo is never shown first', () => {
  const s = setup();
  s.osd.hold();
  s.osd.received('Ada rolled a 7 (d20)');
  s.osd.received('Pip rolled a 2 (d4)');
  assert.deepEqual(s.texts(), []);
  s.osd.release('Ada', '7 (d20)');
  assert.deepEqual(s.texts(), ['Pip rolled a 2 (d4)']);
});

test('a failed roll expects no echo; old expectations expire', () => {
  const s = setup();
  s.osd.hold(); s.osd.release(null, undefined);
  s.osd.received('Ada rolled a 7 (d20)');
  assert.equal(s.texts().length, 1);
  s.osd.hold(); s.osd.release('Ada', '5 (d20)');
  s.advance(20000);
  s.osd.received('Ada rolled a 5 (d20)');
  assert.equal(s.texts().length, 2);
});

test('keeps at most four results, which fade out, and ignores anything but text', () => {
  const s = setup();
  for (let n = 1; n <= 6; n++) s.osd.received(`roll ${n}`);
  s.osd.received({party_id: 1}); s.osd.received('');
  assert.deepEqual(s.texts(), ['roll 3', 'roll 4', 'roll 5', 'roll 6']);
  s.timers.splice(0).forEach(fn => fn());
  assert.ok(s.children.every(item => item.leaving));
  s.timers.splice(0).forEach(fn => fn());
  assert.equal(s.children.length, 0);
});

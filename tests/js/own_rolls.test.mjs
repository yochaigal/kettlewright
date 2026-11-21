import assert from 'node:assert/strict';
import test from 'node:test';

import { ownRolls } from '../../app/static/src/js/own_rolls.js';

// A roll request that resolves when told to (the echo can arrive before or after it).
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((ok, fail) => { resolve = ok; reject = fail; });
  return {promise, resolve, reject};
};

test('the echo of this tab\'s roll is dropped, whether it arrives after or before the response', async () => {
  const shown = [];
  const show = (message) => shown.push(message);

  // After: the response first, then the party's announcement of it.
  await ownRolls.track(Promise.resolve({result: '20 (d20) · STR 11 · Failure'}));
  ownRolls.receive('Brielle rolled a 20 (d20) · STR 11 · Failure', show);
  assert.deepEqual(shown, []);

  // Before: the announcement arrives while the request is still in flight; it waits, then is dropped.
  const roll = deferred();
  const tracked = ownRolls.track(roll.promise);
  ownRolls.receive('Brielle rolled a 7 (d8) · Sword', show);
  assert.deepEqual(shown, []);
  roll.resolve({result: '7 (d8) · Sword'});
  await tracked;
  assert.deepEqual(shown, []);
});

test('other rolls are shown, also those that arrive while this tab is rolling', async () => {
  const shown = [];
  const show = (message) => shown.push(message);
  ownRolls.receive('Wren rolled a 3 (d6)', show);
  assert.deepEqual(shown, ['Wren rolled a 3 (d6)']);

  const roll = deferred();
  const tracked = ownRolls.track(roll.promise);
  ownRolls.receive('Wren rolled a 5 (d6)', show);  // Someone else, during this tab's roll: held, then shown.
  ownRolls.receive('Brielle rolled a 12 (d20)', show);
  assert.deepEqual(shown, ['Wren rolled a 3 (d6)']);
  roll.resolve({result: '12 (d20)'});
  await tracked;
  assert.deepEqual(shown, ['Wren rolled a 3 (d6)', 'Wren rolled a 5 (d6)']);
});

test('a failed roll shows whatever was held, and an echo is only dropped once', async () => {
  const shown = [];
  const show = (message) => shown.push(message);
  const roll = deferred();
  const tracked = ownRolls.track(roll.promise);
  ownRolls.receive('Wren rolled a 2 (d4)', show);
  roll.reject(new Error('offline'));
  await assert.rejects(tracked);
  assert.deepEqual(shown, ['Wren rolled a 2 (d4)']);

  await ownRolls.track(Promise.resolve({result: '4 (d6)'}));
  ownRolls.receive('Brielle rolled a 4 (d6)', show);
  ownRolls.receive('Wren rolled a 4 (d6)', show);  // The same result by someone else, after: shown.
  assert.deepEqual(shown, ['Wren rolled a 2 (d4)', 'Wren rolled a 4 (d6)']);
});

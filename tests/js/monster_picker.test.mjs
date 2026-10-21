import test from 'node:test';
import assert from 'node:assert/strict';
import {initMonsterBatchPicker} from '../../app/static/src/js/monster-picker.js';

function control(values = {}) {
  return Object.defineProperties({listeners: {}, addEventListener(event, listener) {this.listeners[event] = listener;},
    fire(event) {this.listeners[event]();}}, Object.getOwnPropertyDescriptors(values));
}

function setup() {
  const rows = ['Wolf', 'Vampire Bat'].map(name => {
    const check = {checked: false};
    const quantity = control({value: '0', get validity() {
      const n = Number(this.value);
      return {valid: this.value !== '' && Number.isInteger(n) && n >= 0 && n <= 100};
    }});
    const decrease = control(), increase = control();
    return {dataset: {name: name.toLowerCase(), key: name}, check, quantity, decrease, increase,
      querySelector(selector) {return {'[name=template]': check, '[type=number]': quantity,
        '[data-quantity-step="-1"]': decrease, '[data-quantity-step="1"]': increase}[selector];}};
  });
  const search = control({value: ''}), selectedOnly = control({checked: false});
  const total = {}, summon = {}, empty = {};
  initMonsterBatchPicker({rows, search, selectedOnly, total, summon, empty});
  return {rows, search, selectedOnly, total, summon, empty};
}

test('quantities select cards and survive search and selected-only filtering', () => {
  const {rows: [wolf, bat], search, selectedOnly, total, summon, empty} = setup();
  assert.equal(summon.disabled, true);
  assert.equal(wolf.check.checked, false);
  wolf.quantity.value = '3'; wolf.quantity.fire('input');
  assert.equal(wolf.check.checked, true);
  search.value = 'bat'; search.fire('input');
  assert.equal(wolf.hidden, true);
  assert.equal(wolf.check.checked, true);
  bat.quantity.value = '2'; bat.quantity.fire('input');
  assert.equal(total.value, '5');
  assert.equal(summon.disabled, false);
  search.value = ''; search.fire('input');
  selectedOnly.checked = true; selectedOnly.fire('change');
  wolf.quantity.value = '0'; wolf.quantity.fire('input');
  assert.equal(wolf.hidden, true);
  assert.equal(wolf.check.checked, false);
  assert.equal(bat.hidden, false);
  assert.equal(total.value, '2');
  search.value = 'missing'; search.fire('input');
  assert.equal(empty.hidden, false);
  assert.equal(total.value, '2');
});

test('quantity buttons add and remove independent instances between zero and 100', () => {
  const {rows: [wolf, bat], total} = setup();
  assert.equal(wolf.decrease.disabled, true);
  wolf.increase.fire('click');
  assert.equal(wolf.quantity.value, '1');
  assert.equal(wolf.check.checked, true);
  assert.equal(total.value, '1');
  assert.equal(wolf.decrease.disabled, false);
  assert.equal(bat.quantity.value, '0');
  wolf.decrease.fire('click');
  assert.equal(wolf.quantity.value, '0');
  assert.equal(wolf.check.checked, false);
  assert.equal(wolf.decrease.disabled, true);
  wolf.quantity.value = '99'; wolf.quantity.fire('input');
  wolf.increase.fire('click');
  assert.equal(wolf.quantity.value, '100');
  assert.equal(wolf.increase.disabled, true);
});

test('summoning requires valid whole quantities and at most 100 total instances', () => {
  const {rows: [wolf, bat], total, summon} = setup();
  for (const value of ['', '0', '-1', '1.5', '101', '1e1']) {
    wolf.quantity.value = value; wolf.quantity.fire('input');
    assert.equal(summon.disabled, true, value);
  }
  wolf.quantity.value = '100'; wolf.quantity.fire('input');
  assert.equal(summon.disabled, false);
  bat.increase.fire('click');
  assert.equal(total.value, '101');
  assert.equal(summon.disabled, true);
  bat.decrease.fire('click');
  assert.equal(total.value, '100');
  assert.equal(summon.disabled, false);
  bat.quantity.value = ''; bat.quantity.fire('input');
  assert.equal(summon.disabled, true);
});

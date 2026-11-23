import test from 'node:test';
import assert from 'node:assert/strict';
import {hideablePanel} from '../../app/static/src/js/maps/board_panels.js';

const element = () => {
  const classes = new Set(), listeners = {}, attributes = {};
  return {attributes, listeners, focused: false,
    classList: {toggle: (name, on) => (on ? classes.add(name) : classes.delete(name)), contains: name => classes.has(name)},
    setAttribute(name, value) {attributes[name] = value;}, focus() {this.focused = true;},
    addEventListener(name, fn) {listeners[name] = fn;}, removeEventListener(name) {delete listeners[name];}};
};
const memory = (values = {}) => ({values, getItem: key => values[key] ?? null, setItem(key, value) {values[key] = value;}});

test('× hides the Warden tools, puts the brush down and hands focus to the top bar button', () => {
  const panel = element(), hide = element(), toggle = element(), store = memory();
  let brushDown = 0;
  hideablePanel({panel, hide, toggle, key: 'board-tools-hidden', onHide: () => brushDown++, storage: () => store});
  assert.equal(toggle.attributes['aria-pressed'], 'true');
  hide.listeners.click();
  assert.ok(panel.classList.contains('is-user-hidden'));
  assert.equal(brushDown, 1);
  assert.ok(toggle.focused);
  assert.equal(store.values['board-tools-hidden'], 'hidden');
  toggle.listeners.click();
  assert.ok(!panel.classList.contains('is-user-hidden'));
  assert.equal(toggle.attributes['aria-pressed'], 'true');
});

test('the saved choice wins over the old minimized setting; storage that throws is ignored', () => {
  const shown = element();
  hideablePanel({panel: shown, key: 'k', legacy: 'old', storage: () => memory({k: 'shown', old: 'on'})});
  assert.ok(!shown.classList.contains('is-user-hidden'));
  const broken = element();
  hideablePanel({panel: broken, key: 'k', storage: () => ({getItem() {throw new Error('blocked');}, setItem() {throw new Error('blocked');}})});
  assert.ok(!broken.classList.contains('is-user-hidden'));
  assert.equal(hideablePanel({panel: null, key: 'k'}), null);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readCanvasUI, writeCanvasUI, applyCanvasUI, bindCanvasToggles} from '../../app/static/src/js/maps/canvas_ui.js';

const memory = (values = {}) => () => ({getItem: key => values[key] ?? null, setItem(key, value) {values[key] = value;}});
const classes = () => {const set = new Set(); return {set, toggle: (name, on) => (on ? set.add(name) : set.delete(name))};};

test('every control shows until hidden, and a broken or blocked store shows everything', () => {
  assert.deepEqual(readCanvasUI('k', memory()), {drawing: true, zoom: true, fog: true});
  assert.deepEqual(readCanvasUI('k', memory({k: '{"zoom":false}'})), {drawing: true, zoom: false, fog: true});
  assert.deepEqual(readCanvasUI('k', memory({k: 'not json'})), {drawing: true, zoom: true, fog: true});
  assert.deepEqual(readCanvasUI('k', () => {throw new Error('blocked');}), {drawing: true, zoom: true, fog: true});
  const values = {};
  writeCanvasUI('k', {drawing: false, zoom: true}, memory(values));
  assert.equal(values.k, '{"drawing":false,"zoom":true}');
});

test('hidden groups become classes the canvas styles hide', () => {
  const body = {classList: classes()};
  applyCanvasUI(body, {drawing: false, zoom: true});
  assert.deepEqual([...body.classList.set], ['hide-drawing-tools']);
  applyCanvasUI(body, {drawing: true, zoom: false});
  assert.deepEqual([...body.classList.set], ['hide-zoom']);
});

test('the whiteboard\'s toggles hide and show, pressed while shown, and remember', () => {
  const values = {}, body = {classList: classes()};
  const button = group => ({dataset: {canvasUi: group}, attributes: {}, setAttribute(name, value) {this.attributes[name] = value;},
    addEventListener(name, fn) {this.click = fn;}});
  const drawing = button('drawing'), zoom = button('zoom');
  bindCanvasToggles({buttons: [drawing, zoom], key: 'kw-board-ui', target: body, storage: memory(values)});
  assert.equal(drawing.attributes['aria-pressed'], 'true');
  drawing.click();
  assert.equal(drawing.attributes['aria-pressed'], 'false');
  assert.ok(body.classList.set.has('hide-drawing-tools'));
  assert.equal(JSON.parse(values['kw-board-ui']).drawing, false);
  drawing.click();
  assert.ok(!body.classList.set.has('hide-drawing-tools'));
});

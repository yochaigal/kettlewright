import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_fog.js', import.meta.url), 'utf8');
const {fogPoint, paintFog, applyFogOperation} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('brush coordinates stay anchored after zoom, pan, and header resize', () => {
  assert.deepEqual(fogPoint(430, 270, {left: 10, top: 50}, {zoom: {value: 2}, scrollX: 100, scrollY: -20}), [110, 130]);
  assert.deepEqual(fogPoint(110, 250, {left: 10, top: 100}, {zoom: {value: 1}, scrollX: -10, scrollY: 20}), [110, 130]);
});

test('reveal clears and cover repaints the same opaque mask at device scale', () => {
  const calls = [];
  const ctx = new Proxy({}, {get: (obj, key) => obj[key] || ((...args) => calls.push([key, ...args])),
    set(obj, key, value) {obj[key] = value; calls.push([key, value]); return true;}});
  paintFog(ctx, 400, 200, {enabled: true, base: 'covered', strokes: [
    {type: 'reveal', radius: 10, points: [[20, 30]]}, {type: 'cover', radius: 5, points: [[20, 30], [40, 30]]},
  ]}, {zoom: {value: 2}, scrollX: 3, scrollY: -4}, 2);
  assert.ok(calls.some(call => JSON.stringify(call) === JSON.stringify(['setTransform', 4, 0, 0, 4, 12, -16])));
  assert.deepEqual(calls.filter(call => call[0] === 'globalCompositeOperation').map(call => call[1]),
    ['source-over', 'destination-out', 'source-over', 'source-over']);
});

test('optimistic fog operations retain ordering and do not replay acknowledged strokes', () => {
  const base = {enabled: false, base: 'covered', strokes: [], applied: []};
  const reveal = {id: 'one', type: 'reveal', radius: 20, points: [[0, 0]]};
  const fog = [{type: 'hide_all'}, reveal].reduce(applyFogOperation, base);
  assert.equal(fog.enabled, true); assert.equal(fog.strokes.length, 1);
  assert.equal(applyFogOperation(fog, {type: 'undo'}).strokes.length, 0);
  assert.equal(applyFogOperation(fog, {type: 'reveal_all'}).base, 'clear');
  assert.equal(applyFogOperation({...fog, applied: ['one']}, reveal).strokes.length, 1);
  assert.equal(base.strokes.length, 0);
});

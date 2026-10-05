import test from 'node:test';
import assert from 'node:assert/strict';
import {previewResize} from '../../app/static/src/js/preview-resize.js';

const bounds = {left: 200, top: 180, right: 700, bottom: 580, width: 500, height: 400};
const directions = ['n', 'e', 's', 'w', 'ne', 'se', 'sw', 'nw'];

test('all edges and corners move only the grabbed sides', () => {
  for (const direction of directions) {
    const result = previewResize(bounds, direction, 40, 30, 1000, 800);
    assert.equal(result.left, bounds.left + (direction.includes('w') ? 40 : 0));
    assert.equal(result.top, bounds.top + (direction.includes('n') ? 30 : 0));
    assert.equal(result.left + result.width, bounds.right + (direction.includes('e') ? 40 : 0));
    assert.equal(result.top + result.height, bounds.bottom + (direction.includes('s') ? 30 : 0));
  }
});

test('resizing stops at the viewport and minimum size without moving opposite edges', () => {
  for (const direction of directions) {
    for (const dx of [-5000, 5000]) for (const dy of [-5000, 5000]) {
      const result = previewResize(bounds, direction, dx, dy, 1000, 800);
      assert(result.left >= 8 && result.top >= 8);
      assert(result.left + result.width <= 992 && result.top + result.height <= 792);
      assert(result.width >= 240 && result.height >= 160);
      if (!direction.includes('w')) assert.equal(result.left, bounds.left);
      if (!direction.includes('n')) assert.equal(result.top, bounds.top);
      if (!direction.includes('e')) assert.equal(result.left + result.width, bounds.right);
      if (!direction.includes('s')) assert.equal(result.top + result.height, bounds.bottom);
    }
  }
});

test('small viewports and initially constrained previews do not jump when grabbed', () => {
  for (const small of [
    {left: 8, top: 8, right: 192, bottom: 132, width: 184, height: 124},
    {left: 8, top: 90, right: 192, bottom: 132, width: 184, height: 42},
  ]) {
    for (const direction of directions) {
      assert.deepEqual(previewResize(small, direction, 0, 0, 200, 140), {
        left: small.left, top: small.top, width: small.width, height: small.height,
      });
    }
  }
});

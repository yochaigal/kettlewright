import test from 'node:test';
import assert from 'node:assert/strict';
import {fitCover, isPortrait} from '../../app/static/src/js/campaign-covers.js';

function fakeCover(naturalWidth, naturalHeight) {
  const classes = new Set();
  const frame = {classList: {add: name => classes.add(name), contains: name => classes.has(name)}};
  const attributes = {'data-cover': '', loading: 'lazy'};
  const inserted = [];
  const img = {
    naturalWidth, naturalHeight, parentElement: frame, alt: '', className: '',
    before: node => inserted.push(node),
    cloneNode: () => ({
      alt: 'x', className: '', attributes: {...attributes},
      removeAttribute(name) { delete this.attributes[name]; },
      setAttribute(name, value) { this.attributes[name] = value; },
    }),
  };
  return {img, frame, classes, inserted};
}

test('only pictures taller than wide count as portrait', () => {
  assert.equal(isPortrait(1650, 2550), true);
  assert.equal(isPortrait(1600, 900), false);
  assert.equal(isPortrait(800, 800), false);
  assert.equal(isPortrait(0, 0), false);
});

test('a portrait cover gets a blurred backdrop and the portrait class, once', () => {
  const {img, classes, inserted} = fakeCover(1375, 2125);
  fitCover(img);
  fitCover(img);
  assert(classes.has('cover-portrait'));
  assert.equal(inserted.length, 1);
  const [backdrop] = inserted;
  assert.equal(backdrop.className, 'cover-backdrop');
  assert.equal(backdrop.alt, '');
  assert.deepEqual(backdrop.attributes, {'aria-hidden': 'true'});
});

test('a landscape cover keeps the plain crop', () => {
  const {img, classes, inserted} = fakeCover(1920, 1080);
  fitCover(img);
  assert.equal(classes.size, 0);
  assert.equal(inserted.length, 0);
});

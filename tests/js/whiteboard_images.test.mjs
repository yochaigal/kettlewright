import test from 'node:test';
import assert from 'node:assert/strict';
import {COMPRESS_ABOVE, createImageCompressor, needsCompression} from '../../app/static/src/js/maps/whiteboard_images.js';

const tick = () => new Promise(resolve => setImmediate(resolve));
const big = 'data:image/png;base64,' + 'A'.repeat(COMPRESS_ABOVE);

function setup({result = {mimeType: 'image/webp', dataURL: 'data:image/webp;base64,small'}, fail = false} = {}) {
  let elements = [], settled = 0, ids = 0;
  const files = {}, encoded = [];
  const api = {addFiles: list => list.forEach(file => {files[file.id] = file;}), getSceneElements: () => elements,
    updateScene: ({elements: next, captureUpdate}) => {assert.equal(captureUpdate, 'never'); elements = next;}};
  const compressor = createImageCompressor({getApi: () => api, captureUpdate: 'never', onSettled: () => settled++,
    newId: () => `small-${++ids}`,
    encode: async (file, size) => {encoded.push({id: file.id, size}); if (fail) throw new Error(); return result;}});
  const add = (id, file) => {files[id] = {id, ...file}; elements.push({id: `element-${id}`, type: 'image', fileId: id, width: 300, height: 200, version: 1});};
  const drawing = () => ({elements, files: Object.fromEntries(elements.map(element => [element.fileId, files[element.fileId]]))});
  return {compressor, files, encoded, add, drawing, get settled() {return settled;}, get elements() {return elements;},
    set elements(value) {elements = value;}};
}

test('only large PNG/JPEG images and SVGs are compressed (#386)', () => {
  assert.equal(needsCompression({mimeType: 'image/png', dataURL: 'data:image/png;base64,tiny'}), false);
  assert.equal(needsCompression({mimeType: 'image/png', dataURL: big}), true);
  assert.equal(needsCompression({mimeType: 'image/jpeg', dataURL: big.replace('png', 'jpeg')}), true);
  assert.equal(needsCompression({mimeType: 'image/gif', dataURL: big}), false);
  assert.equal(needsCompression({mimeType: 'image/webp', dataURL: big}), false);
  assert.equal(needsCompression({mimeType: 'image/svg+xml', dataURL: 'data:image/svg+xml;base64,PHN2Zz4='}), true);
});

test('a new large image holds the save until its WebP copy replaces it', async () => {
  const s = setup();
  s.add('map', {mimeType: 'image/png', dataURL: big});
  s.add('token', {mimeType: 'image/png', dataURL: 'data:image/png;base64,token'});
  assert.equal(s.compressor.busy(s.drawing(), {files: {}}), true);
  assert.equal(s.compressor.busy(s.drawing(), {files: {}}), true);
  assert.equal(s.encoded.length, 1, 'one encode per image');
  assert.deepEqual(s.encoded[0].size, {width: 300, height: 200});
  await tick();
  assert.equal(s.settled, 1);
  assert.equal(s.elements[0].fileId, 'small-1');
  assert.equal(s.elements[0].version, 2);
  assert.equal(s.elements[1].fileId, 'token');
  assert.equal(s.files['small-1'].mimeType, 'image/webp');
  assert.equal(s.compressor.busy(s.drawing(), {files: {}}), false);
  // Undo brings the original back; it is swapped for the same copy without encoding again.
  s.elements = [{...s.elements[0], fileId: 'map'}];
  assert.equal(s.compressor.busy(s.drawing(), {files: {}}), true);
  assert.equal(s.elements[0].fileId, 'small-1');
  assert.equal(s.encoded.length, 1);
});

test('saved images are left alone, and a copy that is not smaller is not used', async () => {
  const saved = setup();
  saved.add('map', {mimeType: 'image/png', dataURL: big});
  assert.equal(saved.compressor.busy(saved.drawing(), {files: {map: saved.files.map}}), false);
  assert.equal(saved.encoded.length, 0);

  const larger = setup({result: {mimeType: 'image/webp', dataURL: big + 'more'}});
  larger.add('map', {mimeType: 'image/png', dataURL: big});
  assert.equal(larger.compressor.busy(larger.drawing(), {files: {}}), true);
  await tick();
  assert.equal(larger.elements[0].fileId, 'map');
  assert.equal(larger.settled, 1);
  assert.equal(larger.compressor.busy(larger.drawing(), {files: {}}), false);
});

test('SVGs are always converted, and a failed conversion does not hold saves forever', async () => {
  const svg = setup({result: {mimeType: 'image/png', dataURL: 'data:image/png;base64,' + 'B'.repeat(500)}});
  svg.add('drawing', {mimeType: 'image/svg+xml', dataURL: 'data:image/svg+xml;base64,PHN2Zz4='});
  svg.compressor.busy(svg.drawing(), {files: {}});
  await tick();
  assert.equal(svg.files[svg.elements[0].fileId].mimeType, 'image/png');

  const failed = setup({fail: true});
  failed.add('map', {mimeType: 'image/png', dataURL: big});
  failed.compressor.busy(failed.drawing(), {files: {}});
  await tick();
  assert.equal(failed.settled, 1);
  assert.equal(failed.compressor.busy(failed.drawing(), {files: {}}), false);
  assert.equal(failed.elements[0].fileId, 'map');
});

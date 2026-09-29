import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {libraryItems, loadLibraries, MAP_LIBRARIES} from '../../app/static/src/js/maps/libraries.js';

test('bundled v1 and v2 libraries keep every drawing and stable unique item IDs', async () => {
  const ids = new Set();
  for (const name of [...MAP_LIBRARIES, 'clocks']) {
    const data = JSON.parse(await readFile(new URL(`../../app/static/vendor/excalidraw-libraries/${name}.excalidrawlib`, import.meta.url)));
    const items = libraryItems(data, name);
    assert.deepEqual(items.map(item => item.elements), data.library || data.libraryItems.map(item => item.elements));
    assert.deepEqual(items, libraryItems(data, name));
    for (const item of items) {
      assert.ok(item.elements.length);
      assert.ok(!ids.has(item.id));
      ids.add(item.id);
    }
  }
  assert.equal(ids.size, 208);
});

test('one failed library does not prevent other libraries or the canvas from loading', async t => {
  t.mock.method(globalThis, 'fetch', async url => {
    if (url.pathname.includes('missing')) throw new Error('Offline');
    return {ok: true, json: async () => ({type: 'excalidrawlib', version: 1, library: [[{id: 'tree'}]]})};
  });
  const result = await loadLibraries(['trees', 'missing'], new URL('https://example.test/libraries/'));
  assert.equal(result.failed, true);
  assert.deepEqual(result.items.map(item => item.id), ['trees-0']);
});

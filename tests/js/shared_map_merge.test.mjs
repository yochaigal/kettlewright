import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source = readFileSync(new URL('../../app/static/src/js/maps/shared_map_merge.js', import.meta.url), 'utf8');
const {mergeDrawings} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const element = (id, x = 0) => ({id, type: 'rectangle', x});
const scene = (elements, color = '#ffffff', files = {}) => ({elements, files, appState: {viewBackgroundColor: color}});

test('independent edits and additions from both participants survive', () => {
  const base = scene([element('a'), element('b')]);
  const local = scene([element('a', 10), element('b'), element('c')]);
  const remote = scene([element('a'), element('b', 20), element('d')]);
  assert.deepEqual(mergeDrawings(base, local, remote).elements,
    [element('a', 10), element('b', 20), element('d'), element('c')]);
});

test('local deletion keeps remote additions and remote deletion stays deleted', () => {
  const base = scene([element('a'), element('b')]);
  assert.deepEqual(mergeDrawings(base, scene([element('b')]), scene([element('a'), element('c')])).elements,
    [element('c')]);
});

test('a conflicting object takes the edit being saved, including delete versus edit', () => {
  const base = scene([element('a')]);
  assert.deepEqual(mergeDrawings(base, scene([element('a', 10)]), scene([element('a', 20)])).elements, [element('a', 10)]);
  assert.deepEqual(mergeDrawings(base, scene([element('a', 10)]), scene([])).elements, [element('a', 10)]);
  assert.deepEqual(mergeDrawings(base, scene([]), scene([element('a', 20)])).elements, []);
});

test('JSON key order does not turn unchanged elements into local edits', () => {
  const base = scene([element('a')]);
  const local = scene([{x: 0, type: 'rectangle', id: 'a'}]);
  assert.deepEqual(mergeDrawings(base, local, scene([element('a', 20)])).elements, [element('a', 20)]);
});

test('remote background survives unless it was also edited locally', () => {
  assert.equal(mergeDrawings(scene([]), scene([]), scene([], '#000000')).appState.viewBackgroundColor, '#000000');
  assert.equal(mergeDrawings(scene([]), scene([], '#aabbcc'), scene([], '#000000')).appState.viewBackgroundColor, '#aabbcc');
});

test('images from both clients keep their files while deleted images release them', () => {
  const image = id => ({id, type: 'image', fileId: id});
  const base = scene([image('old')], '#ffffff', {old: {id: 'old'}});
  const local = scene([image('local')], '#ffffff', {local: {id: 'local'}});
  const remote = scene([image('old'), image('remote')], '#ffffff', {old: {id: 'old'}, remote: {id: 'remote'}});
  assert.deepEqual(mergeDrawings(base, local, remote).files, {local: {id: 'local'}, remote: {id: 'remote'}});
});

test('local stacking changes retain remote additions', () => {
  const base = scene([element('a'), element('b')]);
  const local = scene([element('b'), element('a')]);
  assert.deepEqual(mergeDrawings(base, local, scene([...base.elements, element('c')])).elements,
    [element('b'), element('a'), element('c')]);
  assert.deepEqual(mergeDrawings(base, base, scene([...local.elements, element('c')])).elements,
    [element('b'), element('a'), element('c')]);
});

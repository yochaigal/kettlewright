import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../../app/static/src/js/maps/party_tokens.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const scope = vm.createContext({});
vm.runInContext(source + '\nthis.helpers = {initials, tokenElement};', scope);
const {initials, tokenElement} = scope.helpers;
test('fallback initials handle empty and non-Latin names', () => {
  assert.equal(initials(''), '?');
  assert.equal(initials('  Ирина Волкова '), 'ИВ');
  assert.equal(initials('A long character name'), 'AL');
});
test('token stays scene-sized and centered after zoom and pan', () => {
  const token = tokenElement('portrait', {width: 1000, height: 600, zoom: {value: 2}, scrollX: -100, scrollY: 30}, 'token');
  assert.equal(token.x, 310); assert.equal(token.y, 80);
  assert.equal(token.width, 80); assert.equal(token.fileId, 'portrait');
  assert.equal(token.type, 'image'); assert.equal(token.locked, false);
});

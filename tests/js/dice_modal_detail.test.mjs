import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// dice_modal.js needs a page to load; evaluate only its result-line parser.
const source = readFileSync(new URL('../../app/static/src/js/dice_modal.js', import.meta.url), 'utf8');
const body = source.slice(source.indexOf('export function extraDetail'), source.indexOf('\n}\n', source.indexOf('export function extraDetail')) + 2);
const extraDetail = new Function(`${body.replace('export ', '')}; return extraDetail;`)();

test('the dice modal keeps what a result says beyond the dice', () => {
  assert.equal(extraDetail('Reaction Roll: 6, 1 (2d6) = 7 — Curious'), '7 — Curious');
  assert.equal(extraDetail('4, 3 (d6+d6) · STR 12 · Success'), 'STR 12 · Success');
  assert.equal(extraDetail('Roll Dice: 17 (d20)'), '');
  assert.equal(extraDetail('no dice here'), '');
});

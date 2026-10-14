import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

function roller(active = '1') {
  const element = () => ({disabled: false, listeners: {}, addEventListener(event, fn) { this.listeners[event] = fn; }});
  const buttons = [element(), element(), element()];
  buttons[1].dataset = {wardenRoll: 'reaction'};
  buttons[2].dataset = {wardenRoll: 'fate'};
  const modal = {resultText: null, initialize(callback) { this.roll = callback; },
    setMode(mode) { this.mode = mode; }, showDiceModal() { this.open = true; }};
  const result = {textContent: ''};
  modal.resultText = result;
  const select = {...element(), value: '', options: [{value: ''}, {value: '1'}]};
  const publicToggle = {...element(), checked: true};
  const panel = {dataset: {rollUrl: '/warden/roll', error: 'Roll failed'},
    querySelectorAll(selector) { return selector === 'button' ? buttons : buttons.slice(1); }};
  const form = {elements: {party_id: select}};
  const stored = new Map([['warden-roll-party', active]]);
  const requests = [];
  const context = vm.createContext({
    document: {getElementById(id) { return {
      'warden-dice': panel, 'warden-dice-form': form, 'warden-roll-result': result,
      'warden-roll-party': select, 'warden-dice-button': buttons[0],
      'warden-public-roll': publicToggle,
    }[id] || null; }},
    diceModal: modal,
    notification: {showNotification() {}}, refreshRollHistory() {},
    localStorage: {getItem: key => stored.get(key), setItem: (key, value) => stored.set(key, value)},
    FormData: class extends Map {constructor() {
      super([['party_id', select.value], ['csrf_token', 'csrf']]);
      if (publicToggle.checked && !publicToggle.disabled) this.set('public_roll', 'on');
    }},
    fetch: async (url, options) => { requests.push({url, ...options}); return {ok: true, json: async () => ({result: '<private result>', values: [6]})}; },
  });
  const source = readFileSync(new URL('../../app/static/src/js/warden_dice.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export async function', 'async function');
  vm.runInContext(source, context);
  return {context, buttons, result, select, requests, stored, publicToggle, modal};
}

test('header opens the shared modal and every roll uses its result display', async () => {
  const {buttons, modal, result, requests} = roller();
  buttons[0].listeners.click();
  assert.equal(modal.open, true);
  assert.equal(modal.mode, 'party');
  await modal.roll('d20');
  assert.equal(requests[0].body.get('kind'), 'dice');
  assert.equal(requests[0].body.get('dice'), 'd20');
  for (const [index, kind] of [[1, 'reaction'], [2, 'fate']]) {
    result.textContent = '';
    await buttons[index].listeners.click();
    assert.equal(requests[index].body.get('kind'), kind);
    assert.equal(result.textContent, '<private result>');
  }
});

test('Tools restores owned active party and sends server request with CSRF', async () => {
  const {context, select, requests, result, stored} = roller();
  assert.equal(select.value, '1');
  await context.requestWardenRoll('reaction');
  assert.equal(requests[0].url, '/warden/roll');
  assert.equal(requests[0].method, 'POST');
  assert.equal(requests[0].body.get('party_id'), '1');
  assert.equal(requests[0].body.get('csrf_token'), 'csrf');
  assert.equal(requests[0].body.get('kind'), 'reaction');
  assert.equal(requests[0].body.has('public_roll'), false);
  assert.equal(result.textContent, '<private result>');
  select.value = '';
  select.listeners.change();
  assert.equal(stored.get('warden-roll-party'), '');
});

test('stale active party falls back to no party', () => {
  const {select, publicToggle} = roller('999');
  assert.equal(select.value, '');
  assert.equal(publicToggle.disabled, true);
  assert.equal(publicToggle.checked, false);
});

test('public mode requires an explicit choice and resets when the party is cleared', async () => {
  const {context, publicToggle, requests, select} = roller();
  assert.equal(publicToggle.checked, false);
  publicToggle.checked = true;
  await context.requestWardenRoll('fate');
  assert.equal(requests[0].body.get('public_roll'), 'on');
  select.value = '';
  select.listeners.change();
  assert.equal(publicToggle.disabled, true);
  assert.equal(publicToggle.checked, false);
  select.value = '1';
  select.listeners.change();
  assert.equal(publicToggle.disabled, false);
  assert.equal(publicToggle.checked, false);
});

test('pending roll prevents duplicate submission and unlocks controls on failure', async () => {
  const {context, buttons, result} = roller();
  let resolve;
  context.fetch = () => new Promise(done => { resolve = done; });
  const pending = context.requestWardenRoll('fate');
  assert.ok(buttons.every(button => button.disabled));
  await assert.rejects(context.requestWardenRoll('fate'), /Roll failed/);
  resolve({ok: false, json: async () => ({error: 'Forbidden'})});
  await assert.rejects(pending, /Forbidden/);
  assert.ok(buttons.every(button => !button.disabled));
  assert.equal(result.textContent, '');
});

test('login redirect cannot be treated as a successful roll', async () => {
  const {context, buttons} = roller();
  context.fetch = async () => ({redirected: true});
  await assert.rejects(context.requestWardenRoll('dice', 'd20'), /Roll failed/);
  assert.ok(buttons.every(button => !button.disabled));
});

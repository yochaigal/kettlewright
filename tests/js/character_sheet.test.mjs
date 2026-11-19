import test from 'node:test';
import assert from 'node:assert/strict';
import {renderSheet, setupCharacterSheet} from '../../app/static/src/js/maps/character_sheet.js';

// A small DOM: enough elements, attributes and events for the sheet.
class Node {
  constructor(tag) {this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {}; this.attributes = {}; this.listeners = {}; this.disabled = false; this.hidden = false;}
  get textContent() {return this._text ?? this.children.map(child => typeof child === 'string' ? child : child.textContent).join('');}
  set textContent(value) {this._text = value; this.children = [];}
  append(...nodes) {if (nodes.length) {this._text = undefined; this.children.push(...nodes);}}
  replaceChildren(...nodes) {this.children = []; this.append(...nodes.filter(node => node !== ''));}
  setAttribute(name, value) {this.attributes[name] = String(value);}
  getAttribute(name) {return this.attributes[name];}
  addEventListener(name, fn) {this.listeners[name] = fn;}
  removeEventListener(name) {delete this.listeners[name];}
  all(test) {return this.children.flatMap(child => typeof child === 'string' ? [] : [...(test(child) ? [child] : []), ...child.all(test)]);}
}
for (const key of ['type', 'value', 'checked', 'className']) Object.defineProperty(Node.prototype, key, {writable: true, value: ''});
const doc = {createElement: tag => new Node(tag)};
const messages = {hp: 'HP', strength: 'STR', dexterity: 'DEX', willpower: 'WIL', armor: 'Armor', deprived: 'Deprived',
  panicked: 'Panicked', dead: 'Dead', inventory: 'Inventory', slots: '{used}/{total} slots', uses: 'uses', charges: 'charges',
  use: 'Use', clear: 'Clear', addFatigue: 'Add Fatigue', lower: 'Lower {stat}', raise: 'Raise {stat}', loading: 'Loading',
  failed: 'Failed', saveFailed: 'Save failed', effective: 'Effective HP: {hp}'};
const character = (overrides = {}) => ({id: 7, name: 'Ada', hp: {value: 0, stored: 3, max: 6},
  strength: {value: 12, max: 14}, dexterity: {value: 10, max: 10}, willpower: {value: 0, max: 9}, armor: 1,
  deprived: false, panicked: true, dead: false, containers: [{id: 0, name: 'Main', slots: 10, used: 3, items: [
    {id: 1, name: 'Lantern', fatigue: false, uses: 2, max_uses: 4, charges: 0, max_charges: 3},
    {id: 9, name: 'Fatigue', fatigue: true}]}], ...overrides});
const buttons = node => node.all(child => child.tagName === 'BUTTON');
const label = (node, text) => buttons(node).find(button => button.attributes['aria-label'] === text || button.textContent === text);

test('the compact sheet shows stats, effective HP, conditions and the inventory (#423)', () => {
  const changes = [];
  const sheet = renderSheet(doc, character(), messages, change => changes.push(change));
  const outputs = sheet.all(node => node.tagName === 'OUTPUT').map(node => node.textContent);
  assert.deepEqual(outputs, ['0/6', '12/14', '10/10', '0/9', '1']);
  assert.ok(sheet.textContent.includes('Effective HP: 0'));
  assert.ok(sheet.textContent.includes('3/10 slots'));
  // Limits: −/+ follow the recorded value, so a panicked character can still be healed.
  assert.equal(label(sheet, 'Lower HP').disabled, false);
  assert.equal(label(sheet, 'Raise DEX').disabled, true);
  assert.equal(label(sheet, 'Lower WIL').disabled, true);
  label(sheet, 'Lower HP').listeners.click();
  label(sheet, 'Add Fatigue').listeners.click();
  label(sheet, 'Clear').listeners.click();
  const [usesButton, chargesButton] = buttons(sheet).filter(button => button.textContent === 'Use');
  usesButton.listeners.click();
  assert.equal(chargesButton.disabled, true);
  assert.equal(usesButton.attributes['aria-label'], 'Use: Lantern, 2/4 uses');
  const [deprived, panicked] = sheet.all(node => node.type === 'checkbox');
  assert.equal(panicked.checked, true);
  deprived.checked = true; deprived.listeners.change();
  assert.deepEqual(changes, [{action: 'stat', stat: 'hp', value: -1}, {action: 'fatigue', amount: 1},
    {action: 'remove', item: 9}, {action: 'use', item: 1, resource: 'uses'}, {action: 'condition', condition: 'deprived', active: true}]);
  // While a change is saving, nothing else can be changed.
  assert.ok(buttons(renderSheet(doc, character(), messages, () => {}, true)).every(button => button.disabled));
});

function page({respond}) {
  const nodes = {}, requests = [], handlers = {};
  for (const id of ['character-sheet', 'board-sheet', 'sheet-body', 'sheet-status', 'sheet-character', 'close-sheet']) nodes[id] = new Node('div');
  Object.assign(nodes['character-sheet'], {open: false, showModal() {this.open = true;}, close() {this.open = false; this.listeners.close?.();}});
  const config = {partyId: 1, sheetsUrl: '/party/1/shared-map/sheets', csrfToken: 'token', messages: {sheet: messages}};
  const sheet = setupCharacterSheet({config, doc: {...doc, getElementById: id => nodes[id]},
    socket: {on: (name, fn) => {handlers[name] = fn;}, off() {}},
    request: async (url, options = {}) => {requests.push([url, options]); return respond(url, options);}});
  return {nodes, requests, handlers, sheet, config};
}
const tick = () => new Promise(resolve => setImmediate(resolve));

test('opening the sheet loads it, saves changes and shows refusals', async () => {
  let next = {ok: true, status: 200, json: async () => ({characters: [character()]})};
  const p = page({respond: () => next});
  p.nodes['board-sheet'].listeners.click(); await tick();
  assert.equal(p.nodes['character-sheet'].open, true);
  assert.equal(p.nodes['board-sheet'].attributes['aria-expanded'], 'true');
  assert.equal(p.nodes['sheet-character'].hidden, true);
  next = {ok: true, status: 200, json: async () => character({hp: {value: 0, stored: 2, max: 6}})};
  label(p.nodes['sheet-body'], 'Lower HP').listeners.click(); await tick();
  const [url, options] = p.requests.at(-1);
  assert.equal(url, '/party/1/shared-map/sheets/7');
  assert.deepEqual(JSON.parse(options.body), {action: 'stat', stat: 'hp', value: -1, csrf_token: 'token'});
  assert.ok(p.nodes['sheet-body'].textContent.includes('0/6'));
  next = {ok: false, status: 400, json: async () => ({reason: 'invalid', message: 'Only 0 uses remain.'})};
  label(p.nodes['sheet-body'], 'Add Fatigue').listeners.click(); await tick();
  assert.equal(p.nodes['sheet-status'].textContent, 'Only 0 uses remain.');
  next = {ok: false, status: 400, json: async () => ({reason: 'csrf'})};
  label(p.nodes['sheet-body'], 'Add Fatigue').listeners.click(); await tick();
  assert.equal(p.nodes['sheet-status'].textContent, 'Save failed');
  // Changes made elsewhere reload the open sheet, for this party only.
  const before = p.requests.length;
  next = {ok: true, status: 200, json: async () => ({characters: [character(), character({id: 8, name: 'Bo'})]})};
  p.handlers.party_members_changed({party_id: 2}); await tick();
  assert.equal(p.requests.length, before);
  p.handlers.party_members_changed({party_id: 1}); await tick();
  assert.equal(p.nodes['sheet-character'].hidden, false);
  p.nodes['close-sheet'].listeners.click();
  assert.equal(p.nodes['board-sheet'].attributes['aria-expanded'], 'false');
  p.handlers.party_members_changed({party_id: 1}); await tick();
  assert.equal(p.requests.length, before + 1);
});

test('without a sheet (the site, or the Warden) nothing is set up', () => {
  const sheet = setupCharacterSheet({config: {sheetsUrl: null, messages: {}}, socket: {on() {assert.fail();}},
    doc: {getElementById: () => null}});
  sheet.destroy();
});

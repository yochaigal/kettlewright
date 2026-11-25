import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import './support/cairn.mjs';  // Cairn, the system these tests play.
import {actorKey} from '../../app/static/src/js/maps/token_stats.js';
import {hideablePanel} from '../../app/static/src/js/maps/board_panels.js';
import {gameSystem} from '#kettlewright';

const source = readFileSync(new URL('../../app/static/src/js/maps/board_rolls.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));
class Node {
  constructor(tag = '') {
    this.tag = tag; this.children = []; this.dataset = {}; this.events = {}; this.checked = true; this.attributes = {};
    const classes = new Set();
    this.classList = {toggle: (name, on) => {if (on) classes.add(name); else classes.delete(name);}, contains: name => classes.has(name)};
  }
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren() {this.children = [];}
  addEventListener(name, fn) {this.events[name] = fn;}
  removeEventListener() {}
  setAttribute(name, value) {this.attributes[name] = value;}
  querySelectorAll() {return this.children.filter(node => node.tag === 'button');}
}
const monster = {id: 'companion:7', name: 'Wolf', kind: 'monster', damage: ['d6+d6', 'd8'],
  stats: {strength: 12, dexterity: 9, willpower: null}};

async function setup(warden = true, {storage = {}, osd = null, system = null} = {}) {
  const nodes = new Map(), events = {}, frames = [], requests = [], intervals = [];
  const node = id => {if (!nodes.has(id)) nodes.set(id, new Node()); return nodes.get(id);};
  const actives = [];
  let roster = warden ? [monster] : [
    {id: '3', name: 'Ada', kind: 'character', weapons: [{name: 'Sword', dice: 'd8'}, {name: 'Bow', dice: 'd6'}],
     attributes: {strength: [10, 12], dexterity: [14, 14], willpower: [8, 9]}},
    {id: '4', name: 'Pip', kind: 'character', weapons: [], attributes: {strength: [5, 5], dexterity: [5, 5], willpower: [5, 5]}}];
  let selected = {}, allowed = true, preview = false;
  let post = async () => ({ok: true, json: async () => ({result: 'A result', values: [4]})});
  const modal = {resultText: new Node(), initialize(fn) {this.roll = fn;}, setMode(value) {this.mode = value;}, showDiceModal() {this.open = true;}};
  const specials = ['reaction', 'fate'].map(kind => {const button = new Node('button'); button.dataset.wardenRoll = kind; return button;});
  const document = {hidden: false, getElementById: node, querySelector: () => node('modal-title'),
    querySelectorAll: () => warden ? specials : [], createElement: tag => new Node(tag),
    addEventListener() {}, removeEventListener() {}};
  const dice3d = {enabled: false, show: async () => false, isAvailable: () => true, isEnabled() {return this.enabled;},
    setEnabled(value) {this.enabled = value;}};
  const localStorage = {getItem: key => storage[key] ?? null, setItem: (key, value) => {storage[key] = value;}};
  const context = vm.createContext({document, actorKey, hideablePanel, gameSystem: system ? () => system : gameSystem, diceModal: modal, dice3d, localStorage, FormData: Map, AbortSignal,
    requestAnimationFrame: fn => {frames.push(fn); return frames.length;}, cancelAnimationFrame() {},
    setInterval(fn) {intervals.push(fn);}, clearInterval() {},
    fetch: async (url, options) => {
      if (!options.method) return {ok: true, json: async () => ({actors: structuredClone(roster)})};
      requests.push({url, body: options.body}); return post();
    }});
  vm.runInContext(source + '\nthis.create = createBoardRolls;', context);
  const controller = context.create({config: {warden, partyId: 1, rollActorsUrl: '/actors', rollUrl: '/roll', wardenRollUrl: '/warden',
    csrfToken: 'csrf', messages: {warden: 'Warden', rollDice: 'Roll Dice', damage: 'DMG', reaction: 'Reaction', fate: 'Fate', rollFailed: 'Failed'}},
    getApi: () => ({getAppState: () => ({selectedElementIds: selected}),
      getSceneElements: () => Object.keys(selected).map(id => ({id}))}), updates: {subscribe(key, callback) {
        const update = () => callback(structuredClone(roster));
        events.party_actors_changed = update; events.party_members_changed = update; update(); return () => {};
      }},
    canRoll: () => allowed, isPlayerPreview: () => preview, osd, onActive: id => actives.push(id)});
  const draw = () => frames.splice(0).forEach(fn => fn());
  await tick(); draw();
  return {controller, node, requests, modal, specials, events, draw, dice3d, storage, actives,
    button: label => node('board-roll-actions').children.find(child => child.ariaLabel === label),
    select(value) {selected = value; controller.redraw(); draw();},
    setRoster(value) {roster = value;}, setPost(fn) {post = fn;},
    preview(value) {preview = value; controller.redraw(); draw();},
    allow(value) {allowed = value; controller.redraw(); draw();}};
}

test('Warden always has the full roller, with explicit public opt-in and special rolls', async () => {
  const s = await setup();
  try {
    assert.equal(s.node('board-roll-name').textContent, 'Warden');
    assert.equal(s.node('board-roll-public').checked, false);
    assert.equal(s.node('board-roll-actions').children.length, 14);
    s.button('d100').events.click(); await tick();
    assert.equal(s.requests[0].url, '/warden');
    assert.equal(s.requests[0].body.get('dice'), 'd100');
    assert.equal(s.requests[0].body.has('public_roll'), false);
    assert.equal(s.requests[0].body.get('csrf_token'), 'csrf');
    s.node('board-roll-public').checked = true;
    s.button('Reaction').events.click(); await tick();
    assert.equal(s.requests[1].body.get('kind'), 'reaction');
    assert.equal(s.requests[1].body.get('public_roll'), 'on');
    assert.equal(s.node('board-roll-result').textContent, 'A result');
    s.button('Fate').events.click(); await tick();
    assert.equal(s.requests[2].body.get('kind'), 'fate');
  } finally {s.controller.destroy();}
});

test('the panel and dice-modal public switches are one choice (#399)', async () => {
  const s = await setup();
  try {
    const panel = s.node('board-roll-public'), modal = s.node('warden-public-roll');
    assert.equal(panel.checked, false); assert.equal(modal.checked, false);
    panel.checked = true; panel.events.change();
    assert.equal(modal.checked, true);
    modal.checked = false; modal.events.change();
    assert.equal(panel.checked, false);
    modal.checked = true; modal.events.change();
    s.select({'actor-companion-7-token': true}); s.select({});
    assert.equal(panel.checked, true);
  } finally {s.controller.destroy();}
});

test('selecting a monster offers damage, saves and its own modal, then returns to Warden controls', async () => {
  const s = await setup();
  try {
    s.node('board-roll-public').checked = true;
    s.select({'actor-companion-7-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Wolf');
    // A public choice stays when another token is selected (#399).
    assert.equal(s.node('board-roll-public').checked, true);
    s.node('board-roll-public').checked = false;
    assert.equal(s.button('WIL').disabled, true);
    assert.equal(s.button('d100'), undefined);
    s.button('DMG d6+d6').events.click(); await tick();
    assert.equal(s.requests[0].url, '/roll');
    assert.equal(s.requests[0].body.get('companion_id'), '7');
    s.button('STR').events.click(); await tick();
    assert.equal(s.requests[1].body.get('save'), 'strength');
    assert.equal(s.requests[1].body.get('dice'), 'd20');
    s.button('Roll Dice').events.click();
    assert.equal(s.modal.open, true); assert.equal(s.node('modal-title').textContent, 'Wolf');
    await s.modal.roll('d8');
    assert.equal(s.requests[2].body.get('companion_id'), '7');
    assert.ok(s.specials.every(button => button.hidden));
    s.select({});
    assert.equal(s.node('board-roll-name').textContent, 'Warden');
    assert.ok(s.button('Reaction'));
  } finally {s.controller.destroy();}
});

test('a player\'s roller has its character\'s quick rolls, follows owned tokens and can choose another owned character', async () => {
  const s = await setup(false);
  try {
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    // Its weapons' damage, its saves, and the dice window for the rest (#532).
    assert.deepEqual(s.node('board-roll-actions').children.map(child => child.ariaLabel),
      ['Sword d8', 'Bow d6', 'STR', 'DEX', 'WIL', 'Roll Dice']);
    assert.equal(s.node('board-roll-actions').dataset.mode, 'quick');
    assert.equal(s.node('board-roll-actor').hidden, false);
    assert.equal(s.button('d100'), undefined);
    s.button('Bow d6').events.click(); await tick();
    assert.equal(s.requests[0].body.get('character_id'), '3');
    assert.equal(s.requests[0].body.get('dice'), 'd6');
    assert.equal(s.requests[0].body.get('public_roll'), 'on');
    s.button('DEX').events.click(); await tick();
    assert.equal(s.requests[1].body.get('save'), 'dexterity');
    assert.equal(s.requests[1].body.get('dice'), 'd20');
    s.select({'actor-4-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Pip');
    s.node('board-roll-actor').value = '3'; s.node('board-roll-actor').events.change(); s.draw();
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    s.select({'actor-companion-7-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    s.select({});
    assert.equal(s.node('board-rolls').hidden, false);
    // The ring follows the character in the roller, picked or selected (#375); a preview shows none.
    assert.equal(s.actives.at(-1), '3');
    s.select({'actor-4-token': true});
    assert.equal(s.actives.at(-1), '4');
    s.preview(true);
    assert.equal(s.actives.at(-1), null);
  } finally {s.controller.destroy();}
});

test('pending rolls prevent duplicates, preview hides the roller and revoked actors cannot roll', async () => {
  const s = await setup();
  try {
    let resolve;
    s.setPost(() => new Promise(done => {resolve = done;}));
    s.button('d6').events.click(); s.button('d6').events.click(); await tick();
    assert.equal(s.requests.length, 1); assert.equal(s.button('d6').disabled, true);
    resolve({ok: false}); await tick();
    assert.equal(s.node('board-roll-result').textContent, 'Failed');
    assert.equal(s.button('d6').disabled, false);
    s.preview(true); assert.equal(s.node('board-rolls').hidden, true);
    s.preview(false); assert.equal(s.node('board-rolls').hidden, false);
    s.allow(false); assert.equal(s.button('d6').disabled, true);
  } finally {s.controller.destroy();}
  const player = await setup(false);
  try {
    player.setRoster([]); player.events.party_members_changed({party_id: 1}); await tick(); player.draw();
    assert.ok(player.node('board-roll-actions').children.every(button => button.disabled));
  } finally {player.controller.destroy();}
});

test('the roller hides from its × and comes back from Dice in the top bar, remembered (Discord feedback)', async () => {
  const s = await setup();
  try {
    const panel = s.node('board-rolls'), toggle = s.node('board-dice-toggle');
    assert.equal(panel.classList.contains('is-user-hidden'), false);
    s.node('board-roll-hide').events.click();
    assert.equal(panel.classList.contains('is-user-hidden'), true);
    assert.equal(toggle.attributes['aria-pressed'], 'false');
    assert.equal(s.storage['board-rolls-hidden'], 'hidden');
    toggle.events.click();
    assert.equal(panel.classList.contains('is-user-hidden'), false);
    assert.equal(toggle.attributes['aria-pressed'], 'true');
    assert.equal(s.storage['board-rolls-hidden'], 'shown');
  } finally {s.controller.destroy();}
  // Hidden last time, or minimized with the old setting: hidden on load.
  for (const storage of [{'board-rolls-hidden': 'hidden'}, {'board-rolls-minimized': 'on'}]) {
    const again = await setup(true, {storage});
    try {assert.equal(again.node('board-rolls').classList.contains('is-user-hidden'), true);
    } finally {again.controller.destroy();}
  }
});

test('the 3D toggle switches the whiteboard\'s own 3D dice choice (#436)', async () => {
  const s = await setup();
  try {
    const toggle = s.node('board-roll-3d');
    assert.equal(toggle.hidden, false);
    assert.equal(toggle.attributes['aria-pressed'], 'false');
    toggle.events.click();
    assert.equal(s.dice3d.enabled, true);
  } finally {s.controller.destroy();}
});

test('own rolls go on screen once settled and their socket echo is recognised (#385)', async () => {
  const calls = [];
  const osd = {hold: () => calls.push(['hold']), release: (...args) => calls.push(['release', ...args]),
    own: (...args) => calls.push(['own', ...args])};
  const s = await setup(true, {osd});
  try {
    s.button('d6').events.click(); await tick();
    assert.deepEqual(calls, [['hold'], ['release', 'Warden', 'A result'], ['own', 'Warden', 'A result']]);
    calls.length = 0;
    s.setPost(async () => ({ok: false}));
    s.button('d6').events.click(); await tick();
    assert.deepEqual(calls, [['hold'], ['release', null, undefined]]);
    calls.length = 0;
    s.setPost(async () => ({ok: true, json: async () => ({result: 'A result', values: [4]})}));
    await s.modal.roll('d8');  // The dice modal shows its own result.
    assert.deepEqual(calls.map(call => call[0]), ['hold', 'release']);
  } finally {s.controller.destroy();}
});

test('the save buttons are the page system\'s attributes that can be saved (#487)', async () => {
  const lucky = {key: 'lucky', hp: {key: 'hp', abbr: 'HP', label: 'HP'},
    attributes: [{key: 'strength', abbr: 'STR', label: 'STR', save: true}, {key: 'luck', abbr: 'LCK', label: 'LCK', save: true},
      {key: 'renown', abbr: 'REN', label: 'REN', save: false}], conditions: []};
  const s = await setup(true, {system: lucky});
  try {
    s.setRoster([{...monster, stats: {strength: 12, luck: 9, renown: 3}}]);
    s.events.party_actors_changed({party_id: 1}); s.draw();
    s.select({'actor-companion-7-token': true});
    assert.ok(s.button('STR') && s.button('LCK'));
    assert.equal(s.button('DEX'), undefined); assert.equal(s.button('REN'), undefined);  // Renown is no save.
    s.button('LCK').events.click(); await tick();
    assert.equal(s.requests.at(-1).body.get('save'), 'luck');
  } finally {s.controller.destroy();}
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {actorKey} from '../../app/static/src/js/maps/token_stats.js';

const source = readFileSync(new URL('../../app/static/src/js/maps/board_rolls.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));
class Node {
  constructor(tag = '') {this.tag = tag; this.children = []; this.dataset = {}; this.events = {}; this.checked = true;}
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren() {this.children = [];}
  addEventListener(name, fn) {this.events[name] = fn;}
  removeEventListener() {}
  setAttribute() {}
  querySelectorAll() {return this.children.filter(node => node.tag === 'button');}
}
const monster = {id: 'companion:7', name: 'Wolf', kind: 'monster', damage: ['d6+d6', 'd8'],
  stats: {strength: 12, dexterity: 9, willpower: null}};

async function setup(warden = true) {
  const nodes = new Map(), events = {}, frames = [], requests = [], intervals = [];
  const node = id => {if (!nodes.has(id)) nodes.set(id, new Node()); return nodes.get(id);};
  let roster = warden ? [monster] : [{id: '3', name: 'Ada', kind: 'character'}, {id: '4', name: 'Pip', kind: 'character'}];
  let selected = {}, allowed = true, preview = false;
  let post = async () => ({ok: true, json: async () => ({result: 'A result', values: [4]})});
  const modal = {resultText: new Node(), initialize(fn) {this.roll = fn;}, setMode(value) {this.mode = value;}, showDiceModal() {this.open = true;}};
  const specials = ['reaction', 'fate'].map(kind => {const button = new Node('button'); button.dataset.wardenRoll = kind; return button;});
  const document = {hidden: false, getElementById: node, querySelector: () => node('modal-title'),
    querySelectorAll: () => warden ? specials : [], createElement: tag => new Node(tag),
    addEventListener() {}, removeEventListener() {}};
  const context = vm.createContext({document, actorKey, diceModal: modal, FormData: Map, AbortSignal,
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
    canRoll: () => allowed, isPlayerPreview: () => preview});
  const draw = () => frames.splice(0).forEach(fn => fn());
  await tick(); draw();
  return {controller, node, requests, modal, specials, events, draw,
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

test('selecting a monster offers damage, saves and its own modal, then returns to Warden controls', async () => {
  const s = await setup();
  try {
    s.node('board-roll-public').checked = true;
    s.select({'actor-companion-7-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Wolf');
    assert.equal(s.node('board-roll-public').checked, false);
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

test('player roller always shows all player dice, follows owned tokens and supports choosing another owned character', async () => {
  const s = await setup(false);
  try {
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    assert.equal(s.node('board-roll-actions').children.length, 11);
    assert.equal(s.node('board-roll-actor').hidden, false);
    assert.equal(s.button('d100'), undefined);
    s.button('d6+d6').events.click(); await tick();
    assert.equal(s.requests[0].body.get('character_id'), '3');
    assert.equal(s.requests[0].body.get('public_roll'), 'on');
    s.select({'actor-4-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Pip');
    s.node('board-roll-actor').value = '3'; s.node('board-roll-actor').events.change(); s.draw();
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    s.select({'actor-companion-7-token': true});
    assert.equal(s.node('board-roll-name').textContent, 'Ada');
    s.select({});
    assert.equal(s.node('board-rolls').hidden, false);
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

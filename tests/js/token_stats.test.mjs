import test from 'node:test';
import assert from 'node:assert/strict';
import {actorKey, tokenStatsPosition, createTokenStats} from '../../app/static/src/js/maps/token_stats.js';

class Node {
  constructor() {this.children = []; this.style = {}; this.attrs = {}; this.events = {};}
  append(...children) {for (const child of children) {child.parent = this; this.children.push(child);}}
  replaceChildren(...children) {this.children = []; this.append(...children);}
  remove() {if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);}
  setAttribute(key, value) {this.attrs[key] = value;}
  addEventListener(name, callback) {this.events[name] = callback;}
  querySelector(selector) {return this.children.find(child => child.tag === selector) || null;}
}

const actor = {id: 'companion:7', name: 'Wolf', kind: 'monster', shared: false,
  stats: {hp: [3, 6], strength: [12, 12]}, armor: 1, attack: 'bite (d6)'};

test('legacy token IDs and rotated/scaled positions remain attached to their actors', () => {
  assert.equal(actorKey('actor-companion-7-copy'), 'companion:7');
  assert.equal(actorKey('actor-3-copy'), '3');
  assert.equal(actorKey('map-background'), null);
  assert.deepEqual(tokenStatsPosition({x: 40, y: 10, width: 80, height: 40, angle: Math.PI / 2},
    {scrollX: -20, scrollY: 5, zoom: {value: 2}}), {x: 120, y: 152, scale: 1});
});

test('stats shrink with token resizing and camera zoom without a minimum scale', () => {
  const state = {scrollX: 0, scrollY: 0, zoom: {value: 1}};
  const full = tokenStatsPosition({x: 0, y: 0, width: 80, height: 80}, state);
  const small = tokenStatsPosition({x: 0, y: 0, width: 20, height: 20}, state);
  const zoomed = tokenStatsPosition({x: 0, y: 0, width: 20, height: 20}, {...state, zoom: {value: .2}});
  assert.deepEqual(full, {x: 40, y: 82, scale: 1});
  assert.deepEqual(small, {x: 10, y: 20.5, scale: .25});
  assert.deepEqual(zoomed, {x: 2, y: 4.1, scale: .05});
});

test('inline visibility requires confirmation, preserves notes, and clears on revocation', async () => {
  const globals = ['document', 'requestAnimationFrame', 'cancelAnimationFrame', 'ResizeObserver', 'fetch', 'confirm', 'setInterval', 'clearInterval'];
  const originals = new Map(globals.map(key => [key, globalThis[key]]));
  const host = new Node(), events = {}, requests = [], frames = [];
  let current = structuredClone(actor), preview = false, confirmResult = false;
  const elements = [{id: 'actor-companion-7-copy', x: 0, y: 0, width: 80, height: 80}];
  globalThis.document = {createElement(tag) {const node = new Node(); node.tag = tag; return node;},
    createTextNode(text) {const node = new Node(); node.textContent = text; return node;}, addEventListener() {}, removeEventListener() {}};
  globalThis.requestAnimationFrame = fn => {frames.push(fn); return frames.length;};
  globalThis.cancelAnimationFrame = () => {};
  globalThis.ResizeObserver = class {observe() {} disconnect() {}};
  globalThis.setInterval = () => 1; globalThis.clearInterval = () => {};
  globalThis.confirm = () => confirmResult;
  globalThis.fetch = async (url, options) => {
    requests.push({url, options});
    if (options.method === 'POST') current.shared = JSON.parse(options.body).shared;
    return {ok: true, json: async () => ({actors: [structuredClone(current)]})};
  };
  const tick = () => new Promise(resolve => setImmediate(resolve));
  const draw = () => {frames.splice(0).forEach(fn => fn());};
  let overlay;
  try {
    overlay = createTokenStats({editor: {querySelector: () => host},
      config: {warden: true, partyId: 1, statsUrl: '/stats', visibilityUrl: '/monsters/0/visibility', csrfToken: 'csrf', messages: {}},
      getApi: () => ({getSceneElements: () => elements, getAppState: () => ({zoom: {value: 1}, scrollX: 0, scrollY: 0, width: 800, height: 600})}),
      canReveal: () => true, confirmReveal: async () => confirmResult, isPlayerPreview: () => preview, socket: {on(name, callback) {events[name] = callback;}, off() {}}});
    await tick(); draw();
    const layer = host.children[0], stats = layer.children[0];
    assert.deepEqual(stats.children[0].children.map(value => value.textContent), ['HP 3', 'STR 12']);
    const button = stats.querySelector('button');
    button.events.click({stopPropagation() {}}); await tick();
    assert.equal(requests.filter(r => r.options.method === 'POST').length, 0);
    confirmResult = true; button.events.click({stopPropagation() {}}); await tick(); draw();
    const post = requests.find(r => r.options.method === 'POST');
    assert.deepEqual(JSON.parse(post.options.body), {shared: true, csrf_token: 'csrf'});
    assert.equal(layer.children[0].querySelector('button').attrs['aria-pressed'], 'true');
    preview = true; overlay.reset(); draw();
    assert.equal(layer.children.length, 1);
    assert.equal(layer.children[0].querySelector('button'), null);
    current.shared = false; events.party_actors_changed({party_id: 1}); await tick(); draw();
    assert.equal(layer.children.length, 0);
    preview = false; overlay.reset(); draw();
    assert.equal(layer.children.length, 1);
    elements[0].x = 100; overlay.redraw(); draw();
    assert.equal(layer.children[0].style.left, '140px');
    elements.length = 0; overlay.redraw(); draw();
    assert.equal(layer.children.length, 0);
  } finally {
    overlay?.destroy();
    for (const [key, value] of originals) if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
  }
});

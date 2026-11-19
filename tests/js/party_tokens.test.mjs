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


function dropBoard() {
  const handlers = {}, nodes = new Map();
  const document = {getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, {addEventListener() {}});
    return nodes.get(id);
  }};
  let generation = 1, editable = true, updates = [], files = [];
  let respond = async () => ({ok: true, json: async () => ({tokens: [{id: 'companion:7', name: 'Wolf'}]})});
  const context = vm.createContext({document, crypto: {randomUUID: () => 'uuid'}, AbortSignal,
    restoreElements: elements => elements, CaptureUpdateAction: {IMMEDIATELY: 'now'},
    fetch: (...args) => respond(...args)});
  vm.runInContext(source + `
    tokenPortrait = async () => ({file: {id: 'portrait', dataURL: 'png'}, fallback: false});
    this.setup = setupPartyTokens;`, context);
  const api = {getAppState: () => ({width: 1000, height: 600, offsetLeft: 100, offsetTop: 50,
    zoom: {value: 2}, scrollX: -20, scrollY: 30}), getSceneElements: () => [],
    addFiles: added => files.push(...added), updateScene: update => updates.push(update), setActiveTool() {}, setToast() {}};
  context.setup({editor: {addEventListener: (event, fn) => handlers[event] = fn},
    config: {tokensUrl: '/tokens', messages: {}}, getApi: () => api,
    getGeneration: () => generation, canInsert: () => editable, beforeInsert() {}});
  const event = (id = 'companion:7') => ({clientX: 500, clientY: 250,
    dataTransfer: {types: ['application/x-kettlewright-actor'], getData: () => id},
    preventDefault() {}, stopPropagation() {}});
  return {handlers, updates, files, event, setGeneration: value => generation = value,
    setEditable: value => editable = value, respond: fn => respond = fn};
}
test('dropping a companion creates a linked token at the drop position', async () => {
  const board = dropBoard();
  await board.handlers.drop(board.event());
  const element = board.updates[0].elements[0];
  assert.equal(element.id, 'actor-companion-7-uuid');
  assert.equal(element.fileId, board.files[0].id);
  assert.equal(element.x, 180); assert.equal(element.y, 30);
  assert.equal(board.updates[0].captureUpdate, 'now');
});
test('unknown actors and view-only boards cannot insert dropped tokens', async () => {
  const board = dropBoard();
  await board.handlers.drop(board.event('999'));
  board.setEditable(false);
  await board.handlers.drop(board.event());
  assert.equal(board.updates.length, 0);
});
test('board replacement while loading a dropped token cancels insertion', async () => {
  const board = dropBoard();
  board.respond(async () => {board.setGeneration(2); return {ok: true,
    json: async () => ({tokens: [{id: 'companion:7', name: 'Wolf'}]})};});
  await board.handlers.drop(board.event());
  assert.equal(board.updates.length, 0);
});

// The Tokens panel, with portraits that can be dragged onto the board (#457).
function picker() {
  const handlers = {}, timers = [], fetches = [];
  class Node {
    constructor() {this.children = []; this.listeners = {}; this.dataset = {}; this.attributes = {};}
    append(...nodes) {this.children.push(...nodes);}
    replaceChildren(...nodes) {this.children = nodes;}
    addEventListener(name, fn) {this.listeners[name] = fn;}
    setAttribute(name, value) {this.attributes[name] = value;}
    removeAttribute(name) {delete this.attributes[name];}
  }
  const nodes = new Map();
  const node = id => {if (!nodes.has(id)) nodes.set(id, new Node()); return nodes.get(id);};
  const dialog = Object.assign(node('party-tokens'), {open: false, modal: false,
    showModal() {this.open = true; this.modal = true;}, close() {this.open = false; this.modal = false;}});
  const updates = [];
  const context = vm.createContext({document: {getElementById: node, createElement: () => new Node()},
    crypto: {randomUUID: () => 'uuid'}, AbortSignal, setTimeout: fn => timers.push(fn),
    restoreElements: elements => elements, CaptureUpdateAction: {IMMEDIATELY: 'now'},
    fetch: async url => {fetches.push(url); return {ok: true, json: async () => ({tokens: [{id: '3', name: 'Ada', kind: 'character'}]})};}});
  vm.runInContext(source + `
    tokenPortrait = async () => ({file: {id: 'portrait', dataURL: 'png'}, fallback: false});
    this.setup = setupPartyTokens;`, context);
  const api = {getAppState: () => ({width: 1000, height: 600, offsetLeft: 0, offsetTop: 0, zoom: {value: 1}, scrollX: 0, scrollY: 0}),
    getSceneElements: () => [], addFiles() {}, updateScene: update => updates.push(update), setActiveTool() {}, setToast() {}};
  const tokens = context.setup({editor: {addEventListener: (event, fn) => handlers[event] = fn},
    config: {tokensUrl: '/tokens', messages: {}}, getApi: () => api, getGeneration: () => 1,
    canInsert: () => true, beforeInsert() {}});
  const data = {};
  const dataTransfer = {get types() {return Object.keys(data);}, setData: (key, value) => {data[key] = value;},
    getData: key => data[key]};
  return {tokens, handlers, dialog, timers, fetches, updates, dataTransfer,
    button: () => node('tokens-grid').children[0],
    drop: (x, y) => handlers.drop({clientX: x, clientY: y, dataTransfer, preventDefault() {}, stopPropagation() {}})};
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('a portrait dragged from the Tokens panel is placed where it is dropped (#457)', async () => {
  const p = picker();
  await p.tokens.open(); await settle();
  const button = p.button();
  assert.equal(button.draggable, true);
  button.listeners.dragstart({dataTransfer: p.dataTransfer, preventDefault() {}});
  assert.equal(p.dataTransfer.getData('application/x-kettlewright-actor'), '3');
  assert.equal(p.dialog.open, true, 'the panel stays put until the drag has started');
  p.timers.splice(0).forEach(fn => fn());
  assert.equal(p.dialog.open, false, 'then steps aside so the board can take the drop');
  const fetched = p.fetches.length;
  await p.drop(300, 200);
  button.listeners.dragend();
  const element = p.updates[0].elements[0];
  assert.equal(element.id, 'actor-3-uuid');
  assert.equal(element.x, 260); assert.equal(element.y, 160);
  assert.equal(p.fetches.length, fetched, 'the drop reuses the portrait the panel already made');
  assert.equal(p.dialog.open, false);
});

test('a drag that does not end on the board brings the Tokens panel back', async () => {
  const p = picker();
  await p.tokens.open(); await settle();
  p.button().listeners.dragstart({dataTransfer: p.dataTransfer, preventDefault() {}});
  p.timers.splice(0).forEach(fn => fn());
  p.button().listeners.dragend();
  assert.equal(p.dialog.open, true); assert.equal(p.dialog.modal, true);
  assert.equal(p.updates.length, 0);
  // Clicking still adds a token in the middle of the view.
  await p.button().listeners.click(); await settle();
  assert.equal(p.updates[0].elements[0].x, 460);
  assert.equal(p.dialog.open, false);
});

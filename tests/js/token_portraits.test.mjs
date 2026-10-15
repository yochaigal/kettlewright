import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {actorKey} from '../../app/static/src/js/maps/token_stats.js';

const source = readFileSync(new URL('../../app/static/src/js/maps/token_portraits.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));

async function setup() {
  const frames = [], events = {}, updates = [], renders = [];
  let actors = [{id: '1', name: 'Ada', portrait: '/new.png'}], fail = false;
  let elements = [
    {id: 'actor-1-copy', type: 'image', fileId: 'old', x: 20, y: 40, width: 80, height: 120, angle: .5, locked: true, version: 7},
    {id: 'actor-companion-2-copy', type: 'image', fileId: 'old', x: 100},
    {id: 'background', type: 'image', fileId: 'old'},
  ];
  const files = {old: {id: 'old', dataURL: 'old png'}};
  const api = {getSceneElements: () => elements, addFiles(added) {for (const file of added) files[file.id] = file;},
    updateScene(update) {elements = update.elements; updates.push(update);}};
  const context = vm.createContext({actorKey, CaptureUpdateAction: {NEVER: 'never'}, AbortSignal,
    requestAnimationFrame: fn => {frames.push(fn); return frames.length;}, cancelAnimationFrame() {},
    setInterval() {}, clearInterval() {}, document: {addEventListener() {}, removeEventListener() {}},
    fetch: async () => ({ok: true, json: async () => ({portraits: structuredClone(actors)})})});
  vm.runInContext(source + '\nthis.create = createTokenPortraits;', context);
  const overlay = context.create({config: {partyId: 1, portraitsUrl: '/portraits'}, getApi: () => api,
    socket: {on(name, fn) {events[name] = fn;}, off() {}}, onProjection: fn => fn(),
    renderPortrait: async actor => {renders.push(actor); return {imageLoaded: !fail, file: {id: actor.portrait, dataURL: actor.portrait}};}});
  const draw = () => frames.splice(0).forEach(fn => fn());
  await tick(); draw();
  return {overlay, updates, renders, files, events, draw, get elements() {return elements;},
    setActors(value) {actors = value;}, setElements(value) {elements = value;}, setFail(value) {fail = value;}};
}

test('reload projects the latest portrait without changing geometry, locks, versions or saved image IDs', async () => {
  const board = await setup();
  try {
    const token = board.elements[0];
    assert.equal(token.fileId, 'live-old-/new.png');
    assert.equal(token.locked, true); assert.equal(token.version, 7);
    assert.equal(token.x, 20); assert.equal(token.angle, .5); assert.equal(token.height, 120);
    assert.equal(board.elements[1].fileId, 'old'); assert.equal(board.elements[2].fileId, 'old');
    assert.equal(board.updates[0].captureUpdate, 'never');
    assert.equal(board.overlay.elements(board.elements)[0].fileId, 'old');
    assert.equal(board.files.old.dataURL, 'old png');
    board.overlay.redraw(); board.draw();
    assert.equal(board.updates.length, 1);
  } finally {board.overlay.destroy();}
});

test('portrait changes update every copy and preserve edits while image loading', async () => {
  const board = await setup();
  try {
    board.setElements([...board.elements, {...board.elements[0], id: 'actor-1-second', x: 300}]);
    board.setActors([{id: '1', name: 'Ada', portrait: '/latest.png'}]);
    board.events.party_actors_changed({party_id: 1});
    board.elements[0].x = 45;
    await tick(); board.draw();
    assert.equal(board.elements[0].fileId, 'live-old-/latest.png');
    assert.equal(board.elements[3].fileId, board.elements[0].fileId);
    assert.equal(board.elements[0].x, 45); assert.equal(board.elements[3].x, 300);
    assert.equal(board.overlay.elements(board.elements)[0].fileId, 'old');
    board.events.party_actors_changed({party_id: 1}); await tick(); board.draw();
    assert.equal(board.renders.length, 2);
    // Applying a remote canonical scene must restore the live artwork next frame.
    board.setElements(board.overlay.elements(board.elements));
    board.overlay.redraw(); board.draw();
    assert.equal(board.elements[0].fileId, 'live-old-/latest.png');
  } finally {board.overlay.destroy();}
});

test('failed image loads keep the current artwork and can retry; destroyed boards never update', async () => {
  const board = await setup();
  board.setActors([{id: '1', name: 'Ada', portrait: '/broken.png'}]); board.setFail(true);
  board.events.party_actors_changed({party_id: 1}); await tick(); board.draw();
  assert.equal(board.elements[0].fileId, 'live-old-/new.png');
  board.setFail(false); board.events.party_actors_changed({party_id: 1}); await tick(); board.draw();
  assert.equal(board.elements[0].fileId, 'live-old-/broken.png');
  const count = board.updates.length;
  board.setActors([{id: '1', name: 'Ada', portrait: '/later.png'}]);
  board.events.party_actors_changed({party_id: 1}); board.overlay.destroy(); await tick(); board.draw();
  assert.equal(board.updates.length, count);
});

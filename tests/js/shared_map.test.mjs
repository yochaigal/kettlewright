import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../../app/static/src/js/maps/shared_map.js', import.meta.url), 'utf8').replace(/^import .*;\n/gm, '');
const librarySource = readFileSync(new URL('../../app/static/src/js/maps/libraries.js', import.meta.url), 'utf8')
  .replace(/^export /gm, '').replace('import.meta.url', 'location.href');
const mergeSource = readFileSync(new URL('../../app/static/src/js/maps/shared_map_merge.js', import.meta.url), 'utf8').replace(/^export /gm, '');
const updatesSource = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_updates.js', import.meta.url), 'utf8').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));
const empty = {elements: [], files: {}};
const response = (body, status = 200) => ({ok: status === 200, status, json: async () => body});

async function setup(editing = true, failedLibrary = null) {
  const requests = [], libraryRequests = [], handlers = {}, windowHandlers = {}, intervals = [], drafts = [], timers = new Map();
  let nextTimer = 0, props, elements = [], files = {}, appState = {viewBackgroundColor: '#ffffff', theme: 'light'};
  const config = {editing, partyId: 1, sceneUrl: '/scene', libraryUrl: '/libraries/', messages: Object.fromEntries(
    ['saved', 'live', 'saving', 'conflict', 'denied', 'invalid', 'failed', 'offline', 'loadFailed', 'draft'].map(key => [key, key]))};
  const stored = new Map(), uiHandlers = {};
  const status = {textContent: ''};
  const api = {
    setToast() {}, scrollToContent() {}, history: {clear() {}}, addFiles(value) {for (const file of value) files[file.id] = file;},
    getSceneElements: () => elements, getFiles: () => files, getAppState: () => appState,
    updateScene(data) {if (data.elements) elements = data.elements; Object.assign(appState, data.appState); props.onChange(elements, appState, files);},
  };
  const context = vm.createContext({
    document: {body: {classList: {toggle() {}}}, createElement: () => ({}), getElementById: id => id === 'shared-map-config' ? {textContent: JSON.stringify(config)} : id === 'map-status' ? status : {addEventListener(name, fn) {uiHandlers[id + ':' + name] = fn;}, setAttribute() {}, append(value) {drafts.push(value);}},
      addEventListener() {}, querySelectorAll: () => []},
    window: {addEventListener(name, fn) {windowHandlers[name] = fn;}},
    localStorage: {getItem: key => stored.get(key) || 'false', setItem: (key, value) => stored.set(key, value)},
    createFogLayer: () => ({redraw() {}, destroy() {}, setState() {}, setTool() {}}),
    applyFogOperation: (fog) => fog, setupMapImport() {}, setupPartyTokens: () => ({open() {}, close() {}}),
    Blob, structuredClone, createLaserSync: () => ({pointerUpdate() {}, stop() {}, clear() {}, destroy() {}}),
    io: () => ({on: (name, handler) => {handlers[name] = handler;}}),
    setTimeout: fn => {timers.set(++nextTimer, fn); return nextTimer;}, clearTimeout: id => timers.delete(id), setInterval(fn, delay) {intervals.push({fn, delay}); return intervals.length;}, clearInterval() {},
    AbortSignal, URL, location: {href: 'https://example.test/map/'}, Excalidraw: {}, CaptureUpdateAction: {NEVER: 'never'},
    restoreElements: elements => elements, drawingFromScene: (elements, files) => ({elements, files}),
    h: (_, value) => value,
    createRoot: () => ({unmount() {}, render(value) {if (!value) return; const first = !props; props = value; if (!first) return; elements = value.initialData.elements;
      files = value.initialData.files; value.excalidrawAPI(api); value.onChange(elements, appState, files);}}),
    fetch: (url, options) => {
      if (url instanceof URL) url = url.pathname;
      if (url.startsWith('/libraries/')) {
        libraryRequests.push(url);
        const name = url.split('/').pop();
        const data = JSON.parse(readFileSync(new URL(`../../app/static/vendor/excalidraw-libraries/${name}`, import.meta.url), 'utf8'));
        return Promise.resolve(response(data, name === failedLibrary ? 503 : 200));
      }
      return new Promise(resolve => requests.push({options, resolve}));
    },
  });
  vm.runInContext(librarySource + '\n' + mergeSource + '\n' + updatesSource + '\n' + source, context);
  requests.shift().resolve(response({version: 0, drawing: empty}));
  await tick();
  return {requests, libraryRequests, handlers, windowHandlers, intervals, drafts, status, stored, uiHandlers, get props() {return props;},
    change(id) {elements = [{id, type: 'rectangle'}]; props.onChange(elements, appState, files);},
    moveInPlace(x) {elements[0].x = x; elements[0].version = (elements[0].version || 1) + 1; props.onChange(elements, appState, files);},
    async timers() {const queued = [...timers.values()]; timers.clear(); queued.forEach(fn => fn()); await tick();},
    elements: () => elements};
}

test('remote changes never trigger writes on a view-only canvas', async () => {
  const state = await setup(false);
  assert.equal(state.props.viewModeEnabled, true);
  assert.equal(state.props.isCollaborating, true);
  assert.equal(state.props.initialData.appState.gridModeEnabled, true);
  state.change('unauthorized');
  await state.timers();
  assert.equal(state.requests.length, 0);
  state.handlers.shared_map_changed({party_id: 1, version: 1});
  state.requests.shift().resolve(response({version: 1, drawing: {elements: [{id: 'remote'}], files: {}}}));
  await tick();
  await state.timers();
  assert.equal(state.elements()[0].id, 'remote');
  assert.equal(state.requests.length, 0);
});

test('edits during an in-flight save are queued with the acknowledged revision', async () => {
  const state = await setup();
  state.change('first'); await state.timers();
  const first = state.requests.shift();
  state.change('second'); await state.timers();
  assert.equal(state.requests.length, 0);
  first.resolve(response({version: 1})); await tick(); await state.timers();
  const second = state.requests.shift();
  assert.equal(JSON.parse(second.options.body).version, 1);
  assert.equal(JSON.parse(second.options.body).drawing.elements[0].id, 'second');
  second.resolve(response({version: 2})); await tick();
  assert.equal(state.status.textContent, 'saved');
});

test('a stale refresh cannot overwrite edits started while it was loading', async () => {
  const state = await setup();
  state.handlers.connect();
  const read = state.requests.shift();
  state.change('local');
  read.resolve(response({version: 2, drawing: empty})); await tick();
  assert.equal(state.elements()[0].id, 'local');
  await state.timers();
  const save = JSON.parse(state.requests.shift().options.body);
  assert.equal(save.version, 2);
  assert.equal(save.drawing.elements[0].id, 'local');
});

test('concurrent edits rebase against the latest scene and retry without reload', async () => {
  const state = await setup();
  assert.equal(state.props.viewModeEnabled, false);
  state.change('local'); await state.timers();
  state.requests.shift().resolve(response({}, 409)); await tick();
  const refresh = state.requests.shift();
  assert.equal(refresh.options.method, undefined);
  state.change('more'); await state.timers();
  assert.equal(state.requests.length, 0);
  refresh.resolve(response({version: 1, drawing: {elements: [{id: 'remote'}], files: {}}}));
  await tick(); await state.timers();
  const retry = state.requests.shift();
  const payload = JSON.parse(retry.options.body);
  assert.equal(payload.version, 1);
  assert.deepEqual(payload.drawing.elements.map(element => element.id), ['remote', 'more']);
  retry.resolve(response({version: 2})); await tick();
  assert.equal(state.status.textContent, 'saved');
});

test('remote notification during save is fetched after acknowledgement', async () => {
  const state = await setup();
  state.change('local'); await state.timers();
  const save = state.requests.shift();
  state.handlers.shared_map_changed({party_id: 1, version: 2});
  assert.equal(state.requests.length, 0);
  save.resolve(response({version: 1})); await tick();
  state.requests.shift().resolve(response({version: 2, drawing: {elements: [{id: 'local'}, {id: 'remote'}], files: {}}}));
  await tick(); await state.timers();
  assert.deepEqual(Array.from(state.elements(), element => element.id), ['local', 'remote']);
  assert.equal(state.requests.length, 0);
});

test('two simultaneous editors converge without losing either drawing', async () => {
  const warden = await setup();
  const player = await setup();
  warden.change('warden'); player.change('player');
  await warden.timers(); await player.timers();
  const first = warden.requests.shift();
  const stale = player.requests.shift();
  assert.equal(JSON.parse(first.options.body).version, 0);
  assert.equal(JSON.parse(stale.options.body).version, 0);
  const saved = JSON.parse(first.options.body).drawing;
  first.resolve(response({version: 1}));
  stale.resolve(response({}, 409)); await tick();
  player.requests.shift().resolve(response({version: 1, drawing: saved}));
  await tick(); await player.timers();
  const retry = player.requests.shift();
  const merged = JSON.parse(retry.options.body);
  assert.equal(merged.version, 1);
  assert.deepEqual(merged.drawing.elements.map(element => element.id), ['warden', 'player']);
  retry.resolve(response({version: 2})); await tick();
  warden.handlers.shared_map_changed({party_id: 1, version: 2});
  warden.requests.shift().resolve(response({version: 2, drawing: merged.drawing}));
  await tick(); await warden.timers(); await player.timers();
  assert.deepEqual(JSON.parse(JSON.stringify(warden.elements())), JSON.parse(JSON.stringify(player.elements())));
  assert.equal(warden.requests.length + player.requests.length, 0);
  assert.equal(warden.status.textContent, 'saved');
  assert.equal(player.status.textContent, 'saved');
});

test('membership is revalidated even with unsaved work', async () => {
  const state = await setup();
  state.change('local');
  state.handlers.party_members_changed({party_id: 1});
  state.requests.shift().resolve(response({}, 403)); await tick(); await state.timers();
  assert.equal(state.status.textContent, 'denied');
  assert.equal(state.requests.length, 0);
});

test('failed saves retry the latest local drawing', async () => {
  const state = await setup();
  state.change('local'); await state.timers();
  state.requests.shift().resolve(response({}, 503)); await tick();
  state.change('latest'); await state.timers();
  const retry = state.requests.shift();
  assert.equal(JSON.parse(retry.options.body).drawing.elements[0].id, 'latest');
  retry.resolve(response({version: 1})); await tick();
  assert.equal(state.status.textContent, 'saved');
});

test('all starter libraries preload without adding anything to the scene', async () => {
  const state = await setup();
  const items = await state.props.initialData.libraryItems;
  assert.equal(state.libraryRequests.length, 5);
  assert.equal(items.length, 208);
  const tokens = items.filter(item => item.id.startsWith('creature-'));
  assert.equal(tokens.length, 99);
  assert.equal(tokens.flatMap(item => item.elements).length, 355);
  for (const token of tokens) {
    assert.ok(token.elements.length <= 6);
    const ids = new Set(token.elements.map(element => element.id));
    const groups = new Set(token.elements.flatMap(element => element.groupIds));
    assert.equal(groups.size, 1);
    for (const element of token.elements) {
      if (element.containerId) assert.ok(ids.has(element.containerId));
      for (const binding of element.boundElements || []) assert.ok(ids.has(binding.id));
    }
  }
  assert.ok(items.length > tokens.length);
  assert.equal(state.elements().length, 0);
  await state.timers();
  assert.equal(state.requests.length, 0);
});

test('one unavailable library does not prevent the other libraries or canvas loading', async () => {
  const state = await setup(true, 'creatures.excalidrawlib');
  const items = await state.props.initialData.libraryItems;
  assert.ok(items.length > 0);
  assert.equal(items.filter(item => item.id.startsWith('creature-')).length, 0);
  assert.equal(state.status.textContent, 'saved');
  assert.equal(state.elements().length, 0);
});

test('socket outage uses fast HTTP fallback without a false connection warning', async () => {
  const state = await setup();
  state.handlers.disconnect();
  assert.equal(state.intervals.at(-1).delay, 3000);
  assert.equal(state.status.textContent, 'saved');
  state.requests.shift().resolve(response({version: 0, drawing: empty})); await tick();
  assert.equal(state.status.textContent, 'saved');
  state.handlers.connect();
  assert.equal(state.intervals.at(-1).delay, 60000);
  state.requests.shift().resolve(response({}, 503)); await tick();
  assert.equal(state.status.textContent, 'offline');
});

test('replacement archives unsaved work and never merges it into the new board', async () => {
  const state = await setup();
  state.change('old-local');
  state.handlers.shared_map_changed({party_id: 1, version: 1, generation: 2});
  state.requests.shift().resolve(response({generation: 2, version: 1, drawing: {elements: [{id: 'new-map'}], files: {}}}));
  await tick(); await state.timers();
  assert.equal(state.drafts.length, 1);
  assert.equal(state.elements()[0].id, 'new-map');
  assert.equal(state.requests.length, 0);
  state.change('new-local'); await state.timers();
  assert.equal(JSON.parse(state.requests.shift().options.body).generation, 2);
});

test('fog updates disable player export without writing or clearing the drawing', async () => {
  const state = await setup();
  state.handlers.shared_map_changed({party_id: 1, version: 0, fog_version: 1});
  state.requests.shift().resolve(response({generation: 1, version: 0, drawing: empty, fog_version: 1,
    fog: {enabled: true, base: 'covered', strokes: [], applied: []}}));
  await tick(); await state.timers();
  assert.equal(state.props.UIOptions.canvasActions.export, false);
  assert.equal(state.props.UIOptions.canvasActions.saveAsImage, false);
  assert.equal(state.props.viewModeEnabled, false);
  assert.equal(state.requests.length, 0);
});

test('theme changes persist locally and do not trigger scene saves', async () => {
  const state = await setup();
  state.uiHandlers['board-theme:click'](); await state.timers();
  assert.equal(state.stored.get('darkMode'), 'true');
  assert.equal(state.requests.length, 0);
  state.windowHandlers.storage({key: 'darkMode', newValue: 'false'}); await state.timers();
  assert.equal(state.requests.length, 0);
});


test('in-place Excalidraw movement is saved after an acknowledged drawing', async () => {
  const state = await setup();
  state.change('token'); await state.timers();
  state.requests.shift().resolve(response({version: 1})); await tick();
  state.moveInPlace(240); await state.timers();
  assert.equal(state.requests.length, 1, 'moving an existing element must enqueue a scene save');
  const request = state.requests.shift();
  assert.equal(JSON.parse(request.options.body).drawing.elements[0].x, 240);
  request.resolve(response({version: 2})); await tick();
});

test('in-place movement of a received element survives a concurrent remote update', async () => {
  const state = await setup();
  state.handlers.shared_map_changed({party_id: 1, version: 1});
  state.requests.shift().resolve(response({version: 1, drawing: {elements: [{id: 'token', type: 'image', x: 0, version: 1}], files: {}}}));
  await tick();
  state.moveInPlace(240);
  state.handlers.shared_map_changed({party_id: 1, version: 2});
  state.requests.shift().resolve(response({version: 2, drawing: {elements: [{id: 'token', type: 'image', x: 0, version: 1}, {id: 'remote', type: 'rectangle'}], files: {}}}));
  await tick(); await state.timers();
  assert.equal(state.elements().find(e => e.id === 'token').x, 240);
  assert.ok(state.elements().some(e => e.id === 'remote'));
  assert.equal(JSON.parse(state.requests.shift().options.body).drawing.elements[0].x, 240);
});


const deltaEvent = (version, elements, extra = {}) => ({party_id: 1, generation: 1, version, fog_version: 0,
  update: {drawing: {base_version: version - 1, elements, order: elements.map(e => e.id), files: {}, appState: {viewBackgroundColor: '#ffffff'}}}, ...extra});

test('socket drawing and fog updates apply without a scene GET or echo POST', async () => {
  const s = await setup();
  s.handlers.shared_map_changed(deltaEvent(1, [{id: 'token', type: 'rectangle', x: 40}]));
  assert.equal(s.elements()[0].x, 40);
  s.handlers.shared_map_changed({party_id: 1, generation: 1, version: 1, fog_version: 1,
    update: {fog: {enabled: true, base: 'covered', strokes: [], applied: []}}});
  assert.equal(s.props.UIOptions.canvasActions.export, false);
  await s.timers(); assert.equal(s.requests.length, 0);
});

test('socket updates wait for an in-flight POST then apply without GET', async () => {
  const s = await setup(); s.change('local'); await s.timers(); const save = s.requests.shift();
  s.handlers.shared_map_changed(deltaEvent(1, [{id: 'local', type: 'rectangle'}]));
  s.handlers.shared_map_changed(deltaEvent(2, [{id: 'local', type: 'rectangle'}, {id: 'remote', type: 'ellipse'}]));
  assert.equal(s.requests.length, 0);
  save.resolve(response({version: 1})); await tick(); await s.timers();
  assert.equal(s.elements().length, 2); assert.equal(s.requests.length, 0);
});

test('a missing socket base revision triggers an HTTP recovery', async () => {
  const s = await setup(); s.handlers.shared_map_changed(deltaEvent(3, [{id: 'remote', type: 'rectangle'}]));
  assert.equal(s.requests.length, 1); assert.equal(s.requests[0].options.method, undefined);
});

test('socket updates preserve pending local edits and save against the new revision', async () => {
  const s = await setup(); s.change('local');
  s.handlers.shared_map_changed(deltaEvent(1, [{id: 'remote', type: 'rectangle'}]));
  assert.equal(s.elements().length, 2); await s.timers();
  assert.equal(s.requests.length, 1);
  const data = JSON.parse(s.requests[0].options.body); assert.equal(data.version, 1);
  assert.equal(data.drawing.elements.length, 2);
});

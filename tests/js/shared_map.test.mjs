import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../../app/static/src/js/maps/shared_map.js', import.meta.url), 'utf8').replace(/^import .*;\n/gm, '');
const librarySource = readFileSync(new URL('../../app/static/src/js/maps/libraries.js', import.meta.url), 'utf8')
  .replace(/^export /gm, '').replace('import.meta.url', 'location.href');
const tick = () => new Promise(resolve => setImmediate(resolve));
const empty = {elements: [], files: {}};
const response = (body, status = 200) => ({ok: status === 200, status, json: async () => body});

async function setup(editing = true, failedLibrary = null) {
  const requests = [], libraryRequests = [], handlers = {}, timers = new Map();
  let nextTimer = 0, props, elements = [], files = {}, appState = {viewBackgroundColor: '#ffffff'};
  const config = {editing, partyId: 1, sceneUrl: '/scene', libraryUrl: '/libraries/', messages: Object.fromEntries(
    ['saved', 'live', 'saving', 'conflict', 'denied', 'invalid', 'failed'].map(key => [key, key]))};
  const status = {textContent: ''};
  const api = {
    setToast() {}, scrollToContent() {}, history: {clear() {}}, addFiles(value) {for (const file of value) files[file.id] = file;},
    getSceneElements: () => elements, getFiles: () => files, getAppState: () => appState,
    updateScene(data) {elements = data.elements; Object.assign(appState, data.appState); props.onChange(elements, appState, files);},
  };
  const context = vm.createContext({
    document: {getElementById: id => id === 'shared-map-config' ? {textContent: JSON.stringify(config)} : id === 'map-status' ? status : {addEventListener() {}},
      addEventListener() {}, querySelectorAll: () => []},
    window: {addEventListener() {}},
    io: () => ({on: (name, handler) => {handlers[name] = handler;}}),
    setTimeout: fn => {timers.set(++nextTimer, fn); return nextTimer;}, clearTimeout: id => timers.delete(id), setInterval() {},
    AbortSignal, URL, location: {href: 'https://example.test/map/'}, Excalidraw: {}, CaptureUpdateAction: {NEVER: 'never'},
    restoreElements: elements => elements, drawingFromScene: (elements, files) => ({elements, files}),
    h: (_, value) => value,
    createRoot: () => ({unmount() {}, render(value) {if (!value) return; props = value; elements = value.initialData.elements;
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
  vm.runInContext(librarySource + '\n' + source, context);
  requests.shift().resolve(response({version: 0, drawing: empty}));
  await tick();
  return {requests, libraryRequests, handlers, status, props,
    change(id) {elements = [{id, type: 'rectangle'}]; props.onChange(elements, appState, files);},
    async timers() {const queued = [...timers.values()]; timers.clear(); queued.forEach(fn => fn()); await tick();},
    elements: () => elements};
}

test('players are read-only and remote changes never trigger writes', async () => {
  const state = await setup(false);
  assert.equal(state.props.viewModeEnabled, true);
  assert.equal(state.props.isCollaborating, false);
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
  assert.equal(JSON.parse(state.requests.shift().options.body).version, 0);
});

test('conflict preserves local work and blocks automatic overwrite', async () => {
  const state = await setup();
  state.change('local'); await state.timers();
  state.requests.shift().resolve(response({}, 409)); await tick();
  state.change('more'); await state.timers();
  state.handlers.connect();
  assert.equal(state.requests.length, 0);
  assert.equal(state.status.textContent, 'conflict');
  assert.equal(state.elements()[0].id, 'more');
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

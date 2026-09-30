import {createElement as h} from 'react';
import {createRoot} from 'react-dom/client';
import {Excalidraw, restoreElements, CaptureUpdateAction} from 'excalidraw';
import {drawingFromScene} from './scene.js';
import {mergeDrawings, sameDrawing} from './shared_map_merge.js';
import {loadLibraries, MAP_LIBRARIES} from './libraries.js';

const config = JSON.parse(document.getElementById('shared-map-config').textContent);
const editor = document.getElementById('editor');
const root = createRoot(editor);
const status = document.getElementById('map-status');
const tell = key => {status.textContent = config.messages[key];};
const snapshot = (elements, files, appState) => ({...drawingFromScene(elements, files),
  appState: {viewBackgroundColor: appState.viewBackgroundColor || '#ffffff'}});
let api, version = -1, initialized = false, applying = false, stopped = false;
let pending = null, saving = false, loading = false, refreshAgain = false, timer;
let lastDrawing = null, saveBlocked = false;
let libraryLoadFailed = false;
let baseDrawing = null;

// Library assets load alongside the scene, without delaying or populating it.
const defaultLibraryItems = config.editing
  ? loadLibraries([...MAP_LIBRARIES, 'clocks'], new URL(config.libraryUrl, location.href)).then(result => {
    libraryLoadFailed = result.failed;
    return result.items;
  })
  : [];
const socket = io();

function revoke() {
  stopped = true;
  pending = null;
  clearTimeout(timer);
  root.unmount();
  api = null;
  tell('denied');
}

function scheduleSave(delay = 180) {
  if (!timer && !stopped && !saveBlocked) timer = setTimeout(() => {timer = null; save();}, delay);
}

async function save() {
  if (!pending || saving || loading || stopped || saveBlocked) return;
  const drawing = pending;
  pending = null;
  saving = true;
  tell('saving');
  try {
    const response = await fetch(config.sceneUrl, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({drawing, version, csrf_token: config.csrfToken}),
      signal: AbortSignal.timeout(15000),
    });
    if (response.redirected || [401, 403, 404].includes(response.status)) {revoke(); return;}
    if (response.status === 409) {
      pending ||= drawing;
      refreshAgain = true;
      tell('conflict');
      return;
    }
    if (response.status === 400 || response.status === 413) {
      pending ||= drawing;
      saveBlocked = true;
      tell('invalid');
      return;
    }
    if (!response.ok) throw new Error('Save failed');
    version = (await response.json()).version;
    baseDrawing = drawing;
    tell('saved');
  } catch (_) {
    pending ||= drawing;
    tell('failed');
    scheduleSave(2500);
  } finally {
    saving = false;
    if (refreshAgain) {refreshAgain = false; refresh();}
    else if (pending) scheduleSave();
  }
}

function onChange(elements, appState, files) {
  if (!api || stopped || applying || appState.isLoading) return;
  const drawing = snapshot(elements, files, appState);
  if (!initialized) {
    initialized = true;
    lastDrawing = drawing;
    baseDrawing = drawing;
    setTimeout(() => {if (!stopped) api?.scrollToContent(undefined, {fitToContent: true});}, 0);
    return;
  }
  if (!config.editing || sameDrawing(drawing, lastDrawing)) return;
  lastDrawing = drawing;
  pending = drawing;
  // Validation failures can be corrected on the canvas.
  if (saveBlocked && status.textContent === config.messages.invalid) saveBlocked = false;
  if (!saveBlocked) {tell('saving'); scheduleSave();}
}

function mount(data) {
  version = data.version;
  root.render(h(Excalidraw, {
    excalidrawAPI: instance => {
      api = instance;
      Promise.resolve(defaultLibraryItems).then(() => {
        if (!stopped && libraryLoadFailed) api?.setToast({message: config.messages.libraryFailed});
      });
    },
    initialData: {elements: restoreElements(data.drawing.elements, null), files: data.drawing.files,
      libraryItems: defaultLibraryItems,
      appState: {...data.drawing.appState, gridModeEnabled: true}},
    viewModeEnabled: !config.editing,
    isCollaborating: true,
    onChange,
    validateEmbeddable: () => false,
    UIOptions: {tools: {image: config.editing}, canvasActions: {
      loadScene: config.editing, saveToActiveFile: false, toggleTheme: true,
    }},
  }));
}

function applyDrawing(drawing) {
  applying = true;
  try {
    const elements = restoreElements(drawing.elements, null);
    // Set the expected snapshot before updateScene's asynchronous onChange.
    lastDrawing = snapshot(elements, drawing.files, drawing.appState || {});
    api.addFiles(Object.values(drawing.files));
    api.updateScene({elements, appState: drawing.appState, captureUpdate: CaptureUpdateAction.NEVER});
    api.history.clear();
  } finally {applying = false;}
}

async function refresh() {
  if (stopped) return;
  if (saving || loading) {refreshAgain = true; return;}
  loading = true;
  let loaded = false;
  try {
    const response = await fetch(config.sceneUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
    if (response.redirected || [401, 403, 404].includes(response.status)) {revoke(); return;}
    if (!response.ok) throw new Error('Load failed');
    const data = await response.json();
    if (stopped) return;
    if (version < 0) mount(data);
    else if (data.version > version && api && initialized) {
      const remote = snapshot(restoreElements(data.drawing.elements, null), data.drawing.files, data.drawing.appState || {});
      const drawing = pending ? mergeDrawings(baseDrawing, pending, remote) : remote;
      baseDrawing = remote;
      version = data.version;
      if (pending) pending = drawing;
      applyDrawing(drawing);
    }
    loaded = true;
    if (!saveBlocked) tell(pending ? 'saving' : config.editing ? 'saved' : 'live');
  } catch (_) {if (!stopped) tell(version < 0 ? 'loadFailed' : 'offline');}
  finally {
    loading = false;
    if (refreshAgain) {refreshAgain = false; refresh();}
    else if (pending) scheduleSave(loaded ? 180 : 2500);
  }
}

socket.on('connect', () => {if (pending) scheduleSave(); else refresh();});
socket.on('disconnect', () => {if (!stopped && !saveBlocked) tell('offline');});
socket.on('shared_map_changed', data => {
  if (data.party_id === config.partyId && data.version > version) refresh();
});
socket.on('party_members_changed', data => {if (data.party_id === config.partyId) refresh();});
// Revalidate membership and recover missed events, including suspended tabs.
setInterval(refresh, 10000);
document.addEventListener('visibilitychange', () => {if (!document.hidden) refresh();});
window.addEventListener('online', () => {if (pending) scheduleSave(); else refresh();});
window.addEventListener('beforeunload', event => {
  if (pending || saving) {event.preventDefault(); event.returnValue = '';}
});
document.getElementById('fit-map').addEventListener('click', () => api?.scrollToContent(undefined, {fitToContent: true}));

refresh();

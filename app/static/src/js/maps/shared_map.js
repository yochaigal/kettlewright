import {createElement as h} from 'react';
import {createRoot} from 'react-dom/client';
import {Excalidraw, restoreElements, CaptureUpdateAction} from 'excalidraw';
import {drawingFromScene} from './scene.js';

const config = JSON.parse(document.getElementById('shared-map-config').textContent);
const editor = document.getElementById('editor');
const root = createRoot(editor);
const status = document.getElementById('map-status');
const tell = key => {status.textContent = config.messages[key];};
const snapshot = (elements, files, appState) => ({...drawingFromScene(elements, files),
  appState: {viewBackgroundColor: appState.viewBackgroundColor || '#ffffff'}});
let api, version = -1, initialized = false, applying = false, stopped = false;
let pending = null, saving = false, loading = false, refreshAgain = false, timer;
let lastDrawing = '', saveBlocked = false;
const libraries = new Map();
let libraryLoadFailed = false;

function loadLibrary(name) {
  if (!libraries.has(name)) {
    const request = fetch(`${config.libraryUrl}${name}.excalidrawlib`, {signal: AbortSignal.timeout(15000)})
      .then(response => {
        if (!response.ok) throw new Error('Library failed');
        return response.json();
      })
      .then(data => data.libraryItems)
      .catch(error => {libraries.delete(name); throw error;});
    libraries.set(name, request);
  }
  return libraries.get(name);
}

// Library assets load alongside the scene, without delaying or populating it.
const defaultLibraryItems = config.editing
  ? Promise.allSettled(['creatures', 'clocks', 'planning'].map(loadLibrary)).then(results => {
    libraryLoadFailed = results.some(result => result.status === 'rejected');
    return results.flatMap(result => result.status === 'fulfilled' ? result.value : []);
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
  if (!pending || saving || stopped || saveBlocked) return;
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
      saveBlocked = true;
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
    tell('saved');
  } catch (_) {
    pending ||= drawing;
    tell('failed');
    scheduleSave(2500);
  } finally {
    saving = false;
    if (pending) scheduleSave();
  }
}

function onChange(elements, appState, files) {
  if (!api || stopped || applying || appState.isLoading) return;
  const drawing = snapshot(elements, files, appState);
  const key = JSON.stringify(drawing);
  if (!initialized) {
    initialized = true;
    lastDrawing = key;
    setTimeout(() => {if (!stopped) api?.scrollToContent(undefined, {fitToContent: true});}, 0);
    return;
  }
  if (!config.editing || key === lastDrawing) return;
  lastDrawing = key;
  pending = drawing;
  // Validation failures can be corrected on the canvas; conflicts require reload.
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
    isCollaborating: false,
    onChange,
    validateEmbeddable: () => false,
    UIOptions: {tools: {image: config.editing}, canvasActions: {
      loadScene: config.editing, saveToActiveFile: false, toggleTheme: true,
    }},
  }));
}

async function refresh() {
  if (stopped || saving || pending || saveBlocked) return;
  if (loading) {refreshAgain = true; return;}
  loading = true;
  try {
    const response = await fetch(config.sceneUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
    if (response.redirected || [401, 403, 404].includes(response.status)) {revoke(); return;}
    if (!response.ok) throw new Error('Load failed');
    const data = await response.json();
    // A fetch started before a local edit must never replace that edit.
    if (stopped || pending || saving || saveBlocked) return;
    if (version < 0) mount(data);
    else if (data.version > version && api && initialized) {
      applying = true;
      try {
        api.addFiles(Object.values(data.drawing.files));
        api.updateScene({elements: restoreElements(data.drawing.elements, null),
          appState: data.drawing.appState, captureUpdate: CaptureUpdateAction.NEVER});
        api.history.clear();
        lastDrawing = JSON.stringify(snapshot(api.getSceneElements(), api.getFiles(),
          {...api.getAppState(), ...data.drawing.appState}));
        version = data.version;
      } finally {applying = false;}
    }
    tell(config.editing ? 'saved' : 'live');
  } catch (_) {if (!stopped) tell(version < 0 ? 'loadFailed' : 'offline');}
  finally {
    loading = false;
    if (refreshAgain) {refreshAgain = false; refresh();}
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

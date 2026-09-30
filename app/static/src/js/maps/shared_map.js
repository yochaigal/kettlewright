import {createElement as h} from 'react';
import {createRoot} from 'react-dom/client';
import {Excalidraw, restoreElements, CaptureUpdateAction} from 'excalidraw';
import {drawingFromScene} from './scene.js';
import {mergeDrawings, sameDrawing} from './shared_map_merge.js';
import {loadLibraries, MAP_LIBRARIES} from './libraries.js';
import {createFogLayer, applyFogOperation} from './whiteboard_fog.js';
import {setupMapImport} from './whiteboard_import.js';
import {setupPartyTokens} from './party_tokens.js';
import {createLaserSync} from './whiteboard_laser.js';
import {stateFromUpdate} from './whiteboard_updates.js';

const config = JSON.parse(document.getElementById('shared-map-config').textContent);
const editor = document.getElementById('editor'), root = createRoot(editor);
const status = document.getElementById('map-status');
const tell = key => {status.textContent = config.messages[key];};
// Excalidraw mutates existing elements in place while dragging/resizing.
// Keep acknowledgements and queued saves detached from those live objects.
const snapshot = (elements, files, appState) => structuredClone({...drawingFromScene(elements, files),
  appState: {viewBackgroundColor: appState.viewBackgroundColor || '#ffffff'}});
let api, props, version = -1, generation = 1, initialized = false, applying = false, stopped = false;
let pending = null, saving = false, loading = false, importing = false, refreshAgain = false, timer, poll;
let lastDrawing = null, baseDrawing = null, saveBlocked = false, saveFailed = false, readFailed = false;
let fog = {enabled: false, base: 'covered', strokes: [], applied: []}, fogVersion = 0;
let fogQueue = [], fogSaving = false, fogBlocked = false, fogTimer, fogFailed = false;
let playerPreview = false, theme = 'light', connected = false;
let socketUpdates = [];
try {theme = localStorage.getItem('darkMode') === 'true' ? 'dark' : 'light';} catch (_) {}
document.body.classList.toggle('dark-mode', theme === 'dark');
const layer = createFogLayer({editor, getApi: () => api, warden: config.warden, onOperation: queueFog});
const library = loadLibraries([...MAP_LIBRARIES, 'clocks'], new URL(config.libraryUrl, location.href));
// Match the app's existing Socket.IO transport. HTTP polling below is the fallback.
const socket = io({transports: ['websocket'], reconnectionDelay: 1000, reconnectionDelayMax: 10000});

const laser = createLaserSync({socket, getApi: () => api, getGeneration: () => generation, config,
  canSend: () => initialized && !stopped && !importing});
editor.addEventListener('pointerleave', () => laser.stop());
window.addEventListener('blur', () => laser.stop());

const tokens = setupPartyTokens({config, getApi: () => api, getGeneration: () => generation,
  canInsert: () => config.editing && initialized && !stopped && !importing && !playerPreview,
  beforeInsert: () => {layer.setTool(''); document.querySelectorAll('[data-fog-tool]').forEach(button => button.setAttribute('aria-pressed', 'false'));}});

function showStatus() {
  if (stopped) {tell('denied'); return;}
  tell(saveBlocked ? 'invalid' : saveFailed ? 'failed' : readFailed ? 'offline'
    : pending || saving || importing ? 'saving' : 'saved');
  const fogStatus = document.getElementById('fog-status');
  if (fogStatus) fogStatus.textContent = config.messages[fogBlocked ? 'fogInvalid' : fogFailed ? 'fogFailed'
    : fogQueue.length || fogSaving ? 'saving' : ''] || '';
  const discard = document.getElementById('discard-fog');
  if (discard) discard.hidden = !fogBlocked;
}

function renderEditor() {
  if (!props || stopped) return;
  root.render(h(Excalidraw, {...props,
    renderTopRightUI: () => h('button', {type: 'button', className: 'party-tokens-button',
      disabled: !config.editing || playerPreview || importing, onClick: tokens.open}, config.messages.tokens),
    viewModeEnabled: !config.editing || playerPreview || importing,
    UIOptions: {tools: {image: config.editing}, canvasActions: {
      loadScene: config.editing, saveToActiveFile: false, toggleTheme: true,
      export: !config.warden && fog.enabled || playerPreview ? false : {saveFileToDisk: true},
      saveAsImage: !((!config.warden && fog.enabled) || playerPreview),
    }},
  }));
}

function setTheme(value, persist = true) {
  if (!['light', 'dark'].includes(value) || value === theme) return;
  theme = value; document.body.classList.toggle('dark-mode', theme === 'dark');
  if (persist) {try {localStorage.setItem('darkMode', String(theme === 'dark'));} catch (_) {}}
  if (api && api.getAppState().theme !== value) api.updateScene({appState: {theme: value}, captureUpdate: CaptureUpdateAction.NEVER});
}

function revoke() {
  stopped = true; pending = null; fogQueue = [];
  clearTimeout(timer); clearTimeout(fogTimer); clearInterval(poll);
  tokens.close(); laser.destroy(); layer.destroy(); root.unmount(); api = null; tell('denied');
}
function denied(response) {
  if (response.redirected || [401, 403, 404].includes(response.status)) {revoke(); return true;}
  return false;
}
function post(url, body) {
  return fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({...body, csrf_token: config.csrfToken}), signal: AbortSignal.timeout(15000)});
}
function scheduleSave(delay = 180) {
  if (!timer && !stopped && !saveBlocked) timer = setTimeout(() => {timer = null; save();}, delay);
}
async function save() {
  if (!pending || saving || loading || importing || stopped || saveBlocked) return;
  const drawing = pending, sentGeneration = generation;
  pending = null; saving = true; showStatus();
  try {
    const response = await post(config.sceneUrl, {drawing, version, generation: sentGeneration});
    if (denied(response)) return;
    if (response.status === 409) {pending ||= drawing; refreshAgain = true; return;}
    if ([400, 413].includes(response.status)) {pending ||= drawing; saveBlocked = true; return;}
    if (!response.ok) throw new Error();
    version = (await response.json()).version; baseDrawing = drawing; saveFailed = false;
  } catch (_) {pending ||= drawing; saveFailed = true; scheduleSave(2500);}
  finally {
    saving = false; drainUpdates(); showStatus();
    if (refreshAgain) {refreshAgain = false; refresh();} else if (pending) scheduleSave();
  }
}

function onChange(elements, appState, files) {
  layer.redraw();
  if (stopped || appState.isLoading) return;
  setTheme(appState.theme);
  if (appState.activeTool?.type !== 'laser') laser.stop();
  else document.querySelectorAll('[data-fog-tool][aria-pressed="true"]').forEach(button => {
    button.setAttribute('aria-pressed', 'false'); layer.setTool('');
  });
  if (!api || applying) return;
  const drawing = snapshot(elements, files, appState);
  if (!initialized) {
    initialized = true; lastDrawing = baseDrawing = drawing;
    setTimeout(() => {
      if (stopped) return;
      api?.scrollToContent(undefined, {fitToContent: true}); drainUpdates();
      if (refreshAgain && !saving && !loading) {refreshAgain = false; refresh();}
    }, 0);
    return;
  }
  if (!config.editing || playerPreview || importing || sameDrawing(drawing, lastDrawing)) return;
  lastDrawing = drawing; pending = drawing; saveBlocked = false;
  showStatus(); scheduleSave();
}

function mount(data) {
  version = data.version; generation = data.generation || 1;
  props = {
    excalidrawAPI: instance => {api = instance; layer.redraw();},
    initialData: {elements: restoreElements(data.drawing.elements, null), files: data.drawing.files,
      libraryItems: library.then(result => result.items),
      appState: {...data.drawing.appState, theme, gridModeEnabled: true}},
    isCollaborating: true, onChange, onPointerUpdate: laser.pointerUpdate, validateEmbeddable: () => false,
  };
  renderEditor();
  library.then(result => {if (!stopped && result.failed) api?.setToast({message: config.messages.libraryFailed});});
}
function applyDrawing(drawing) {
  applying = true;
  try {
    const elements = restoreElements(structuredClone(drawing.elements), null);
    lastDrawing = snapshot(elements, drawing.files, drawing.appState || {});
    api.addFiles(structuredClone(Object.values(drawing.files)));
    api.updateScene({elements, appState: drawing.appState, captureUpdate: CaptureUpdateAction.NEVER});
    api.history.clear();
  } finally {applying = false; layer.redraw();}
}
function preserveDraft() {
  if (!pending && !fogQueue.length) return;
  const data = {type: 'excalidraw', version: 2, source: location.origin,
    ...(pending || lastDrawing), whiteboardFog: fogQueue.reduce(applyFogOperation, fog)};
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([JSON.stringify(data)], {type: 'application/json'}));
  link.download = `whiteboard-draft-${generation}.excalidraw`; link.textContent = config.messages.draft;
  document.getElementById('board-notices').append(link);
}
function displayFog() {
  layer.setState(fogQueue.reduce(applyFogOperation, fog));
  document.getElementById('fog-enabled')?.setAttribute('aria-pressed', String(fog.enabled));
  document.querySelectorAll('[data-fog-tool]').forEach(button => {button.disabled = !fog.enabled || playerPreview;});
  renderEditor(); showStatus();
}
function acceptState(data) {
  const nextGeneration = data.generation || 1;
  if (nextGeneration < generation) return;
  if (version >= 0 && nextGeneration !== generation) {
    tokens.close(); laser.clear(); preserveDraft(); pending = null; fogQueue = []; saveBlocked = fogBlocked = saveFailed = fogFailed = false;
    clearTimeout(timer); timer = null; clearTimeout(fogTimer); fogTimer = null;
    layer.setTool(''); document.querySelectorAll('[data-fog-tool]').forEach(button => button.setAttribute('aria-pressed', 'false'));
    generation = nextGeneration; version = data.version; fogVersion = -1;
    applyDrawing(data.drawing); baseDrawing = lastDrawing;
    api?.setToast({message: config.messages.replaced});
  } else if (version < 0) mount(data);
  else if (data.version > version && api && initialized) {
    const remote = snapshot(restoreElements(data.drawing.elements, null), data.drawing.files, data.drawing.appState || {});
    const drawing = pending ? mergeDrawings(baseDrawing, pending, remote) : remote;
    baseDrawing = remote; version = data.version;
    if (pending) pending = drawing;
    applyDrawing(drawing);
  }
  if (data.fog && data.fog_version >= fogVersion) {
    fog = data.fog; fogVersion = data.fog_version;
    fogQueue = fogQueue.filter(operation => !fog.applied.includes(operation.id));
    displayFog();
  }
}
async function refresh() {
  if (stopped) return;
  if (saving || loading || importing) {refreshAgain = true; return;}
  loading = true;
  try {
    const response = await fetch(config.sceneUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
    if (denied(response)) return;
    if (!response.ok) throw new Error();
    const data = await response.json();
    if (!stopped) {acceptState(data); readFailed = false;}
  } catch (_) {readFailed = true; if (version < 0 && !stopped) tell('loadFailed');}
  finally {
    loading = false; drainUpdates(); if (version >= 0) showStatus();
    if (refreshAgain) {refreshAgain = false; refresh();}
    else {if (pending) scheduleSave(readFailed ? 2500 : 180); scheduleFog();}
  }
}
function scheduleFog(delay = 180) {
  if (!fogTimer && fogQueue.length && !stopped && !fogBlocked) fogTimer = setTimeout(() => {fogTimer = null; saveFog();}, delay);
}
function queueFog(operation) {
  if (!config.warden || stopped || playerPreview || importing || version < 0) return;
  fogQueue.push({...operation, id: operation.id || crypto.randomUUID()}); displayFog(); scheduleFog();
}
async function saveFog() {
  if (!fogQueue.length || fogSaving || loading || importing || fogBlocked || stopped) return;
  fogSaving = true; const operation = fogQueue[0], sentGeneration = generation;
  try {
    const response = await post(config.fogUrl, {operation, generation: sentGeneration, fog_version: fogVersion});
    if (denied(response)) return;
    if (response.status === 409) {await refresh(); return;}
    if ([400, 413].includes(response.status)) {fogBlocked = true; return;}
    if (!response.ok) throw new Error();
    const data = await response.json();
    if (generation !== sentGeneration) return;
    fogQueue = fogQueue.filter(item => item.id !== operation.id);
    if (data.fog_version >= fogVersion) {fog = data.fog; fogVersion = data.fog_version;}
    fogFailed = false; displayFog();
  } catch (_) {fogFailed = true; scheduleFog(2500);}
  finally {fogSaving = false; showStatus(); scheduleFog();}
}

function drainUpdates() {
  if (saving || loading || importing || !api || !initialized || stopped) return;
  const queued = socketUpdates; socketUpdates = [];
  for (const event of queued) {
    const state = stateFromUpdate(event, {drawing: baseDrawing, version, generation, fog, fog_version: fogVersion});
    if (!state) {refreshAgain = true; break;}
    acceptState(state);
  }
  if (pending) scheduleSave();
}
function receiveUpdate(data) {
  if (data.party_id !== config.partyId || stopped) return;
  if (!(data.version > version || data.generation > generation || data.fog_version > fogVersion)) return;
  if (!data.update) {refresh(); return;} // Rolling upgrade from an older server.
  if (socketUpdates.length >= 100) {socketUpdates = []; refreshAgain = true;}
  else socketUpdates.push(data);
  drainUpdates();
  if (refreshAgain && !saving && !loading && !importing) {refreshAgain = false; refresh();}
}
function polling() {clearInterval(poll); poll = setInterval(refresh, connected ? 60000 : 3000);}
socket.on('connect', () => {connected = true; polling(); refresh();});
socket.on('disconnect', () => {connected = false; polling(); refresh();});
socket.on('shared_map_changed', receiveUpdate);
socket.on('party_members_changed', data => {if (data.party_id === config.partyId) refresh();});
document.addEventListener('visibilitychange', () => {if (!document.hidden) refresh();});
window.addEventListener('online', () => {refresh(); if (pending) scheduleSave(); scheduleFog();});
window.addEventListener('storage', event => {if (event.key === 'darkMode') setTheme(event.newValue === 'true' ? 'dark' : 'light', false);});
window.addEventListener('beforeunload', event => {
  if (pending || saving || fogQueue.length || fogSaving || importing) {event.preventDefault(); event.returnValue = '';}
});
document.getElementById('fit-map').addEventListener('click', () => api?.scrollToContent(undefined, {fitToContent: true}));
document.getElementById('board-theme').addEventListener('click', () => setTheme(theme === 'dark' ? 'light' : 'dark'));
if (config.warden) {
  document.getElementById('fog-enabled').addEventListener('click', () => {
    const effective = fogQueue.reduce(applyFogOperation, fog);
    if (confirm(config.messages.confirmFog)) queueFog({type: effective.enabled ? 'disable' : 'hide_all'});
  });
  document.querySelectorAll('[data-fog-tool]').forEach(button => button.addEventListener('click', () => {
    const active = button.getAttribute('aria-pressed') !== 'true';
    document.querySelectorAll('[data-fog-tool]').forEach(item => item.setAttribute('aria-pressed', 'false'));
    button.setAttribute('aria-pressed', String(active)); layer.setTool(active ? button.dataset.fogTool : '');
  }));
  document.getElementById('fog-radius').addEventListener('input', event => layer.setRadius(Number(event.target.value)));
  document.querySelectorAll('[data-fog-action]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.fogAction === 'undo' || confirm(config.messages.confirmFog)) queueFog({type: button.dataset.fogAction});
  }));
  document.getElementById('player-preview').addEventListener('click', event => {
    playerPreview = !playerPreview; event.currentTarget.setAttribute('aria-pressed', String(playerPreview));
    layer.setPreview(playerPreview); displayFog();
  });
  document.getElementById('discard-fog').addEventListener('click', () => {
    if (confirm(config.messages.discardFog)) {fogQueue = []; fogBlocked = fogFailed = false; displayFog(); refresh();}
  });
  setupMapImport({config, tell, replace: async (source, cover) => {
    if (pending || saving || loading || fogQueue.length || fogSaving || version < 0) throw new Error(config.messages.waitForSave);
    importing = true; renderEditor(); showStatus();
    try {
      const response = await post(config.importUrl, {source_id: source.source_id, digest: source.digest,
        generation, version, fog_version: fogVersion, cover});
      if (denied(response)) throw new Error(config.messages.denied);
      if (response.status === 409) {refreshAgain = true; throw new Error(config.messages.importChanged);}
      if (!response.ok) throw new Error(config.messages.importFailed);
      acceptState(await response.json());
      api?.scrollToContent(undefined, {fitToContent: true});
    } finally {importing = false; drainUpdates(); renderEditor(); showStatus(); if (refreshAgain) {refreshAgain = false; refresh();}}
  }});
}
polling(); refresh();

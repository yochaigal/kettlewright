import {createElement as h} from 'react';
import {createRoot} from 'react-dom/client';
import {Excalidraw, restoreElements, CaptureUpdateAction} from 'excalidraw';
import {drawingFromScene, drawingImagesReady, drawingForSave} from './scene.js';
import {createActorUpdates} from './actor_updates.js';
import {mergeDrawings, sameDrawing} from './shared_map_merge.js';
import {loadLibraries, MAP_LIBRARIES} from './libraries.js';
import {createFogLayer, applyFogOperation} from './whiteboard_fog.js';
import {setupMapImport} from './whiteboard_import.js';
import {setupPartyTokens} from './party_tokens.js';
import {createLaserSync} from './whiteboard_laser.js';
import {stateFromUpdate} from './whiteboard_updates.js';
import {setupBoardControls} from './board_controls.js';
import {createTokenStats} from './token_stats.js';
import {createBoardRolls} from './board_rolls.js';
import {createTokenPortraits} from './token_portraits.js';
import {createWhiteboardSession} from './whiteboard_session.js';
import {editorLocale} from './locale.js';

const config = JSON.parse(document.getElementById('shared-map-config').textContent);
const editor = document.getElementById('editor'), root = createRoot(editor);
const status = document.getElementById('map-status');
const tell = key => {status.textContent = config.messages[key];};
// Excalidraw mutates existing elements in place while dragging/resizing.
// Keep acknowledgements and queued saves detached from those live objects.
const snapshot = (elements, files, appState) => structuredClone({...drawingFromScene(portraits.elements(elements), files),
  appState: {viewBackgroundColor: appState.viewBackgroundColor || '#ffffff'}});
let api, props, version = -1, generation = 1, initialized = false, applying = false, stopped = false;
let pending = null, saving = false, loading = false, importing = false, refreshAgain = false, timer, poll;
let lastDrawing = null, baseDrawing = null, saveBlocked = false, saveFailed = false, readFailed = false;
let fog = {enabled: false, base: 'covered', strokes: [], applied: []}, fogVersion = 0;
let fogQueue = [], fogSaving = false, fogBlocked = false, fogTimer, fogFailed = false;
let playerPreview = false, theme = 'light', connected = false;
let socketUpdates = [];
let latestState = null, sceneEpoch = 0;
let currentScene = config.warden ? new URL(location.href).searchParams.get('scene_id') : null;
let waitingForImages = false;
try {theme = localStorage.getItem('darkMode') === 'true' ? 'dark' : 'light';} catch (_) {}
document.body.classList.toggle('dark-mode', theme === 'dark');
const layer = createFogLayer({editor, getApi: () => api, warden: config.warden, onOperation: queueFog});
const library = loadLibraries([...MAP_LIBRARIES, 'clocks'], new URL(config.libraryUrl, location.href));
// Match the app's existing Socket.IO transport. HTTP polling below is the fallback.
const socket = io({transports: ['websocket'], reconnectionDelay: 1000, reconnectionDelayMax: 10000});
const actorUpdates = createActorUpdates({config, socket, denied});
const session = createWhiteboardSession({config, socket, getApi: () => api, refresh, switchScene, flushDrawing, preserveDraft,
  isPreview: () => playerPreview, onStatus: showStatus,
  onPanelChange: name => {if (name !== 'fog') {layer.setTool(''); document.querySelectorAll('[data-fog-tool]').forEach(button => button.setAttribute('aria-pressed', 'false'));}},
  project: update => {applying = true; try {update();} finally {applying = false;}}});
actorUpdates.subscribe('stats', data => session.actorSnapshot(data));

const laser = createLaserSync({socket, getApi: () => api, getGeneration: () => generation, config,
  canSend: () => initialized && !stopped && !importing});
editor.addEventListener('pointerleave', () => laser.stop());
window.addEventListener('blur', () => laser.stop());

const tokens = setupPartyTokens({editor, config, getApi: () => api, getGeneration: () => generation,
  canInsert: () => config.editing && initialized && !stopped && !importing && !playerPreview,
  managedInsert: (actor, element, file) => session.insert(actor, element, file),
  beforeInsert: () => {layer.setTool(''); document.querySelectorAll('[data-fog-tool]').forEach(button => button.setAttribute('aria-pressed', 'false'));}});

const boardControls = setupBoardControls({config, getApi: () => api, socket,
  canEdit: () => config.editing && initialized && !stopped && !importing && !playerPreview});
const boardRolls = createBoardRolls({config, getApi: () => api, updates: actorUpdates,
  canRoll: () => initialized && !stopped && !importing && !playerPreview,
  isPlayerPreview: () => playerPreview});
const tokenStats = createTokenStats({editor, config, getApi: () => api, updates: actorUpdates,
  confirmReveal: boardControls.confirmReveal,
  canReveal: () => config.warden && initialized && !stopped && !importing && !playerPreview,
  isPlayerPreview: () => playerPreview});

const portraits = createTokenPortraits({getApi: () => api, updates: actorUpdates,
  onProjection: update => {
    applying = true;
    try {update();} finally {applying = false;}
  }});

function showStatus() {
  if (stopped) {tell('denied'); return;}
  tell(saveBlocked ? 'invalid' : saveFailed ? 'failed' : readFailed ? 'offline'
    : pending || saving || importing || waitingForImages || session.busy ? 'saving' : 'saved');
  const fogStatus = document.getElementById('fog-status');
  if (fogStatus) fogStatus.textContent = config.messages[fogBlocked ? 'fogInvalid' : fogFailed ? 'fogFailed'
    : fogQueue.length || fogSaving ? 'saving' : ''] || '';
  const discard = document.getElementById('discard-fog');
  if (discard) discard.hidden = !fogBlocked;
}

function renderEditor() {
  if (!props || stopped) return;
  root.render(h(Excalidraw, {...props, key: `${latestState?.scene_id || 0}:${generation}`, langCode: editorLocale(document.documentElement.lang),
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
  session.destroy(); actorUpdates.destroy();
  boardControls.destroy(); boardRolls.destroy(); tokenStats.destroy(); portraits.destroy(); tokens.close(); laser.destroy(); layer.destroy(); root.unmount(); api = null; tell('denied');
}
function denied(response) {
  if (response.redirected || [401, 403, 404].includes(response.status)) {revoke(); return true;}
  return false;
}
function post(url, body, timeout = 15000) {
  return fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({...session.context(), ...body, csrf_token: config.csrfToken}), signal: AbortSignal.timeout(timeout)});
}
function scheduleSave(delay = 400) {
  if (stopped || saveBlocked || waitingForImages) return;
  clearTimeout(timer);
  timer = setTimeout(() => {timer = null; save();}, delay);
}
async function save() {
  if (!pending || saving || loading || importing || stopped || saveBlocked || waitingForImages) return;
  const drawing = pending, sentGeneration = generation, sentEpoch = sceneEpoch;
  pending = null; saving = true; showStatus();
  try {
    const response = await post(config.sceneUrl, {...drawingForSave(drawing, baseDrawing), version, generation: sentGeneration}, 60000);
    if (sentEpoch !== sceneEpoch) return;
    if (denied(response)) return;
    if (response.status === 409) {
      pending ||= drawing; const error = await response.json();
      if (error.reason === 'reload_required') {saveBlocked = true; api?.setToast({message: config.messages.reloadRequired});}
      else if (error.reason === 'active_changed') await switchScene(null, true);
      else refreshAgain = true;
      return;
    }
    if ([400, 413].includes(response.status)) {pending ||= drawing; saveBlocked = true; return;}
    if (!response.ok) throw new Error();
    version = (await response.json()).version; if (latestState) latestState.version = version; baseDrawing = drawing; saveFailed = false;
    actorUpdates.placed(drawing.elements);
  } catch (_) {if (sentEpoch === sceneEpoch) {pending ||= drawing; saveFailed = true; scheduleSave(2500);}}
  finally {
    if (sentEpoch !== sceneEpoch) return;
    saving = false; drainUpdates(); showStatus();
    if (refreshAgain) {refreshAgain = false; refresh();} else if (pending) scheduleSave(saveFailed ? 2500 : 400);
  }
}

function onChange(elements, appState, files) {
  layer.redraw(); tokenStats.redraw(); portraits.redraw(); boardRolls.redraw(); boardControls.selection(appState);
  if (stopped || appState.isLoading) return;
  setTheme(appState.theme);
  if (appState.activeTool?.type !== 'laser') laser.stop();
  else document.querySelectorAll('[data-fog-tool][aria-pressed="true"]').forEach(button => {
    button.setAttribute('aria-pressed', 'false'); layer.setTool('');
  });
  if (!api || applying) return;
  const drawing = snapshot(elements, files, appState);
  const imagesWerePending = waitingForImages;
  waitingForImages = !drawingImagesReady(drawing);
  if (waitingForImages) {showStatus(); return;}
  if (!initialized) {
    initialized = true; lastDrawing = baseDrawing = drawing;
    setTimeout(() => {
      if (stopped) return;
      api?.scrollToContent(undefined, {fitToContent: true}); drainUpdates();
      if (refreshAgain && !saving && !loading) {refreshAgain = false; refresh();}
    }, 0);
    return;
  }
  if (!config.editing || playerPreview || importing) return;
  session.capture(elements);
  if (sameDrawing(drawing, lastDrawing)) {
    if (imagesWerePending) {
      showStatus(); if (pending) scheduleSave(); drainUpdates();
      if (refreshAgain && !saving && !loading) {refreshAgain = false; refresh();}
    }
    return;
  }
  lastDrawing = drawing; pending = drawing; saveBlocked = false;
  showStatus(); scheduleSave();
}

function mount(data) {
  const initial = session.initialDrawing(data.drawing);
  version = data.version; generation = data.generation || 1;
  props = {
    excalidrawAPI: instance => {api = instance; layer.redraw(); tokenStats.redraw(); session.render();},
    initialData: {elements: restoreElements(initial.elements, null), files: initial.files,
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
  } finally {applying = false; layer.redraw(); session.render();}
}
function preserveDraft() {
  if (!pending && !saving && !fogQueue.length && !session.busy) return;
  const data = {type: 'excalidraw', version: 2, source: location.origin,
    ...(pending || lastDrawing),
    elements: [...(pending || lastDrawing).elements, ...session.draft()],
    files: {...(pending || lastDrawing).files, ...session.files()}, whiteboardFog: fogQueue.reduce(applyFogOperation, fog)};
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
  if (version >= 0 && nextGeneration !== generation) {preserveDraft(); session.reset();}
  latestState = {...latestState, ...data};
  data = latestState;
  session.accept(data);
  if (version >= 0 && nextGeneration !== generation) {
    tokens.close(); laser.clear(); pending = null; fogQueue = []; saveBlocked = fogBlocked = saveFailed = fogFailed = false;
    clearTimeout(timer); timer = null; clearTimeout(fogTimer); fogTimer = null;
    layer.setTool(''); document.querySelectorAll('[data-fog-tool]').forEach(button => button.setAttribute('aria-pressed', 'false'));
    generation = nextGeneration; version = data.version; fogVersion = -1;
    initialized = false; api = null; props = null; root.render(null);
    mount(data); baseDrawing = data.drawing;
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
  actorUpdates.placed([...data.drawing.elements, ...(data.tokens || []).map(token => token.element)]);
  session.render();
}
async function refresh(force = false) {
  if (stopped || document.hidden) return;
  if (saving || loading || importing || waitingForImages) {refreshAgain = true; return;}
  loading = true; const sentEpoch = sceneEpoch;
  try {
    const params = new URLSearchParams();
    if (currentScene) params.set('scene_id', currentScene);
    if (version >= 0 && latestState && force !== true) for (const key of ['version', 'generation', 'fog_version', 'tokens_version', 'encounter_version', 'markers_version', 'activation_version', 'view_revision']) params.set(key, latestState[key]);
    const response = await fetch(config.sceneUrl + '?' + params, {cache: 'no-store', signal: AbortSignal.timeout(60000)});
    if (sentEpoch !== sceneEpoch) return;
    if (response.status === 409 || response.status === 404 && config.warden && currentScene) {await switchScene(null, true); return;}
    if (denied(response)) return;
    if (!response.ok) throw new Error();
    if (response.status === 204) {readFailed = false; return;}
    const data = await response.json();
    if (!stopped && sentEpoch === sceneEpoch) {acceptState(data); readFailed = false;}
  } catch (_) {if (sentEpoch === sceneEpoch) {readFailed = true; if (version < 0 && !stopped) tell('loadFailed');}}
  finally {
    if (sentEpoch !== sceneEpoch) return;
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
  fogSaving = true; const operation = fogQueue[0], sentGeneration = generation, sentEpoch = sceneEpoch;
  try {
    const response = await post(config.fogUrl, {operation, generation: sentGeneration, fog_version: fogVersion});
    if (denied(response)) return;
    if (response.status === 409) {await refresh(); return;}
    if ([400, 413].includes(response.status)) {fogBlocked = true; return;}
    if (!response.ok) throw new Error();
    const data = await response.json();
    if (generation !== sentGeneration || sentEpoch !== sceneEpoch) return;
    fogQueue = fogQueue.filter(item => item.id !== operation.id);
    if (data.fog_version >= fogVersion) {fog = data.fog; fogVersion = data.fog_version;}
    fogFailed = false; displayFog();
  } catch (_) {if (sentEpoch === sceneEpoch) {fogFailed = true; scheduleFog(2500);}}
  finally {if (sentEpoch === sceneEpoch) {fogSaving = false; showStatus(); scheduleFog();}}
}

function drainUpdates() {
  if (saving || loading || importing || waitingForImages || !api || !initialized || stopped) return;
  const queued = socketUpdates; socketUpdates = [];
  for (const event of queued) {
    const state = stateFromUpdate(event, {...latestState, drawing: baseDrawing, version, generation, fog, fog_version: fogVersion});
    if (!state) {refreshAgain = true; break;}
    acceptState(state);
  }
  if (pending) scheduleSave();
}
function receiveUpdate(data) {
  if (data.party_id !== config.partyId || stopped) return;
  if (data.scene_id && data.scene_id !== latestState?.scene_id) return;
  if (latestState && ['tokens_version', 'encounter_version', 'markers_version', 'activation_version'].some(key => data[key] > latestState[key])) {refresh(); return;}
  if (!(data.version > version || data.generation > generation || data.fog_version > fogVersion)) return;
  if (!data.update) {refresh(); return;} // Rolling upgrade from an older server.
  if (socketUpdates.length >= 100) {socketUpdates = []; refreshAgain = true;}
  else socketUpdates.push(data);
  drainUpdates();
  if (refreshAgain && !saving && !loading && !importing) {refreshAgain = false; refresh();}
}
function polling() {clearInterval(poll); poll = setInterval(() => {if (!document.hidden) refresh();}, connected ? 60000 : 15000);}
socket.on('connect', () => {connected = true; polling(); refresh();});
socket.on('disconnect', () => {connected = false; polling(); refresh();});
socket.on('shared_map_changed', receiveUpdate);
socket.on('whiteboard_active_changed', data => {if (data.party_id === config.partyId) {if (config.warden) refresh(); else switchScene(null, true);}});
socket.on('party_members_changed', data => {if (data.party_id === config.partyId) refresh(true);});
socket.on('party_actors_changed', data => {if (data.party_id === config.partyId) refresh(true);});
document.addEventListener('visibilitychange', () => {if (!document.hidden) refresh();});
window.addEventListener('online', () => {refresh(); if (pending) scheduleSave(); scheduleFog();});
window.addEventListener('storage', event => {if (event.key === 'darkMode') setTheme(event.newValue === 'true' ? 'dark' : 'light', false);});
window.addEventListener('beforeunload', event => {
  if (pending || saving || waitingForImages || fogQueue.length || fogSaving || importing || session.busy) {event.preventDefault(); event.returnValue = '';}
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
    layer.setPreview(playerPreview); session.render(); tokenStats.reset(); boardRolls.redraw(); displayFog();
  });
  document.getElementById('discard-fog').addEventListener('click', () => {
    if (confirm(config.messages.discardFog)) {fogQueue = []; fogBlocked = fogFailed = false; displayFog(); refresh();}
  });
  if (config.canLoadMaps) setupMapImport({config, tell, replace: async (source, cover, mode) => {
    if (pending || saving || waitingForImages || loading || fogQueue.length || fogSaving || version < 0) throw new Error(config.messages.waitForSave);
    await session.flush();
    importing = true; renderEditor(); showStatus();
    try {
      const response = await post(config.importUrl, {source_id: source.source_id, digest: source.digest,
        generation, version, fog_version: fogVersion, tokens_version: latestState.tokens_version,
        markers_version: latestState.markers_version, encounter_version: latestState.encounter_version, cover, mode});
      if (denied(response)) throw new Error(config.messages.denied);
      if (response.status === 409) {refreshAgain = true; throw new Error(config.messages.importChanged);}
      if (!response.ok) throw new Error(config.messages.importFailed);
      const data = await response.json();
      if (data.scene_id !== latestState.scene_id) await switchScene(data.scene_id, true);
      else acceptState(data);
      api?.scrollToContent(undefined, {fitToContent: true});
    } finally {importing = false; drainUpdates(); renderEditor(); showStatus(); if (refreshAgain) {refreshAgain = false; refresh();}}
  }});
}
polling(); refresh();

async function flushDrawing() {
  for (let attempt = 0; attempt < 150; attempt++) {
    if (!pending && !saving && !loading && !waitingForImages && !fogQueue.length && !fogSaving) return;
    if (saveBlocked || fogBlocked || saveFailed || fogFailed) break;
    await save(); await saveFog();
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(config.messages.waitForSave);
}
async function switchScene(id, forced = false) {
  if (stopped) return;
  if (!forced) {await flushDrawing(); await session.flush();}
  preserveDraft(); ++sceneEpoch;
  currentScene = id; session.reset(); latestState = null;
  pending = null; fogQueue = []; socketUpdates = []; waitingForImages = false;
  clearTimeout(timer); clearTimeout(fogTimer);
  saving = loading = fogSaving = importing = initialized = applying = false;
  saveBlocked = fogBlocked = saveFailed = fogFailed = readFailed = false;
  version = -1; fogVersion = -1; generation = 1; api = null; props = null;
  tokens.close(); laser.clear(); tokenStats.reset(); root.render(null);
  const address = new URL(location.href);
  if (config.warden && id) address.searchParams.set('scene_id', id); else address.searchParams.delete('scene_id');
  history.replaceState(null, '', address);
  await refresh(); actorUpdates.refresh();
}

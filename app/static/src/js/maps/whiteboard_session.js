import {restoreElements, CaptureUpdateAction} from 'excalidraw';
import {initials} from './party_tokens.js';

export const tokenGeometry = element => Object.fromEntries(['x', 'y', 'width', 'height', 'angle'].map(key => [key, element[key] || 0]));
export const managedElement = element => ['token', 'marker'].includes(element.customData?.kwType);
export function presenceUsers(members) {
  return members.map(member => ({...member, label: member.warden ? 'W' : initials(member.characters[0] || member.username)}));
}

// Managed objects never enter Excalidraw's free-drawing save queue.
export function createWhiteboardSession({config, socket, getApi, project, refresh, switchScene, flushDrawing, preserveDraft, isPreview, onStatus = () => {}, onPanelChange = () => {}}) {
  const base = config.boardUrl, messages = config.messages;
  const pending = new Map(), statTimers = new Map(), statSaves = new Map();
  let state = null, tokens = new Map(), saving = null, timer, stopped = false, active = null, panelSignature = '', epoch = 0;
  let markersFrame = null, presenceEpoch = 0, sceneRequest = 0, presenceScene = null, sceneListSignature = '';
  let activating = false;
  const toolbar = document.getElementById('scene-controls'), select = document.getElementById('board-scene');
  const activateButton = document.getElementById('scene-activate');
  const tokenPanel = document.getElementById('token-actions');
  const panels = ['scene', 'fog', 'encounter'].map(name => ({name,
    button: document.getElementById(name === 'encounter' ? 'board-encounter' : `board-${name}-toggle`),
    panel: document.getElementById(`${name}-panel`)})).filter(item => item.button && item.panel);
  let openPanel = null, encounterBusy = false;
  const encounterPortraits = new Map();
  const markerLayer = document.createElement('div'); markerLayer.className = 'board-markers';
  let markerHost;
  const context = () => state ? {protocol: 2, scene_id: state.scene_id, activation_version: state.activation_version, generation: state.generation} : {};
  const url = path => `${base}/${path}?scene_id=${state?.scene_id || ''}`;
  function busyMessage(error) {getApi()?.setToast({message: error?.message || messages.actionFailed});}
  async function request(path, body) {
    const response = await fetch(`${base}/${path}`, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({...context(), ...body, csrf_token: config.csrfToken}), signal: AbortSignal.timeout(15000)});
    if (!response.ok || response.redirected) {
      if (response.status === 409) {await refresh(); throw new Error(messages.conflict);}
      const error = new Error(messages.actionFailed); error.status = response.status; throw error;
    }
    return response.json();
  }
  function schedule() {onStatus(); clearTimeout(timer); if (!stopped) timer = setTimeout(() => {save().catch(busyMessage);}, 180);}
  async function save() {
    if (saving) return saving;
    if (!pending.size || !state) return;
    const run = epoch, sent = new Map([...pending].map(([id, operation]) => [id, structuredClone(operation)])), revision = state.tokens_version;
    saving = (async () => {
      try {
        const data = await request('placed-tokens', {tokens_version: revision, operations: [...sent.values()]});
        if (run !== epoch || stopped) return;
        for (const [id, operation] of sent) if (JSON.stringify(pending.get(id)) === JSON.stringify(operation)) pending.delete(id);
        accept(data);
      } catch (error) {
        if (run === epoch) {
          if ([400, 403, 404, 413].includes(error.status)) for (const id of sent.keys()) pending.delete(id);
          await refresh(true);
          busyMessage(error);
        }
      } finally {if (run === epoch) {saving = null; onStatus(); if (pending.size) {clearTimeout(timer); timer = setTimeout(() => save().catch(busyMessage), 2500);}}}
    })();
    return saving;
  }
  function initialDrawing(drawing) {
    const elements = drawing.elements.filter(element => !managedElement(element));
    const files = {...drawing.files};
    for (const token of tokens.values()) {
      const operation = pending.get(token.id);
      if (operation?.action === 'delete' || isPreview() && !token.visible) continue;
      elements.push({...token.element, ...operation?.geometry,
        locked: !token.can_control || isPreview(), opacity: token.visible ? 100 : 40,
        customData: {kwType: 'token', actorId: token.actor_id}});
      Object.assign(files, token.files);
    }
    return {elements, files};
  }
  function render() {
    const api = getApi();
    if (!api || !state || stopped) return;
    const drawing = initialDrawing({elements: api.getSceneElements(), files: {}});
    project(() => {
      api.addFiles(Object.values(drawing.files));
      api.updateScene({elements: restoreElements(drawing.elements, null), captureUpdate: CaptureUpdateAction.NEVER});
    });
    syncPanels();
    drawPanel(); redrawMarkers();
  }
  function capture(elements) {
    if (!state || stopped || isPreview()) return;
    const current = new Map(elements.filter(element => !element.isDeleted).map(element => [element.id, element]));
    let repair = false;
    for (const token of tokens.values()) {
      const element = current.get(token.id), queued = pending.get(token.id);
      if (queued?.action === 'delete') continue;
      const expected = {...token.element, ...queued?.geometry};
      if (!element) {repair = true; continue;}
      if (JSON.stringify(tokenGeometry(element)) !== JSON.stringify(tokenGeometry(expected))) {
        if (!token.can_control) {repair = true; continue;}
        if (queued?.action === 'create') {
          if (!element) {pending.delete(token.id); tokens.delete(token.id);}
          else {queued.drawing.elements[0] = {...queued.drawing.elements[0], ...tokenGeometry(element)}; token.element = queued.drawing.elements[0];}
        } else pending.set(token.id, element ? {id: token.id, action: 'update', geometry: tokenGeometry(element)} : {id: token.id, action: 'delete'});
        schedule();
      }
    }
    // Native duplicate/paste cannot forge another actor or bypass token creation.
    if (elements.some(element => managedElement(element) && !tokens.has(element.id))) repair = true;
    if (repair) queueMicrotask(render);
    const selected = Object.keys(getApi()?.getAppState().selectedElementIds || {});
    if (selected.length === 1 && tokens.has(selected[0])) active = selected[0];
    else if (selected.length) active = null;
    drawPanel(); redrawMarkers();
  }
  async function insert(actor, element, file) {
    if (!state || isPreview()) return;
    const token = {id: element.id, actor_id: String(actor.id), element, files: {[file.id]: file}, can_control: true,
      name: actor.name, kind: actor.kind || 'character', visible: actor.kind !== 'monster', numbered: false};
    tokens.set(token.id, token); active = token.id;
    pending.set(token.id, {id: token.id, action: 'create', actor_id: token.actor_id, drawing: {elements: [element], files: token.files}});
    render();
    getApi()?.updateScene({appState: {selectedElementIds: {[token.id]: true}}, captureUpdate: CaptureUpdateAction.NEVER});
    schedule();
  }
  function accept(data) {
    if (stopped || !data?.scene_id) return;
    if (state && state.scene_id === data.scene_id) {
      if (data.generation < state.generation) return;
      data = {...data};
      for (const [field, value] of [['tokens_version', 'tokens'], ['encounter_version', 'encounter'], ['markers_version', 'markers']]) {
        if (data[field] < state[field]) {data[field] = state[field]; data[value] = state[value];}
      }
      if (data.activation_version < state.activation_version) {
        data.activation_version = state.activation_version; data.active_scene_id = state.active_scene_id;
      }
    }
    state = data; config.boardContext = context();
    tokens = new Map(data.tokens.map(token => [token.id, token]));
    for (const [id, operation] of pending) {
      if (operation.action === 'create' && !tokens.has(id)) {
        tokens.set(id, {id, actor_id: operation.actor_id, element: operation.drawing.elements[0], files: operation.drawing.files,
          can_control: true, visible: false, name: messages.saving, kind: 'monster'});
      } else if (operation.action === 'create' && tokens.has(id)) {
        const geometry = tokenGeometry(operation.drawing.elements[0]);
        if (JSON.stringify(geometry) !== JSON.stringify(tokenGeometry(tokens.get(id).element))) pending.set(id, {id, action: 'update', geometry});
        else pending.delete(id);
      } else if (operation.action === 'delete' && !tokens.has(id)) pending.delete(id);
      else if (operation.action === 'update' && (!tokens.has(id) || !tokens.get(id).can_control)) pending.delete(id);
    }
    if (select) select.value = String(data.scene_id);
    document.getElementById('scene-name').textContent = data.name;
    document.getElementById('scene-draft').hidden = !config.warden || data.scene_id === data.active_scene_id;
    updateActivation();
    render(); renderEncounter();
    if (presenceScene !== state.scene_id) {presenceScene = state.scene_id; announcePresence();}
    const signature = JSON.stringify([state.scene_id, state.name, state.active_scene_id]);
    if (sceneListSignature !== signature) {sceneListSignature = signature; loadScenes();}
  }
  function selectedActor() {return tokens.get(active);}
  function button(text, handler, disabled = false) {
    const node = document.createElement('button'); node.type = 'button'; node.textContent = text; node.disabled = disabled;
    node.addEventListener('click', () => Promise.resolve(handler()).catch(busyMessage)); return node;
  }
  function removeTokens(ids) {
    if (isPreview()) return;
    for (const id of ids) {
      if (!tokens.get(id)?.can_control) continue;
      if (pending.get(id)?.action === 'create') {pending.delete(id); tokens.delete(id);}
      else pending.set(id, {id, action: 'delete'});
      if (active === id) active = null;
    }
    render(); schedule();
  }
  const deleteKey = event => {
    if (!['Delete', 'Backspace'].includes(event.key) || event.target.closest?.('input, textarea, [contenteditable=true]')) return;
    const selected = Object.keys(getApi()?.getAppState().selectedElementIds || {});
    const owned = selected.filter(id => tokens.get(id)?.can_control);
    if (!owned.length) return;
    removeTokens(owned);
    if (selected.every(id => tokens.has(id) || owned.includes(id))) {event.preventDefault(); event.stopPropagation();}
  };
  document.getElementById('editor').addEventListener('keydown', deleteKey, true);
  async function tokenAction(values) {
    const token = selectedActor(); if (!token) return;
    await flush();
    accept(await request('placed-tokens', {tokens_version: state.tokens_version,
      operations: [{id: token.id, action: 'update', ...values}]}));
  }
  let actors = new Map();
  function actorSnapshot(list) {actors = new Map((list || []).map(actor => [actor.id, actor])); panelSignature = ''; drawPanel();}
  function drawPanel() {
    if (!tokenPanel) return;
    const token = selectedActor(), actor = actors.get(token?.actor_id);
    document.body?.classList.toggle('board-token-selected', Boolean(token));
    tokenPanel.hidden = !token || isPreview();
    if (!token || isPreview()) return;
    const participating = state.encounter.participants.some(actor => actor.id === token.actor_id);
    const encounterAction = tokenPanel.querySelector('#token-encounter-action');
    if (encounterAction) {
      encounterAction.textContent = messages[participating ? 'alreadyEncounter' : 'addEncounter'];
      encounterAction.disabled = participating || encounterBusy;
    }
    if (document.activeElement?.matches?.('input[type=number]') && tokenPanel.contains?.(document.activeElement)) return;
    const signature = JSON.stringify([token.id, token.name, token.visible, token.numbered, token.can_edit, actor, participating, encounterBusy]);
    if (signature === panelSignature) return;
    panelSignature = signature; tokenPanel.replaceChildren();
    const heading = document.createElement('strong'); heading.textContent = token.name; tokenPanel.append(heading);
    if (actor?.stats?.hp) {
      const label = document.createElement('label'); label.textContent = 'HP ';
      const input = document.createElement('input'); input.type = 'number'; input.min = '0'; input.max = actor.stats.hp[1];
      input.value = actor.stats.hp[0]; input.required = true; input.disabled = !token.can_edit;
      input.setAttribute('aria-label', 'HP');
      input.addEventListener('input', () => {if (input.validity.valid && input.value !== '') queueStat(token, 'hp', input.value);});
      input.addEventListener('change', () => {if (input.reportValidity()) queueStat(token, 'hp', input.value, true);});
      label.append(input); tokenPanel.append(label);
    }
    if (actor?.conditions) for (const field of ['deprived', 'panicked', 'dead']) {
      const checked = actor.conditions[field];
      const label = document.createElement('label'), input = document.createElement('input'); input.type = 'checkbox'; input.checked = checked;
      input.disabled = !token.can_edit; label.append(input, document.createTextNode(messages[field]));
      input.addEventListener('change', () => queueStat(token, field, input.checked ? 1 : 0, true)); tokenPanel.append(label);
    }
    if (token.can_control) tokenPanel.append(button(messages.deleteToken, () => removeTokens([token.id])));
    if (token.sheet_url) tokenPanel.append(button(messages.openSheet, () => openSheet(token.sheet_url)));
    if (config.warden) {
      tokenPanel.append(button(messages[token.visible ? 'hideToken' : 'showToken'], () => tokenAction({visible: !token.visible})));
      if (token.kind === 'monster') tokenPanel.append(button(messages.numberTokens, () => tokenAction({numbered: !token.numbered})));
      const add = button(messages[participating ? 'alreadyEncounter' : 'addEncounter'], async () => {
        await changeEncounter('add', {actor_id: token.actor_id});
        setOpenPanel('encounter');
      }, participating || encounterBusy);
      add.id = 'token-encounter-action'; tokenPanel.append(add);
    }
  }
  function queueStat(token, stat, value, immediate = false) {
    const key = `${token.actor_id}:${stat}`, scope = context();
    clearTimeout(statTimers.get(key)?.timer);
    const run = () => {
      statTimers.delete(key);
      const previous = statSaves.get(key) || Promise.resolve();
      const saving = previous.catch(() => {}).then(() => saveStat(token, stat, value, scope));
      statSaves.set(key, saving); onStatus();
      saving.catch(busyMessage).finally(() => {if (statSaves.get(key) === saving) statSaves.delete(key); onStatus();});
      return saving;
    };
    if (immediate) run();
    else statTimers.set(key, {run, timer: setTimeout(run, 350)});
    onStatus();
  }
  async function saveStat(token, stat, value, scope = context()) {
    const body = new FormData();
    for (const [key, val] of Object.entries({...scope, csrf_token: config.csrfToken, actor_id: token.actor_id, stat, value})) body.set(key, val);
    const response = await fetch(`${base}/actor-stat`, {method: 'POST', body, signal: AbortSignal.timeout(10000)});
    if (!response.ok || response.redirected) throw new Error(messages.actionFailed);
    await refresh(true);
  }
  function openSheet(address) {
    const panel = document.getElementById('party-panel'), frame = document.getElementById('party-frame');
    frame.src = address + (address.includes('?') ? '&' : '?') + 'scene_id=' + state.scene_id;
    if (!panel.open) panel.show();
  }
  function renderEncounter() {
    const list = document.getElementById('encounter-list'); if (!state || !list) return;
    syncPanels();
    document.getElementById('encounter-count').textContent = state.encounter.participants.length ? ` (${state.encounter.participants.length})` : '';
    document.getElementById('encounter-round').textContent = `${messages.round} ${state.encounter.round}`;
    document.getElementById('encounter-empty').hidden = state.encounter.participants.length > 0;
    list.replaceChildren(); encounterPortraits.clear();
    for (const actor of state.encounter.participants) {
      const row = document.createElement('div'), acted = document.createElement('input'); row.className = 'encounter-row';
      acted.type = 'checkbox'; acted.checked = actor.acted; acted.disabled = !actor.can_control || encounterBusy;
      acted.setAttribute('aria-label', `${actor.name}: ${messages.acted}`);
      acted.addEventListener('change', async () => {
        try {await changeEncounter('acted', {actor_id: actor.id, acted: acted.checked});}
        catch (error) {busyMessage(error); renderEncounter();}
      });
      const label = document.createElement('label'); label.append(acted, document.createTextNode(messages.acted));
      const actorButton = button(actor.name, () => {
        const token = [...tokens.values()].find(token => token.actor_id === actor.id && (!isPreview() || token.visible));
        if (token) {active = token.id; getApi()?.scrollToContent(token.element, {animate: true}); drawPanel();}
        else if (actor.sheet_url) openSheet(actor.sheet_url);
      });
      actorButton.className = 'encounter-actor'; actorButton.title = actor.name;
      const avatar = document.createElement('span'); avatar.className = 'encounter-avatar';
      avatar.textContent = initials(actor.name); avatar.setAttribute('aria-hidden', 'true');
      actorButton.replaceChildren(avatar, document.createTextNode(actor.name));
      encounterPortraits.set(actor.id, {node: avatar});
      row.append(actorButton, label);
      if (config.warden) {
        const remove = button('×', () => changeEncounter('remove', {actor_id: actor.id}), encounterBusy);
        remove.title = messages.removeEncounter; remove.setAttribute('aria-label', messages.removeEncounter); row.append(remove);
      }
      list.append(row);
    }
    refreshEncounterPortraits();
    if (config.warden) {
      const choices = document.getElementById('encounter-actor'), selected = choices.value;
      const participating = new Set(state.encounter.participants.map(actor => actor.id));
      const available = new Map([...tokens.values()].filter(token => !participating.has(token.actor_id)).map(token => [token.actor_id, token]));
      const placeholder = document.createElement('option'); placeholder.value = '';
      placeholder.textContent = messages[available.size ? 'chooseEncounterToken' : 'noEncounterTokens'];
      choices.replaceChildren(placeholder);
      for (const [id, token] of available) {const option = document.createElement('option'); option.value = id; option.textContent = token.name; choices.append(option);}
      choices.value = available.has(selected) ? selected : ''; choices.disabled = !available.size || encounterBusy;
      document.getElementById('encounter-add').disabled = !choices.value || encounterBusy;
      for (const action of ['next_round', 'reset']) document.getElementById(`encounter-${action}`).disabled = !participating.size || encounterBusy;
    }
  }
  function refreshEncounterPortraits() {
    if (!state || stopped) return;
    const api = getApi(), elements = new Map((api?.getSceneElements() || []).map(element => [element.id, element]));
    const files = api?.getFiles?.() || {};
    for (const [actorId, portrait] of encounterPortraits) {
      const token = [...tokens.values()].find(token => token.actor_id === actorId && (!isPreview() || token.visible));
      const element = token && elements.get(token.id);
      const source = token && (files[element?.fileId] || token.files[token.element.fileId])?.dataURL;
      if (portrait.source === source) continue;
      portrait.source = source; portrait.image?.remove(); portrait.image = null;
      if (source) {
        const image = document.createElement('img'); image.alt = ''; image.referrerPolicy = 'no-referrer'; image.src = source;
        image.addEventListener('error', () => image.remove()); portrait.node.append(image); portrait.image = image;
      }
    }
  }
  function syncPanels() {
    for (const {name, button, panel} of panels) {
      const available = Boolean(state) && (!isPreview() || name === 'fog');
      panel.hidden = openPanel !== name || !available;
      button.disabled = !available; button.setAttribute('aria-expanded', String(!panel.hidden));
    }
  }
  function setOpenPanel(name) {openPanel = name; syncPanels(); onPanelChange(name);}
  async function changeEncounter(action, values = {}) {
    if (!state || encounterBusy) return;
    if (action === 'add' && state.encounter.participants.some(actor => actor.id === values.actor_id)) return;
    const run = epoch; encounterBusy = true; renderEncounter(); drawPanel();
    try {
      const data = await request('encounter', {encounter_version: state.encounter_version, action, ...values});
      if (run === epoch) accept(data);
    } finally {if (run === epoch) {encounterBusy = false; renderEncounter(); drawPanel();}}
  }
  for (const {name, button} of panels) button.addEventListener('click', () => setOpenPanel(openPanel === name ? null : name));
  document.getElementById('encounter-close')?.addEventListener('click', () => setOpenPanel(null));
  function redrawMarkers() {
    if (markersFrame === null && !stopped) markersFrame = requestAnimationFrame(drawMarkers);
  }
  function drawMarkers() {
    markersFrame = null;
    const api = getApi(), host = document.querySelector('#editor .excalidraw');
    if (!api || !state || !host) return;
    if (markerHost !== host) {markerHost = host; host.append(markerLayer);}
    const view = api.getAppState(); markerLayer.replaceChildren();
    for (const token of tokens.values()) {
      if (!token.numbered || isPreview() && !token.visible || pending.get(token.id)?.action === 'delete') continue;
      const element = {...token.element, ...pending.get(token.id)?.geometry};
      const label = document.createElement('span'); label.className = 'token-name'; label.textContent = token.name;
      label.style.left = `${(element.x+element.width/2+view.scrollX)*view.zoom.value}px`;
      label.style.top = `${(element.y+view.scrollY)*view.zoom.value-18}px`; markerLayer.append(label);
    }
    for (const marker of state.markers) {
      if (isPreview() && config.warden) continue; // No private labels in opaque player preview.
      const node = button(marker.number || '●', () => showMarker(marker));
      node.className = 'board-marker'; node.title = marker.title; node.setAttribute('aria-label', marker.title);
      node.style.left = `${(marker.x + view.scrollX) * view.zoom.value}px`;
      node.style.top = `${(marker.y + view.scrollY) * view.zoom.value}px`;
      if (config.warden) {
        let origin = null, moved = false;
        node.addEventListener('pointerdown', event => {event.stopPropagation(); origin = {x: event.clientX, y: event.clientY}; moved = false; node.setPointerCapture(event.pointerId);});
        node.addEventListener('pointermove', event => {
          if (!origin) return;
          const dx = event.clientX-origin.x, dy = event.clientY-origin.y;
          if (Math.hypot(dx,dy) > 3) moved = true;
          if (moved) {node.style.left = `${(marker.x+view.scrollX)*view.zoom.value+dx}px`; node.style.top = `${(marker.y+view.scrollY)*view.zoom.value+dy}px`;}
        });
        node.addEventListener('pointerup', async event => {
          if (!origin) return;
          const start = origin; origin = null;
          if (!moved) return;
          try {accept(await request('markers', {markers_version: state.markers_version, action: 'update', id: marker.id,
            x: marker.x+(event.clientX-start.x)/view.zoom.value, y: marker.y+(event.clientY-start.y)/view.zoom.value}));}
          catch (error) {busyMessage(error); redrawMarkers();}
        });
        node.addEventListener('click', event => {if (moved) {event.stopImmediatePropagation(); event.preventDefault();}}, true);
      }
      markerLayer.append(node);
    }
  }
  function showMarker(marker) {
    const dialog = document.getElementById('marker-detail'); dialog.replaceChildren();
    const title = document.createElement('h2'); title.textContent = marker.title; dialog.append(title);
    dialog.append(button(messages.openMaterial, () => {openSheet(marker.url); dialog.close();}));
    if (marker.reveal_url) {
      dialog.append(button(messages.revealMaterial, () => {openSheet(marker.reveal_url); dialog.close();}));
      dialog.append(button(messages.delete, async () => {accept(await request('markers', {markers_version: state.markers_version, action: 'delete', id: marker.id})); dialog.close();}));
    }
    dialog.append(button(messages.close, () => dialog.close())); dialog.showModal();
  }
  async function flush() {
    for (const task of [...statTimers.values()]) {clearTimeout(task.timer); task.run();}
    await Promise.all([...statSaves.values()]);
    for (let attempts = 0; attempts < 3 && (pending.size || saving); attempts++) await save();
    if (pending.size) throw new Error(messages.waitForSave);
  }
  async function sceneAction(action, name) {
    await flushDrawing(); await flush();
    const data = await request('scenes', {action, name});
    if (action === 'activate') {state.activation_version = data.activation_version; state.active_scene_id = data.active_scene_id; accept(data);}
    else if (action === 'delete') await switchScene(null);
    else await switchScene(data.scene_id);
  }
  function updateActivation() {
    if (!activateButton) return;
    const shown = state?.scene_id === state?.active_scene_id;
    activateButton.disabled = !state || shown || activating;
    activateButton.textContent = activating ? messages.showingScene : shown ? messages.activeScene : messages.showScene;
    const help = document.getElementById('scene-visibility-help');
    if (help) help.textContent = state ? messages[shown ? 'shownSceneHelp' : 'privateSceneHelp'] : '';
  }
  async function activateScene() {
    if (!state || activating || state.scene_id === state.active_scene_id) return;
    activating = true; updateActivation();
    try {await sceneAction('activate');}
    catch (error) {busyMessage(error);}
    finally {activating = false; updateActivation();}
  }
  async function loadScenes() {
    if (!config.warden || !state) return;
    const run = ++sceneRequest;
    try {
      const response = await fetch(url('scenes'), {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok) return;
      const data = await response.json(); if (run !== sceneRequest || stopped) return;
      select.replaceChildren();
      for (const scene of data.scenes) {
        const option = document.createElement('option'); option.value = scene.id;
        option.textContent = scene.name + (scene.id === data.active_scene_id ? ` · ${messages.activeScene}` : ''); select.append(option);
      }
      select.value = state.scene_id;
    } catch (_) { /* Keep the current scene usable during a connection outage. */ }
  }
  if (toolbar) {
    select.addEventListener('change', async () => {
      const target = Number(select.value);
      try {await flushDrawing(); await flush(); await switchScene(target);} catch (error) {select.value = state.scene_id; busyMessage(error);}
    });
    const sceneDialog = document.getElementById('scene-dialog'), sceneInput = document.getElementById('scene-dialog-name');
    let editingAction = 'create';
    for (const action of ['create', 'rename', 'duplicate']) document.getElementById(`scene-${action}`).addEventListener('click', () => {
      editingAction = action;
      sceneInput.value = action === 'create' ? '' : state?.name + (action === 'duplicate' ? ' (copy)' : '');
      document.getElementById('scene-dialog-error').textContent = '';
      sceneDialog.showModal(); sceneInput.focus();
    });
    document.getElementById('scene-dialog-cancel').addEventListener('click', () => sceneDialog.close());
    document.getElementById('scene-form').addEventListener('submit', async event => {
      event.preventDefault();
      const submit = event.currentTarget.querySelector('button[type=submit]'); submit.disabled = true;
      try {await sceneAction(editingAction, sceneInput.value.trim()); sceneDialog.close();}
      catch (error) {document.getElementById('scene-dialog-error').textContent = error.message;}
      finally {submit.disabled = false;}
    });
    document.getElementById('scene-delete').addEventListener('click', () => {if (confirm(messages.deleteScene)) sceneAction('delete').catch(busyMessage);});
    activateButton.addEventListener('click', activateScene);
    for (const action of ['next_round', 'reset']) document.getElementById(`encounter-${action}`).addEventListener('click', async () => {
      try {await changeEncounter(action);} catch (error) {busyMessage(error);}
    });
    document.getElementById('encounter-actor').addEventListener('change', event => {
      document.getElementById('encounter-add').disabled = !event.target.value || encounterBusy;
    });
    document.getElementById('encounter-add').addEventListener('click', async () => {
      const actor_id = document.getElementById('encounter-actor').value;
      if (actor_id) try {await changeEncounter('add', {actor_id});} catch (error) {busyMessage(error);}
    });
    document.getElementById('marker-create').addEventListener('click', async () => {
      try {
        const response = await fetch(url('markers'), {cache: 'no-store'}); if (!response.ok) throw new Error();
        const {entries} = await response.json(), dialog = document.getElementById('marker-detail'); dialog.replaceChildren();
        const choices = document.createElement('select'); choices.setAttribute('aria-label', messages.openMaterial);
        for (const entry of entries) {const option = document.createElement('option'); option.value = entry.id; option.textContent = entry.title; choices.append(option);}
        dialog.append(choices, button(messages.addMarker, async () => {
          const view = getApi().getAppState();
          accept(await request('markers', {markers_version: state.markers_version, action: 'create', entry_id: Number(choices.value),
            x: view.width / (2 * view.zoom.value) - view.scrollX, y: view.height / (2 * view.zoom.value) - view.scrollY})); dialog.close();
        }, !entries.length), button(messages.close, () => dialog.close())); dialog.showModal();
      } catch (error) {busyMessage(error);}
    });
  }
  function announcePresence() {
    if (!state || stopped || !socket.connected) return;
    socket.emit('whiteboard_presence', {...context(), party_id: config.partyId, visible: !document.hidden, csrf_token: config.csrfToken});
    refreshPresence();
  }
  async function refreshPresence() {
    if (!state || stopped || document.hidden) return;
    const run = ++presenceEpoch;
    try {
      const response = await fetch(url('presence'), {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json(); if (run !== presenceEpoch || stopped) return;
      const group = document.getElementById('board-presence'); group.replaceChildren();
      const members = presenceUsers(data.members), limit = window.matchMedia('(max-width: 600px)').matches ? 3 : 6;
      for (const member of members.slice(0, limit)) {
        const icon = document.createElement('span'); icon.className = `presence-avatar${member.visible ? '' : ' presence-away'}`;
        icon.textContent = member.label;
        icon.title = `${member.warden ? messages.warden : member.username}${member.characters.length ? ' · ' + member.characters.join(', ') : ''} · ${messages[member.visible ? 'viewing' : 'away']}`;
        icon.setAttribute('aria-label', icon.title);
        if (member.portrait) {const img = document.createElement('img'); img.alt = ''; img.referrerPolicy = 'no-referrer';
          img.addEventListener('error', () => img.remove()); img.src = member.portrait; icon.append(img);}
        group.append(icon);
      }
      if (members.length > limit) {const more = document.createElement('span'); more.className = 'presence-avatar'; more.textContent = '+' + (members.length - limit);
        more.title = members.slice(limit).map(member => member.username).join(', '); group.append(more);}
    } catch (_) {document.getElementById('board-presence')?.replaceChildren();}
  }
  const visible = () => {announcePresence(); if (!document.hidden) refresh();};
  const disconnected = () => document.getElementById('board-presence')?.replaceChildren();
  const presenceChanged = data => {if (data.party_id === config.partyId && data.scene_id === state?.scene_id) refreshPresence();};
  socket.on('connect', announcePresence); socket.on('disconnect', disconnected); socket.on('whiteboard_presence_changed', presenceChanged);
  document.addEventListener('visibilitychange', visible);
  const leave = () => {if (socket.connected) socket.emit('whiteboard_presence', {leave: true, csrf_token: config.csrfToken});};
  window.addEventListener('pagehide', leave);
  const membership = data => {if (data.party_id === config.partyId) {refreshPresence(); refresh();}};
  const catalogue = data => {if (data.party_id === config.partyId) {loadScenes(); refresh(true);}};
  socket.on('whiteboard_scenes_changed', catalogue);
  socket.on('party_members_changed', membership); socket.on('campaign_content_changed', membership);
  const poll = setInterval(() => {if (!document.hidden) refreshPresence();}, 15000);
  document.getElementById('editor').addEventListener('pointerup', event => {
    if (event.target.tagName !== 'CANVAS' || !state) return;
    const api = getApi(), view = api.getAppState();
    const x = (event.clientX - (view.offsetLeft || 0)) / view.zoom.value - view.scrollX;
    const y = (event.clientY - (view.offsetTop || 0)) / view.zoom.value - view.scrollY;
    const hit = [...tokens.values()].reverse().find(token => {
      if (isPreview() && !token.visible) return false;
      const e = {...token.element, ...pending.get(token.id)?.geometry}, a = -(e.angle || 0), dx = x-e.x-e.width/2, dy = y-e.y-e.height/2;
      return Math.abs(dx*Math.cos(a)-dy*Math.sin(a)) <= e.width/2 && Math.abs(dx*Math.sin(a)+dy*Math.cos(a)) <= e.height/2;
    });
    active = hit?.id || null; drawPanel();
  });
  return {context, accept, capture, insert, render, flush, actorSnapshot, initialDrawing, refreshEncounterPortraits,
    get busy() {return Boolean(pending.size || saving || statTimers.size || statSaves.size);},
    draft() {return [...tokens.values()].filter(token => pending.get(token.id)?.action !== 'delete').map(token => ({...token.element, ...pending.get(token.id)?.geometry}));},
    files() {return Object.assign({}, ...[...tokens.values()].map(token => token.files));},
    reset() {for (const task of statTimers.values()) clearTimeout(task.timer); statTimers.clear(); ++epoch; presenceScene = null; state = null; saving = null; pending.clear(); tokens.clear(); encounterPortraits.clear(); active = null; encounterBusy = false; syncPanels(); document.body?.classList.remove('board-token-selected'); panelSignature = ''; config.boardContext = {}; markerLayer.replaceChildren();},
    destroy() {for (const task of statTimers.values()) clearTimeout(task.timer); statTimers.clear(); stopped = true; ++epoch; leave(); clearTimeout(timer); clearInterval(poll); if (markersFrame !== null) cancelAnimationFrame(markersFrame);
      markerLayer.remove(); encounterPortraits.clear(); tokenPanel.hidden = true; document.body?.classList.remove('board-token-selected');
      document.getElementById('editor').removeEventListener('keydown', deleteKey, true); disconnected();
      document.removeEventListener('visibilitychange', visible); window.removeEventListener('pagehide', leave);
      socket.off('connect', announcePresence); socket.off('disconnect', disconnected); socket.off('whiteboard_presence_changed', presenceChanged);
      socket.off('whiteboard_scenes_changed', catalogue);
      socket.off('party_members_changed', membership); socket.off('campaign_content_changed', membership);},
  };
}

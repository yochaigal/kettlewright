import {restoreElements, CaptureUpdateAction} from 'excalidraw';

export function setupBoardControls({config, getApi, canEdit, socket}) {
  const sheet = document.getElementById('actor-sheet'), frame = document.getElementById('actor-frame');
  const selectedButton = document.getElementById('token-stats');
  let actor = null, displayedActorId = null;
  const visibilityForm = document.getElementById('board-monster-visibility');
  const sharedToggle = document.getElementById('board-monster-shared');
  const publicNotes = document.getElementById('board-monster-notes');
  const visibilityStatus = document.getElementById('board-visibility-status');
  let visibilityEpoch = 0, visibilityId = null, visibilitySaving = false;
  const visibilityUrl = id => config.visibilityUrl.replace('/0/visibility', `/${id}/visibility`);
  function resetVisibility() {
    ++visibilityEpoch; visibilityId = null; visibilitySaving = false;
    if (visibilityForm) {visibilityForm.hidden = true; visibilityForm.querySelector('details').open = false;}
  }
  async function loadVisibility(selected) {
    if (!visibilityForm || selected?.kind !== 'companion') return;
    const run = visibilityEpoch;
    visibilityForm.hidden = false;
    visibilityStatus.textContent = config.messages.tokensLoading;
    visibilityForm.querySelectorAll('input, textarea, button').forEach(input => {input.disabled = true;});
    try {
      const response = await fetch(visibilityUrl(selected.id), {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (run !== visibilityEpoch) return;
      if (response.status === 404) {visibilityForm.hidden = true; return;}
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      if (run !== visibilityEpoch) return;
      visibilityId = data.id; sharedToggle.checked = data.shared; publicNotes.value = data.public_notes;
      visibilityStatus.textContent = '';
      visibilityForm.querySelectorAll('input, textarea, button').forEach(input => {input.disabled = false;});
    } catch (_) {if (run === visibilityEpoch) visibilityStatus.textContent = config.messages.visibilityFailed;}
  }
  visibilityForm?.addEventListener('submit', async event => {
    event.preventDefault();
    if (visibilityId === null || visibilitySaving) return;
    const run = visibilityEpoch, id = visibilityId;
    const body = {shared: sharedToggle.checked, public_notes: publicNotes.value, csrf_token: config.csrfToken};
    visibilitySaving = true; visibilityStatus.textContent = config.messages.saving;
    visibilityForm.querySelectorAll('input, textarea, button').forEach(input => {input.disabled = true;});
    try {
      const response = await fetch(visibilityUrl(id), {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body), signal: AbortSignal.timeout(10000)});
      if (!response.ok || response.redirected) throw new Error();
      if (run === visibilityEpoch) visibilityStatus.textContent = config.messages.saved;
    } catch (_) {if (run === visibilityEpoch) visibilityStatus.textContent = config.messages.visibilityFailed;}
    finally {
      if (run === visibilityEpoch) {
        visibilitySaving = false;
        visibilityForm.querySelectorAll('input, textarea, button').forEach(input => {input.disabled = false;});
      }
    }
  });
  frame.addEventListener('load', () => {
    if (frame.contentDocument) frame.contentDocument.body.classList.add('board-embedded');
    if (frame.contentDocument && displayedActorId !== null
        && frame.contentWindow.location.pathname !== `/companions/${displayedActorId}`) resetVisibility();
  });
  function openSheet(url, selected = null) {
    displayedActorId = selected?.kind === 'companion' ? selected.id : null;
    resetVisibility(); loadVisibility(selected);
    frame.src = url;
    if (!sheet.open) sheet.show();
  }
  document.getElementById('close-actor').addEventListener('click', () => {resetVisibility(); sheet.close(); frame.src = 'about:blank';});
  sheet.addEventListener('close', resetVisibility);
  selectedButton.addEventListener('click', () => {
    if (!actor) return;
    const url = actor.kind === 'companion' ? config.actorsUrl : config.characterActorsUrl;
    openSheet(url.replace(/\/0$/, `/${actor.id}`), {...actor});
  });
  function selection(state) {
    const selected = Object.keys(state.selectedElementIds || {}).filter(id => state.selectedElementIds[id]);
    const companion = selected.length === 1 && selected[0].match(/^actor-companion-(\d+)-/);
    const character = selected.length === 1 && selected[0].match(/^actor-(\d+)-/);
    actor = companion ? {kind: 'companion', id: companion[1]} : character ? {kind: 'character', id: character[1]} : null;
    selectedButton.disabled = !actor;
  }
  if (config.warden) {
    document.getElementById('board-monsters').addEventListener('click', () => openSheet(config.monstersUrl));
    function lock(locked) {
      if (!canEdit()) return;
      const api = getApi();
      const elements = api.getSceneElements().map(element => {
        const change = !element.id.startsWith('actor-');
        if (!change || element.locked === locked) return element;
        return {...element, locked, version: element.version + 1, versionNonce: Math.floor(Math.random() * 2147483647)};
      });
      api.updateScene({elements: restoreElements(elements, null), captureUpdate: CaptureUpdateAction.IMMEDIATELY});
    }
    document.getElementById('lock-map').addEventListener('click', () => lock(true));
    document.getElementById('unlock-map').addEventListener('click', () => lock(false));
  }
  const rolls = document.getElementById('board-rolls'), form = document.getElementById('board-roll-form');
  const result = document.getElementById('board-roll-result'), history = document.getElementById('board-roll-history');
  let reading = false;
  async function refreshHistory() {
    if (!rolls.open || reading) return;
    reading = true;
    try {
      const response = await fetch(config.historyUrl, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (response.ok && !response.redirected && rolls.open) {
        history.innerHTML = await response.text();
        history.querySelectorAll('time[datetime]').forEach(time => {time.textContent = new Date(time.dateTime).toLocaleString();});
      }
    } catch (_) { /* Preserve the last acknowledged history while offline. */ }
    finally {reading = false;}
  }
  document.getElementById('board-dice').addEventListener('click', () => {if (!rolls.open) rolls.showModal(); refreshHistory();});
  document.getElementById('close-board-rolls').addEventListener('click', () => rolls.close());
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button'); button.disabled = true;
    const body = new FormData(form); body.set('csrf_token', config.csrfToken);
    try {
      const response = await fetch(config.rollUrl, {method: 'POST', body, signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error();
      result.textContent = (await response.json()).result; refreshHistory();
    } catch (_) {result.textContent = config.messages.rollFailed;}
    finally {button.disabled = false;}
  });
  socket.on('party_actors_changed', data => {
    if (data.party_id === config.partyId && sheet.open && frame.contentDocument?.getElementById('public-monster')) frame.contentWindow.location.reload();
  });
  socket.on('roll_history_changed', data => {if (data.party_id === config.partyId) refreshHistory();});
  const timer = setInterval(refreshHistory, 5000);
  return {selection, destroy() {resetVisibility(); clearInterval(timer); sheet.close(); rolls.close(); frame.src = 'about:blank';}};
}

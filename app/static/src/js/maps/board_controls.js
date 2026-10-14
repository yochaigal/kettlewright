import {restoreElements, CaptureUpdateAction} from 'excalidraw';

export function setupBoardControls({config, getApi, canEdit, socket}) {
  const sheet = document.getElementById('actor-sheet'), frame = document.getElementById('actor-frame');
  const selectedButton = document.getElementById('token-stats');
  let actor = null;
  frame.addEventListener('load', () => {
    if (frame.contentDocument) frame.contentDocument.body.classList.add('board-embedded');
  });
  function openSheet(url) {
    frame.src = url;
    if (!sheet.open) sheet.show();
  }
  document.getElementById('close-actor').addEventListener('click', () => {sheet.close(); frame.src = 'about:blank';});
  selectedButton.addEventListener('click', () => {
    if (!actor) return;
    const url = actor.kind === 'companion' ? config.actorsUrl : config.characterActorsUrl;
    openSheet(url.replace(/\/0$/, `/${actor.id}`));
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
  return {selection, destroy() {clearInterval(timer); sheet.close(); rolls.close(); frame.src = 'about:blank';}};
}

import {restoreElements, CaptureUpdateAction} from 'excalidraw';

export const initials = name => Array.from((name || '?').trim().split(/\s+/).slice(0, 2)
  .map(word => Array.from(word)[0]).join('')).join('').toLocaleUpperCase() || '?';

async function portraitImage(url) {
  if (!url) return null;
  return new Promise(resolve => {
    const image = new Image();
    const finish = value => {clearTimeout(timer); image.onload = image.onerror = null; resolve(value);};
    const timer = setTimeout(() => finish(null), 8000);
    image.crossOrigin = 'anonymous'; image.referrerPolicy = 'no-referrer';
    image.onload = () => finish(image.naturalWidth * image.naturalHeight <= 25000000 ? image : null);
    image.onerror = () => finish(null);
    image.src = url;
  });
}

export async function tokenPortrait(character) {
  const image = await portraitImage(character.portrait);
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.beginPath(); ctx.arc(128, 128, 122, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = '#e1defa'; ctx.fillRect(0, 0, 256, 256);
  if (image) {
    const side = Math.min(image.naturalWidth, image.naturalHeight);
    ctx.drawImage(image, (image.naturalWidth-side)/2, (image.naturalHeight-side)/2, side, side, 0, 0, 256, 256);
  } else {
    ctx.fillStyle = '#393253'; ctx.font = 'bold 88px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(initials(character.name), 128, 132, 210);
  }
  ctx.strokeStyle = '#8278c8'; ctx.lineWidth = 12; ctx.stroke();
  const dataURL = canvas.toDataURL('image/png');
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(dataURL));
  const id = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  return {file: {id, dataURL, mimeType: 'image/png', created: Date.now()},
    imageLoaded: Boolean(image), fallback: !image && !['pet', 'hireling'].includes(character.kind)};
}

export function tokenElement(fileId, state, id = crypto.randomUUID()) {
  return {id, type: 'image', fileId, status: 'saved', scale: [1, 1],
    x: state.width / (2 * state.zoom.value) - state.scrollX - 40,
    y: state.height / (2 * state.zoom.value) - state.scrollY - 40,
    width: 80, height: 80, angle: 0, opacity: 100, locked: false};
}

export function setupPartyTokens({editor, config, getApi, getGeneration, canInsert, beforeInsert, managedInsert}) {
  const dialog = document.getElementById('party-tokens');
  const grid = document.getElementById('tokens-grid'), status = document.getElementById('tokens-status');
  let epoch = 0, busy = false;
  const close = () => {++epoch; busy = false; if (dialog.open) dialog.close();};
  document.getElementById('mobile-party-tokens').addEventListener('click', open);
  document.getElementById('close-tokens').addEventListener('click', close);
  dialog.addEventListener('cancel', close);
  async function insert(character, portrait, generation, valid = () => true, point = null) {
    const {file, fallback} = await portrait;
    if (!valid() || generation !== getGeneration() || !canInsert()) return;
    const api = getApi(), state = api.getAppState();
    const element = tokenElement(file.id, state, `actor-${String(character.id).replace(':', '-')}-${crypto.randomUUID()}`);
    if (point) {
      element.x = (point.x - (state.offsetLeft || 0)) / state.zoom.value - state.scrollX - 40;
      element.y = (point.y - (state.offsetTop || 0)) / state.zoom.value - state.scrollY - 40;
    }
    beforeInsert();
    if (managedInsert) {await managedInsert(character, element, file); api.setActiveTool({type: 'selection'}); return;}
    api.addFiles([file]);
    api.updateScene({elements: [...api.getSceneElements(), ...restoreElements([element], null)],
      appState: {selectedElementIds: {[element.id]: true}}, captureUpdate: CaptureUpdateAction.IMMEDIATELY});
    api.setActiveTool({type: 'selection'});
    if (fallback) api.setToast({message: config.messages.tokenFallback});
  }
  const isActor = event => [...event.dataTransfer.types].includes('application/x-kettlewright-actor');
  editor.addEventListener('dragover', event => {
    if (!isActor(event)) return;
    event.preventDefault(); event.stopPropagation(); event.dataTransfer.dropEffect = canInsert() ? 'copy' : 'none';
  }, true);
  editor.addEventListener('drop', async event => {
    if (!isActor(event)) return;
    event.preventDefault(); event.stopPropagation();
    if (busy || !canInsert()) return;
    const id = event.dataTransfer.getData('application/x-kettlewright-actor');
    const generation = getGeneration(), point = {x: event.clientX, y: event.clientY};
    busy = true;
    try {
      const response = await fetch(config.tokensUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error();
      const {tokens} = await response.json(), character = tokens.find(token => String(token.id) === id);
      if (!character) throw new Error();
      await insert(character, tokenPortrait(character), generation, () => true, point);
    } catch (_) {getApi()?.setToast({message: config.messages.tokensFailed});}
    finally {busy = false;}
  }, true);
  async function open() {
    if (!canInsert() || dialog.open) return;
    const run = ++epoch, generation = getGeneration();
    dialog.showModal(); grid.replaceChildren(); status.textContent = config.messages.tokensLoading;
    try {
      const response = await fetch(config.tokensUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error();
      const {tokens} = await response.json();
      if (run !== epoch) return;
      status.textContent = tokens.length ? '' : config.messages.tokensEmpty;
      for (const character of tokens) {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'party-token';
        const avatar = document.createElement('span'); avatar.className = 'token-avatar'; avatar.textContent = initials(character.name);
        const name = document.createElement('span'); name.textContent = character.name;
        button.append(avatar, name); grid.append(button);
        if (character.kind === 'pet' || ['hireling', 'monster'].includes(character.kind)) {
          const caption = document.createElement('small');
          caption.textContent = `${config.messages[character.kind]} · ${character.parent}`;
          button.append(caption);
        }
        const portrait = tokenPortrait(character).then(result => {
          if (run === epoch) {
            const img = document.createElement('img'); img.src = result.file.dataURL; img.alt = '';
            avatar.replaceChildren(img);
            if (result.fallback) button.title = config.messages.tokenFallback;
          }
          return result;
        });
        // Attach a rejection handler immediately, even before a token is chosen.
        portrait.catch(() => {if (run === epoch) button.title = config.messages.tokensFailed;});
        button.addEventListener('click', async () => {
          if (busy || !canInsert()) return;
          busy = true; grid.setAttribute('aria-busy', 'true'); status.textContent = config.messages.tokensLoading;
          try {
            await insert(character, portrait, generation, () => run === epoch);
            if (run === epoch) close();
          } catch (_) {if (run === epoch) status.textContent = config.messages.tokensFailed;}
          finally {if (run === epoch) busy = false; grid.removeAttribute('aria-busy');}
        });
      }
    } catch (_) {if (run === epoch) status.textContent = config.messages.tokensFailed;}
  }
  return {open, close};
}

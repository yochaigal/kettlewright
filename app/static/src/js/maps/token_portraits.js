import {CaptureUpdateAction} from 'excalidraw';
import {actorKey} from './token_stats.js';
import {tokenPortrait} from './party_tokens.js';

// Project current artwork locally. The stored scene keeps its original image so
// refreshing a portrait never edits the board, its locks, or another user's undo.
export function createTokenPortraits({config, getApi, socket, onProjection,
  renderPortrait = tokenPortrait}) {
  const artwork = new Map(), originals = new Map();
  let stopped = false, epoch = 0, frame = null, refreshing = false;
  function redraw() {
    if (!stopped && frame === null) frame = requestAnimationFrame(draw);
  }
  function draw() {
    frame = null;
    const api = getApi();
    if (!api || stopped) return;
    const files = [], elements = api.getSceneElements().map(element => {
      const file = artwork.get(actorKey(element.id))?.file;
      if (!file || element.type !== 'image' || element.isDeleted) return element;
      const original = originals.get(element.fileId) || element.fileId;
      // Each original image has its own projection, even when actors share artwork.
      const id = `live-${original}-${file.id}`;
      if (element.fileId === id) return element;
      originals.set(id, original);
      files.push({...file, id});
      return {...element, fileId: id};
    });
    if (!files.length) return;
    onProjection(() => {
      api.addFiles(files);
      api.updateScene({elements, captureUpdate: CaptureUpdateAction.NEVER});
    });
  }
  async function refresh() {
    if (stopped || refreshing) return;
    refreshing = true;
    const run = ++epoch;
    try {
      const response = await fetch(config.portraitsUrl, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok || response.redirected) throw new Error();
      const {portraits} = await response.json();
      await Promise.all(portraits.map(async actor => {
        const signature = JSON.stringify([actor.portrait, actor.portrait ? '' : actor.name]);
        if (artwork.get(actor.id)?.signature === signature) return;
        try {
          const result = await renderPortrait(actor);
          if (run !== epoch || stopped || (actor.portrait && !result.imageLoaded)) return;
          artwork.set(actor.id, {signature, file: result.file});
        } catch (_) { /* Keep the existing token if a remote portrait cannot load. */ }
      }));
      if (run !== epoch || stopped) return;
      const ids = new Set(portraits.map(actor => actor.id));
      for (const id of artwork.keys()) if (!ids.has(id)) artwork.delete(id);
      redraw();
    } catch (_) { /* Retry on the next roster event or poll without removing artwork. */ }
    finally {refreshing = false;}
  }
  const changed = data => {if (data.party_id === config.partyId) refresh();};
  const visible = () => {if (!document.hidden) refresh();};
  socket.on('party_actors_changed', changed); socket.on('party_members_changed', changed); socket.on('connect', refresh);
  document.addEventListener('visibilitychange', visible);
  const timer = setInterval(refresh, 5000);
  refresh();
  return {redraw,
    // All save/merge comparisons use canonical IDs, including projected undo states.
    elements(elements) {
      return elements.map(element => originals.has(element.fileId)
        ? {...element, fileId: originals.get(element.fileId)} : element);
    },
    destroy() {
      stopped = true; ++epoch; clearInterval(timer);
      if (frame !== null) cancelAnimationFrame(frame);
      socket.off('party_actors_changed', changed); socket.off('party_members_changed', changed); socket.off('connect', refresh);
      document.removeEventListener('visibilitychange', visible);
      artwork.clear(); originals.clear();
    }};
}

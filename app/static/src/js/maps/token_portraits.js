import {CaptureUpdateAction} from 'excalidraw';
import {actorKey} from './token_stats.js';
import {tokenPortrait} from './party_tokens.js';

// Project current artwork locally. The stored scene keeps its original image so
// refreshing a portrait never edits the board, its locks, or another user's undo.
export function createTokenPortraits({getApi, updates, onProjection,
  renderPortrait = tokenPortrait}) {
  const artwork = new Map(), originals = new Map();
  let stopped = false, epoch = 0, frame = null;
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
  const unsubscribe = updates.subscribe('portraits', async portraits => {
    if (stopped || !portraits) return;
    const run = ++epoch;
    try {
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
    } catch (_) { /* Keep existing artwork until the next update. */ }
  });
  return {redraw,
    // All save/merge comparisons use canonical IDs, including projected undo states.
    elements(elements) {
      return elements.map(element => originals.has(element.fileId)
        ? {...element, fileId: originals.get(element.fileId)} : element);
    },
    destroy() {
      stopped = true; ++epoch; unsubscribe();
      if (frame !== null) cancelAnimationFrame(frame);
      artwork.clear(); originals.clear();
    }};
}

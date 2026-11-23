// Clean view (Discord feedback): every canvas can hide Excalidraw's drawing tools and its zoom and undo controls, from
// toggle buttons beside it (pressed = shown), like the whiteboard's Warden tools and dice roller. Remembered per kind
// of canvas: 'kw-board-ui' for the whiteboard, 'kw-map-ui' for maps. The classes are styled in css/canvas_ui.css.
// 'fog' is the Warden's fog row on a party's map: the page shows or hides it (party_map.html).
export const CANVAS_GROUPS = ['drawing', 'zoom', 'fog'];

export function readCanvasUI(key, storage = () => globalThis.localStorage) {
  let saved = {};
  try {saved = JSON.parse(storage()?.getItem(key) || '{}') || {};} catch (_) { /* Optional preference. */ }
  return Object.fromEntries(CANVAS_GROUPS.map(group => [group, saved[group] !== false]));
}

export function writeCanvasUI(key, ui, storage = () => globalThis.localStorage) {
  try {storage()?.setItem(key, JSON.stringify(ui));} catch (_) { /* Optional preference. */ }
}

export function applyCanvasUI(target, ui = {}) {
  target?.classList?.toggle('hide-drawing-tools', ui.drawing === false);
  target?.classList?.toggle('hide-zoom', ui.zoom === false);
}

// The whiteboard: its toggles are buttons with data-canvas-ui="drawing" or "zoom" in its top bar.
export function bindCanvasToggles({buttons, key, target, storage}) {
  const ui = readCanvasUI(key, storage);
  const show = () => {
    applyCanvasUI(target, ui);
    for (const button of buttons) button.setAttribute('aria-pressed', String(ui[button.dataset.canvasUi] !== false));
  };
  for (const button of buttons) button.addEventListener('click', () => {
    ui[button.dataset.canvasUi] = !ui[button.dataset.canvasUi];
    writeCanvasUI(key, ui, storage); show();
  });
  show();
  return ui;
}

// The Dungeon brush (#439): an overlay above Excalidraw, like the fog brush.
// Dragging highlights squares; releasing rebuilds the dungeon's shapes in one
// undoable step, and the whiteboard saves and shares them like any drawing.
// With Shift (#498) the brush and eraser fill a rectangle: Shift-drag from one corner to the other,
// or Shift-click a corner, move, and click the other corner. Escape cancels.
import {DEFAULT_SIZE, STYLE, boardSize, cellsAlong, cellsInBox, cycleEdge, dungeonFromShapes, dungeonPart,
  dungeonShapes, edgeAt, edgeKind, floorColor, paint} from './whiteboard_dungeon.js';

const MAX_ELEMENTS = 2000; // map_drawing.validate_drawing
const GEOMETRY = ['x', 'y', 'width', 'height', 'strokeWidth', 'strokeColor', 'backgroundColor', 'opacity'];
const nonce = () => Math.floor(Math.random() * 2147483647);

// The scene after replacing the board's dungeon with `shapes`. Unchanged shapes
// keep their elements; removed ones are marked deleted so undo and sync see them.
export function nextScene(all, size, shapes, toElements) {
  const existing = new Map(all.filter(element => dungeonPart(element.id)?.size === size).map(element => [element.id, element]));
  const wanted = new Set(shapes.map(shape => shape.id));
  const changed = shapes.filter(shape => {
    const old = existing.get(shape.id);
    return !old || old.isDeleted || GEOMETRY.some(key => key in shape && old[key] !== shape[key]);
  });
  const fresh = new Map(toElements(changed).map(element => {
    const old = existing.get(element.id);
    return [element.id, old ? {...element, version: old.version + 1, versionNonce: nonce()} : element];
  }));
  const dungeon = shapes.map(shape => fresh.get(shape.id) || existing.get(shape.id));
  const removed = [...existing.values()].filter(element => !element.isDeleted && !wanted.has(element.id))
    .map(element => ({...element, isDeleted: true, version: element.version + 1, versionNonce: nonce()}));
  const others = all.filter(element => !existing.has(element.id));
  const count = others.filter(element => !element.isDeleted).length + dungeon.length;
  return {elements: [...dungeon, ...removed, ...others], count, tooBig: count > MAX_ELEMENTS};
}

export function createDungeonLayer({editor, getApi, canEdit, toElements, captureUpdate, onTooBig, onChange}) {
  const canvas = document.createElement('canvas');
  canvas.className = 'whiteboard-dungeon';
  canvas.setAttribute('aria-hidden', 'true');
  let tool = '', host = null, frame = null, color = STYLE.floor;
  let active = null, pan = null, space = false, hover = null;

  const scene = () => getApi()?.getSceneElementsIncludingDeleted() || [];
  // One square per token; a board drawn earlier at another size keeps its own.
  const size = () => boardSize(scene()) ?? DEFAULT_SIZE;
  const current = () => dungeonFromShapes(scene(), size());
  function point(event) {
    const state = getApi().getAppState(), rect = host.getBoundingClientRect();
    return [(event.clientX - rect.left) / state.zoom.value - state.scrollX,
      (event.clientY - rect.top) / state.zoom.value - state.scrollY];
  }

  function draw() {
    frame = null;
    const nextHost = editor.querySelector('.excalidraw'), api = getApi();
    if (!nextHost || !api) return;
    if (host !== nextHost) {host = nextHost; host.insertBefore(canvas, host.querySelector(':scope > .SVGLayer'));}
    const rect = host.getBoundingClientRect(), ratio = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(rect.width * ratio) || canvas.height !== Math.round(rect.height * ratio)) {
      canvas.width = Math.round(rect.width * ratio); canvas.height = Math.round(rect.height * ratio);
    }
    const enabled = Boolean(tool) && canEdit();
    canvas.style.pointerEvents = enabled ? 'auto' : 'none';
    canvas.style.cursor = !enabled ? '' : pan ? 'grabbing' : tool === 'door' ? 'pointer' : 'crosshair';
    const ctx = canvas.getContext('2d'), state = api.getAppState(), zoom = state.zoom.value, s = size();
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);
    if (!enabled) return;
    ctx.setTransform(ratio * zoom, 0, 0, ratio * zoom, state.scrollX * zoom * ratio, state.scrollY * zoom * ratio);
    if (active?.cells) {
      // The squares about to be painted, in the brush's color (#453).
      ctx.fillStyle = active.erase ? 'rgba(200, 60, 60, .35)' : color;
      ctx.globalAlpha = active.erase ? 1 : .7;
      ctx.strokeStyle = active.erase ? '#c83c3c' : '#3c78c8';
      ctx.lineWidth = 2 / zoom;
      for (const key of active.cells) {
        const [c, r] = key.split(',').map(Number);
        ctx.fillRect(c * s, r * s, s, s); ctx.strokeRect(c * s, r * s, s, s);
      }
      ctx.globalAlpha = 1;
    }
    if (tool === 'door' && hover) {
      const [kind, c, r] = hover.split(':'), x = Number(c) * s, y = Number(r) * s;
      ctx.strokeStyle = '#3c78c8'; ctx.lineWidth = Math.max(4, s / 8); ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(kind === 'h' ? x + s : x, kind === 'h' ? y : y + s); ctx.stroke();
    }
  }
  function redraw() {if (frame === null) frame = requestAnimationFrame(draw);}

  function commit(change) {
    const api = getApi();
    if (!api || !canEdit()) return;
    const s = size(), dungeon = current(), next = change(dungeon);
    if (next === dungeon) return;
    const result = nextScene(scene(), s, dungeonShapes(next), toElements);
    if (result.tooBig) {onTooBig(); return;}
    api.updateScene({elements: result.elements, captureUpdate});
    onChange?.();
  }

  function finish() {
    const stroke = active; active = null;
    if (stroke?.cells?.size) commit(dungeon => paint(dungeon, stroke.cells, stroke.erase, color));
    redraw();
  }
  function end(event) {
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    // A Shift-click that did not drag sets the rectangle's first corner; the next click sets the other.
    if (active?.box && !active.waiting && Math.hypot(event.clientX - active.start[0], event.clientY - active.start[1]) < 5) {
      active.waiting = true; redraw(); return;
    }
    pan = null; finish();
  }

  canvas.addEventListener('pointerdown', event => {
    if (active?.waiting && event.button === 0) {
      // The second click of a Shift rectangle: its other corner.
      event.preventDefault(); event.stopPropagation();
      active.cells = cellsInBox(active.anchor, point(event), size());
      finish();
      return;
    }
    if (!tool || !canEdit() || active || pan || !host) return;
    if (event.button !== 0 && event.button !== 1) return;
    event.preventDefault(); event.stopPropagation();
    canvas.setPointerCapture(event.pointerId);
    if (event.button === 1 || space) {pan = [event.clientX, event.clientY]; redraw(); return;}
    const at = point(event), s = size();
    if (tool === 'door') {
      const edge = edgeAt(...at, s);
      commit(dungeon => edgeKind(dungeon, edge) ? cycleEdge(dungeon, edge) : dungeon);
      return;
    }
    const erase = tool === 'erase' || event.altKey;
    active = event.shiftKey
      ? {box: true, anchor: at, start: [event.clientX, event.clientY], erase, cells: cellsInBox(at, at, s)}
      : {last: at, erase, cells: cellsAlong(at, at, s)};
    redraw();
  });
  canvas.addEventListener('pointermove', event => {
    if (!host || !getApi()) return;
    if (pan) {
      const state = getApi().getAppState();
      getApi().updateScene({appState: {scrollX: state.scrollX + (event.clientX - pan[0]) / state.zoom.value,
        scrollY: state.scrollY + (event.clientY - pan[1]) / state.zoom.value}});
      pan = [event.clientX, event.clientY];
    } else if (active?.box) {
      active.cells = cellsInBox(active.anchor, point(event), size());
    } else if (active) {
      const at = point(event), s = size();
      if (active.cells.size < 20000) for (const cell of cellsAlong(active.last, at, s)) active.cells.add(cell);
      active.last = at;
    } else if (tool === 'door') hover = edgeAt(...point(event), size());
    redraw();
  });
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', () => {active = null; pan = null; redraw();});
  canvas.addEventListener('pointerleave', () => {hover = null; redraw();});
  // The overlay sits above Excalidraw, so scroll and pinch-zoom the board here.
  canvas.addEventListener('wheel', event => {
    const api = getApi();
    if (!api || !host) return;
    event.preventDefault();
    const state = api.getAppState(), rect = host.getBoundingClientRect();
    if (event.ctrlKey || event.metaKey) {
      const zoom = Math.min(30, Math.max(.1, state.zoom.value * Math.exp(-event.deltaY / 300)));
      const sx = event.clientX - rect.left, sy = event.clientY - rect.top;
      const wx = sx / state.zoom.value - state.scrollX, wy = sy / state.zoom.value - state.scrollY;
      api.updateScene({appState: {zoom: {value: zoom}, scrollX: sx / zoom - wx, scrollY: sy / zoom - wy}});
    } else {
      api.updateScene({appState: {scrollX: state.scrollX - event.deltaX / state.zoom.value,
        scrollY: state.scrollY - event.deltaY / state.zoom.value}});
    }
    redraw();
  }, {passive: false});
  const keys = event => {
    if (event.code === 'Space') space = event.type === 'keydown';
    if (event.type === 'keydown' && event.key === 'Escape' && active) {active = null; redraw();}
  };
  window.addEventListener('keydown', keys); window.addEventListener('keyup', keys);
  const resize = new ResizeObserver(redraw); resize.observe(editor);

  return {
    redraw,
    tool: () => tool,
    setTool(value) {tool = value; active = null; hover = null; redraw();},
    color: () => color,
    setColor(value) {color = floorColor(value); redraw();},
    clear() {commit(dungeon => dungeon.cells.size ? {...dungeon, cells: new Map(), edges: new Map()} : dungeon);},
    hasDungeon: () => boardSize(scene()) !== null,
    destroy() {
      resize.disconnect(); window.removeEventListener('keydown', keys); window.removeEventListener('keyup', keys);
      if (frame !== null) cancelAnimationFrame(frame); canvas.remove();
    },
  };
}

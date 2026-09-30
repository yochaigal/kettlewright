export function applyFogOperation(fog, operation) {
  if (fog.applied?.includes(operation.id)) return fog;
  if (operation.type === 'disable') return {...fog, enabled: false};
  if (operation.type === 'hide_all' || operation.type === 'reveal_all') {
    return {...fog, enabled: true, base: operation.type === 'hide_all' ? 'covered' : 'clear', strokes: []};
  }
  if (operation.type === 'undo') return {...fog, strokes: fog.strokes.slice(0, -1)};
  return {...fog, strokes: [...fog.strokes, operation]};
}

export const fogPoint = (x, y, rect, state) => [
  (x - rect.left) / state.zoom.value - state.scrollX,
  (y - rect.top) / state.zoom.value - state.scrollY,
];

// Paint an opaque logical mask first, then apply role opacity to the whole layer.
export function paintFog(ctx, width, height, fog, state, ratio = 1) {
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  if (!fog.enabled) return;
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#171923';
  ctx.strokeStyle = '#171923';
  if (fog.base === 'covered') ctx.fillRect(0, 0, width, height);
  const zoom = state.zoom.value;
  ctx.setTransform(ratio * zoom, 0, 0, ratio * zoom, state.scrollX * zoom * ratio, state.scrollY * zoom * ratio);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const stroke of fog.strokes) {
    ctx.globalCompositeOperation = stroke.type === 'reveal' ? 'destination-out' : 'source-over';
    ctx.lineWidth = stroke.radius * 2;
    ctx.beginPath();
    ctx.arc(stroke.points[0][0], stroke.points[0][1], stroke.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    stroke.points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.stroke();
  }
  ctx.globalCompositeOperation = 'source-over';
}

export function createFogLayer({editor, getApi, warden, onOperation}) {
  const canvas = document.createElement('canvas');
  canvas.className = 'whiteboard-fog';
  canvas.setAttribute('aria-hidden', 'true');
  const cursor = document.createElement('div');
  cursor.className = 'fog-brush-cursor';
  let fog = {enabled: false, base: 'covered', strokes: []}, tool = '', radius = 60;
  let preview = false, active = null, frame = null, host = null, pan = null, space = false;
  function draw() {
    frame = null;
    const nextHost = editor.querySelector('.excalidraw');
    if (!nextHost || !getApi()) return;
    if (host !== nextHost) {
      host = nextHost;
      // Native laser SVGs share z-index 3; fog must precede them in paint order.
      host.insertBefore(canvas, host.querySelector(':scope > .SVGLayer')); host.append(cursor);
    }
    const rect = host.getBoundingClientRect(), ratio = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(rect.width * ratio) || canvas.height !== Math.round(rect.height * ratio)) {
      canvas.width = Math.round(rect.width * ratio); canvas.height = Math.round(rect.height * ratio);
    }
    canvas.style.opacity = warden && !preview ? '0.45' : '1';
    canvas.style.pointerEvents = warden && tool && fog.enabled && !preview ? 'auto' : 'none';
    paintFog(canvas.getContext('2d'), rect.width, rect.height,
      active ? {...fog, strokes: [...fog.strokes, active]} : fog, getApi().getAppState(), ratio);
  }
  function redraw() {if (frame === null) frame = requestAnimationFrame(draw);}
  function point(event) {return fogPoint(event.clientX, event.clientY, host.getBoundingClientRect(), getApi().getAppState());}
  function end(event) {
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (active) {const stroke = active; active = null; onOperation(stroke);}
    pan = null; redraw();
  }
  canvas.addEventListener('pointerdown', event => {
    if (!warden || !tool || preview || !fog.enabled || active || pan) return;
    if (event.button !== 0 && event.button !== 1) return;
    event.preventDefault(); event.stopPropagation();
    canvas.setPointerCapture(event.pointerId);
    if (event.button === 1 || space) pan = [event.clientX, event.clientY];
    else active = {id: crypto.randomUUID(), type: tool, radius, points: [point(event)]};
    redraw();
  });
  canvas.addEventListener('pointermove', event => {
    if (!host || !getApi()) return;
    const state = getApi().getAppState(), rect = host.getBoundingClientRect();
    const size = radius * state.zoom.value * 2;
    Object.assign(cursor.style, {display: tool && !preview ? 'block' : 'none', width: `${size}px`, height: `${size}px`,
      left: `${event.clientX - rect.left}px`, top: `${event.clientY - rect.top}px`});
    if (pan) {
      getApi().updateScene({appState: {scrollX: state.scrollX + (event.clientX-pan[0])/state.zoom.value,
        scrollY: state.scrollY + (event.clientY-pan[1])/state.zoom.value}});
      pan = [event.clientX, event.clientY];
    } else if (active && active.points.length < 5000) {
      const next = point(event), last = active.points.at(-1);
      if (Math.hypot(next[0]-last[0], next[1]-last[1]) > Math.max(1, radius/8)) active.points.push(next);
    }
    redraw();
  });
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', () => {active = null; pan = null; redraw();});
  canvas.addEventListener('pointerleave', () => {cursor.style.display = 'none';});
  const keys = event => {if (event.code === 'Space') space = event.type === 'keydown';};
  window.addEventListener('keydown', keys); window.addEventListener('keyup', keys);
  const resize = new ResizeObserver(redraw); resize.observe(editor);
  return {
    redraw,
    setState(value) {fog = value; redraw();},
    setTool(value) {tool = value; active = null; cursor.style.display = 'none'; redraw();},
    setRadius(value) {radius = value;},
    setPreview(value) {preview = value; active = null; cursor.style.display = 'none'; redraw();},
    destroy() {resize.disconnect(); window.removeEventListener('keydown', keys); window.removeEventListener('keyup', keys);
      if (frame !== null) cancelAnimationFrame(frame); canvas.remove(); cursor.remove();},
  };
}

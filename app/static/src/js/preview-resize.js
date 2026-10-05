// Keep the opposite edge fixed when resizing from the top or left.
export function previewResize(bounds, direction, dx, dy, viewportWidth, viewportHeight) {
  const margin = 8;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  let {left, top, right, bottom} = bounds;
  const minWidth = Math.min(240, bounds.width, viewportWidth - 2 * margin);
  const minHeight = Math.min(160, bounds.height, viewportHeight - 2 * margin);
  if (direction.includes('w')) left = clamp(left + dx, margin, right - minWidth);
  if (direction.includes('e')) right = clamp(right + dx, left + minWidth, viewportWidth - margin);
  if (direction.includes('n')) top = clamp(top + dy, margin, bottom - minHeight);
  if (direction.includes('s')) bottom = clamp(bottom + dy, top + minHeight, viewportHeight - margin);
  return {left, top, width: right - left, height: bottom - top};
}

export function addPreviewResizeHandles(panel, onStart, onEnd) {
  for (const direction of ['n', 'e', 's', 'w', 'ne', 'se', 'sw', 'nw']) {
    const handle = document.createElement('div');
    handle.className = 'article-preview-resize';
    handle.dataset.direction = direction;
    handle.setAttribute('aria-hidden', 'true');
    panel.append(handle);
    handle.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      const bounds = panel.getBoundingClientRect();
      const x = event.clientX, y = event.clientY;
      handle.setPointerCapture(event.pointerId);
      panel.classList.add('article-preview-resizing');
      // Replace the initial placement limit with the full viewport limit.
      panel.style.maxHeight = 'calc(100vh - 16px)';
      panel.style.width = bounds.width + 'px';
      panel.style.height = bounds.height + 'px';
      onStart();
      handle.onpointermove = move => {
        if (move.pointerId !== event.pointerId) return;
        const size = previewResize(bounds, direction, move.clientX - x, move.clientY - y, innerWidth, innerHeight);
        for (const [property, value] of Object.entries(size)) panel.style[property] = value + 'px';
      };
      const finish = end => {
        if (end.pointerId !== event.pointerId) return;
        handle.onpointermove = handle.onpointerup = handle.onpointercancel = handle.onlostpointercapture = null;
        if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
        panel.classList.remove('article-preview-resizing');
        onEnd();
      };
      handle.onpointerup = handle.onpointercancel = handle.onlostpointercapture = finish;
    });
  }
}

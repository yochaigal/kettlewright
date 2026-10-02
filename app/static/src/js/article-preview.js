// Delegated listeners also cover dynamically rendered map/article links.
export function previewURL(href, origin = location.origin) {
  const url = new URL(href, origin);
  if (url.origin !== origin) return null;
  if (/^\/materials\/[1-9]\d*\/edit\/?$/.test(url.pathname))
    return url.pathname.replace(/\/edit\/?$/, '/preview');
  if (/^\/party\/[1-9]\d*\/materials\/[1-9]\d*\/?$/.test(url.pathname))
    return url.pathname.replace(/\/$/, '') + '/preview';
  return null;
}

let transient, openTimer, closeTimer, layer = 1100;
const labels = document.documentElement.lang?.startsWith('ru')
  ? {preview:'Предпросмотр', pin:'Закрепить', pinned:'Закреплено', close:'Закрыть', loading:'Загрузка…', error:'Не удалось загрузить статью.'}
  : {preview:'Preview', pin:'Pin', pinned:'Pinned', close:'Close', loading:'Loading…', error:'Unable to load article.'};
function close(panel) {
  panel?.resizeObserver?.disconnect();
  clearTimeout(panel?.fitTimer);
  panel?.controller.abort();
  panel?.remove();
  if (transient === panel) transient = null;
}
function scheduleClose() {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  closeTimer = setTimeout(() => close(transient), 250);
}
async function show(link, url) {
  close(transient);
  const panel = document.createElement('section');
  panel.className = 'article-preview';
  panel.dataset.previewUrl = url;
  panel.setAttribute('role', 'region');
  panel.setAttribute('aria-label', labels.preview + ': ' + link.textContent.trim());
  panel.innerHTML = '<header class="article-preview-bar"><span></span><button type="button" data-pin></button><button type="button" data-close></button></header><div class="article-preview-content" aria-live="polite"></div>';
  const bar = panel.querySelector('header'), content = panel.querySelector('.article-preview-content');
  bar.querySelector('span').textContent = labels.preview;
  const pin = bar.querySelector('[data-pin]');
  pin.textContent = labels.pin;
  const dismiss = bar.querySelector('[data-close]');
  dismiss.textContent = '×'; dismiss.setAttribute('aria-label', labels.close);
  content.textContent = labels.loading;
  panel.controller = new AbortController();
  transient = panel;
  document.body.append(panel);
  const rect = link.getBoundingClientRect();
  panel.style.left = Math.max(8, Math.min(rect.left, innerWidth - panel.offsetWidth - 8)) + 'px';
  panel.style.top = Math.max(8, Math.min(rect.bottom + 6, innerHeight - panel.offsetHeight - 8)) + 'px';
  panel.style.zIndex = ++layer;
  panel.addEventListener('pointerenter', () => clearTimeout(closeTimer));
  panel.addEventListener('pointerleave', () => { if (transient === panel) scheduleClose(); });
  panel.addEventListener('focusin', () => clearTimeout(closeTimer));
  pin.onclick = () => {
    if (transient === panel) transient = null;
    pin.textContent = labels.pinned; pin.disabled = true;
  };
  dismiss.onclick = () => close(panel);
  bar.addEventListener('pointerdown', event => {
    if (event.target.closest('button')) return;
    const bounds = panel.getBoundingClientRect(), x = event.clientX, y = event.clientY;
    bar.setPointerCapture(event.pointerId);
    panel.style.zIndex = ++layer;
    bar.onpointermove = move => {
      panel.style.left = Math.max(8, Math.min(innerWidth - panel.offsetWidth - 8, bounds.left + move.clientX - x)) + 'px';
      panel.style.top = Math.max(8, Math.min(innerHeight - panel.offsetHeight - 8, bounds.top + move.clientY - y)) + 'px';
    };
    bar.onpointerup = bar.onpointercancel = () => { bar.onpointermove = null; };
  });
  try {
    const response = await fetch(url, {signal: panel.controller.signal, headers: {'Accept':'text/html'}});
    if (!response.ok || response.redirected) throw new Error('Unavailable');
    content.innerHTML = await response.text(); // Server renders sanitized rich content and escaped metadata.
    if (content.querySelector('.article-preview-map') && panel.isConnected) {
      panel.classList.add('article-preview-with-map');
      panel.style.left = Math.max(8, Math.min(parseFloat(panel.style.left), innerWidth - panel.offsetWidth - 8)) + 'px';
      panel.style.top = Math.max(8, Math.min(parseFloat(panel.style.top), innerHeight - panel.offsetHeight - 8)) + 'px';
      const canvas = content.querySelector('.article-preview-map-canvas');
      panel.resizeObserver = new ResizeObserver(() => {
        clearTimeout(panel.fitTimer);
        panel.fitTimer = setTimeout(() => {
          canvas.contentWindow?.postMessage({channel:'kw-map', type:'fit'}, location.origin);
        }, 120);
      });
      panel.resizeObserver.observe(canvas);
    }
  } catch (error) {
    if (error.name !== 'AbortError') content.textContent = labels.error;
  }
}
function enter(event) {
  const link = event.target.closest('a[href]');
  if (!link || link.contains(event.relatedTarget)) return;
  const url = previewURL(link.href);
  if (!url) return;
  if (link.closest('.article-preview')?.dataset.previewUrl === url) return;
  clearTimeout(openTimer); clearTimeout(closeTimer);
  openTimer = setTimeout(() => show(link, url), 350);
}
document.addEventListener('pointerover', event => { if (event.pointerType !== 'touch') enter(event); });
document.addEventListener('focusin', enter);
document.addEventListener('pointerout', event => {
  const link = event.target.closest('a[href]');
  if (link && previewURL(link.href) && !link.contains(event.relatedTarget)) scheduleClose();
});
document.addEventListener('focusout', event => {
  if (!event.relatedTarget?.closest('.article-preview')) scheduleClose();
});
document.addEventListener('keydown', event => { if (event.key === 'Escape') close(transient); });

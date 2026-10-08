import {previewPosition} from './preview-position.js';
import {addPreviewResizeHandles} from './preview-resize.js';

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
  ? {preview:'Предпросмотр', move:'Переместить', pin:'Закрепить', unpin:'Открепить', close:'Закрыть', loading:'Загрузка…', error:'Не удалось загрузить статью.'}
  : {preview:'Preview', move:'Move', pin:'Pin', unpin:'Unpin', close:'Close', loading:'Loading…', error:'Unable to load article.'};
const icon = paths => '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + paths + '</svg>';
function close(panel) {
  panel?.resizeObserver?.disconnect();
  panel?.contentObserver?.disconnect();
  clearTimeout(panel?.fitTimer);
  panel?.controller.abort();
  panel?.remove();
  if (transient === panel) transient = null;
}
function scheduleClose() {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  if (transient?.interacting) return;
  closeTimer = setTimeout(() => close(transient), 250);
}
function position(panel, link) {
  panel.style.maxHeight='';
  const placement=previewPosition(link.getBoundingClientRect(),panel.offsetWidth,panel.offsetHeight,innerWidth,innerHeight);
  panel.style.left=placement.left+'px';
  panel.style.top=placement.top+'px';
  panel.style.maxHeight=Math.max(0,placement.maxHeight)+'px';
}
function fitContent(panel, content, bar) {
  const last = content.lastElementChild;
  if (!last || panel.manuallySized) return;
  const panelStyle = getComputedStyle(panel), contentStyle = getComputedStyle(content);
  const contentHeight = last.getBoundingClientRect().bottom - content.getBoundingClientRect().top
    + parseFloat(getComputedStyle(last).marginBottom) + parseFloat(contentStyle.paddingBottom);
  const frameHeight = ['paddingTop', 'paddingBottom', 'borderTopWidth', 'borderBottomWidth']
    .reduce((sum, property) => sum + parseFloat(panelStyle[property]), 0);
  panel.style.height = Math.ceil(contentHeight + bar.offsetHeight + frameHeight) + 'px';
}
async function show(link, url) {
  close(transient);
  const panel = document.createElement('section');
  panel.className = 'article-preview';
  panel.dataset.previewUrl = url;
  panel.setAttribute('role', 'region');
  panel.setAttribute('aria-label', labels.preview + ': ' + link.textContent.trim());
  panel.innerHTML = '<header class="article-preview-bar"><h2 class="article-preview-title"></h2><button type="button" data-drag></button><button type="button" data-pin aria-pressed="false"></button><button type="button" data-close></button></header><div class="article-preview-content" aria-live="polite"></div>';
  const bar = panel.querySelector('header'), content = panel.querySelector('.article-preview-content');
  const title = bar.querySelector('.article-preview-title');
  title.textContent = link.textContent.trim();
  const drag = bar.querySelector('[data-drag]');
  drag.innerHTML = icon('<path d="M12 3v18M3 12h18M9 6l3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3"/>');
  const pin = bar.querySelector('[data-pin]');
  pin.innerHTML = icon('<path d="M8 3h8l-1 7 3 3v2H6v-2l3-3-1-7ZM12 15v6"/>');
  const dismiss = bar.querySelector('[data-close]');
  dismiss.innerHTML = icon('<path d="m6 6 12 12M18 6 6 18"/>');
  for (const [button, label] of [[drag, labels.move], [pin, labels.pin], [dismiss, labels.close]]) {
    button.setAttribute('aria-label', label);
    button.title = label;
  }
  content.textContent = labels.loading;
  panel.controller = new AbortController();
  transient = panel;
  document.body.append(panel);
  position(panel, link);
  panel.style.zIndex = ++layer;
  panel.addEventListener('pointerenter', () => clearTimeout(closeTimer));
  panel.addEventListener('pointerleave', () => { if (transient === panel) scheduleClose(); });
  panel.addEventListener('focusin', () => clearTimeout(closeTimer));
  pin.onclick = () => {
    clearTimeout(openTimer); clearTimeout(closeTimer);
    const pinned = pin.getAttribute('aria-pressed') !== 'true';
    if (pinned) {
      if (transient === panel) transient = null;
    } else {
      if (transient !== panel) close(transient);
      transient = panel;
    }
    pin.setAttribute('aria-pressed', String(pinned));
    pin.setAttribute('aria-label', pinned ? labels.unpin : labels.pin);
    pin.title = pinned ? labels.unpin : labels.pin;
  };
  dismiss.onclick = () => close(panel);
  const beginInteraction = () => {
    clearTimeout(openTimer); clearTimeout(closeTimer);
    panel.interacting = true;
    panel.manuallyPositioned = true;
    panel.style.zIndex = ++layer;
  };
  const endInteraction = () => {
    panel.interacting = false;
    if (transient === panel && !panel.matches(':hover') && !panel.contains(document.activeElement)) scheduleClose();
  };
  addPreviewResizeHandles(panel, () => {
    panel.manuallySized = true;
    panel.classList.add('article-preview-sized');
    beginInteraction();
  }, endInteraction);
  bar.addEventListener('pointerdown', event => {
    if (event.button !== 0 || event.target.closest('button:not([data-drag])')) return;
    event.preventDefault();
    beginInteraction();
    const bounds = panel.getBoundingClientRect(), x = event.clientX, y = event.clientY;
    bar.setPointerCapture(event.pointerId);
    panel.style.zIndex = ++layer;
    bar.onpointermove = move => {
      if (move.pointerId !== event.pointerId) return;
      panel.style.left = Math.max(8, Math.min(innerWidth - panel.offsetWidth - 8, bounds.left + move.clientX - x)) + 'px';
      panel.style.top = Math.max(8, Math.min(innerHeight - panel.offsetHeight - 8, bounds.top + move.clientY - y)) + 'px';
    };
    const finish = end => {
      if (end.pointerId !== event.pointerId) return;
      bar.onpointermove = bar.onpointerup = bar.onpointercancel = bar.onlostpointercapture = null;
      if (bar.hasPointerCapture(event.pointerId)) bar.releasePointerCapture(event.pointerId);
      endInteraction();
    };
    bar.onpointerup = bar.onpointercancel = bar.onlostpointercapture = finish;
  });
  try {
    const response = await fetch(url, {signal: panel.controller.signal, headers: {'Accept':'text/html'}});
    if (!response.ok || response.redirected) throw new Error('Unavailable');
    content.innerHTML = await response.text(); // Server renders sanitized rich content and escaped metadata.
    const heading = content.firstElementChild;
    if (heading?.tagName === 'H2') {
      title.textContent = heading.textContent;
      heading.remove();
    }
    if (content.querySelector('.article-preview-map') && panel.isConnected) {
      panel.classList.add('article-preview-with-map');
      const canvas = content.querySelector('.article-preview-map-canvas');
      panel.resizeObserver = new ResizeObserver(() => {
        clearTimeout(panel.fitTimer);
        panel.fitTimer = setTimeout(() => {
          canvas.contentWindow?.postMessage({channel:'kw-map', type:'fit'}, location.origin);
        }, 120);
      });
      panel.resizeObserver.observe(canvas);
    }
    if (panel.isConnected) {
      const fit = () => {
        fitContent(panel, content, bar);
        if (!panel.manuallyPositioned) position(panel, link);
      };
      fit();
      panel.contentObserver = new MutationObserver(fit);
      panel.contentObserver.observe(content, {subtree: true, childList: true, attributes: true, attributeFilter: ['style', 'hidden']});
      // Images may acquire their natural dimensions after the HTML arrives.
      for (const img of content.querySelectorAll('img')) img.addEventListener('load', fit, {once: true});
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

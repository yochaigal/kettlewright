import {previewPosition} from './preview-position.js';

export function initMonsterPreviews({triggers, panel, closeButton, render}) {
  // The panel must escape the scrollable catalog's clipping boundary.
  document.body.append(panel);
  let active, openTimer, closeTimer, returningFocus = false;
  function hide(returnFocus = false) {
    clearTimeout(openTimer);
    clearTimeout(closeTimer);
    const trigger = active;
    active?.setAttribute('aria-expanded', 'false');
    active = null;
    panel.hidden = true;
    if (returnFocus && trigger) {
      returningFocus = true;
      trigger.focus({preventScroll: true});
      returningFocus = false;
    }
  }
  function show(trigger) {
    clearTimeout(openTimer);
    clearTimeout(closeTimer);
    if (active !== trigger) {
      active?.setAttribute('aria-expanded', 'false');
      render(trigger.dataset.preview);
      panel.scrollTop = 0;
      active = trigger;
    }
    active.setAttribute('aria-expanded', 'true');
    panel.hidden = false;
    panel.style.maxHeight = '';
    const width = document.documentElement?.clientWidth || innerWidth;
    const height = document.documentElement?.clientHeight || innerHeight;
    panel.style.maxWidth = Math.max(0, width - 16) + 'px';
    const position = previewPosition(trigger.getBoundingClientRect(), panel.offsetWidth, panel.offsetHeight, width, height);
    panel.style.left = position.left + 'px';
    panel.style.top = position.top + 'px';
    panel.style.maxHeight = Math.max(0, position.maxHeight) + 'px';
  }
  function scheduleClose() {
    clearTimeout(openTimer);
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {
      if (!panel.matches(':hover') && !panel.contains(document.activeElement) && document.activeElement !== active) hide();
    }, 200);
  }
  for (const trigger of triggers) {
    trigger.addEventListener('pointerenter', event => {
      if (event.pointerType === 'touch') return;
      clearTimeout(closeTimer);
      clearTimeout(openTimer);
      openTimer = setTimeout(() => show(trigger), 180);
    });
    trigger.addEventListener('pointerleave', scheduleClose);
    trigger.addEventListener('focus', () => { if (!returningFocus) show(trigger); });
    trigger.addEventListener('blur', scheduleClose);
    trigger.addEventListener('click', () => {
      show(trigger);
      closeButton.focus({preventScroll: true});
    });
  }
  panel.addEventListener('pointerenter', () => { clearTimeout(openTimer); clearTimeout(closeTimer); });
  panel.addEventListener('pointerleave', scheduleClose);
  panel.addEventListener('focusin', () => clearTimeout(closeTimer));
  panel.addEventListener('focusout', scheduleClose);
  closeButton.addEventListener('click', () => hide(true));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && active) hide(panel.contains(document.activeElement) || document.activeElement === active);
  });
  document.addEventListener('click', event => {
    if (active && !panel.contains(event.target) && !active.contains(event.target)) hide();
  });
  document.addEventListener('input', event => { if (event.target.id === 'monster-search') hide(); });
  document.getElementById('monster-selected-only').addEventListener('change', () => hide());
  window.addEventListener('resize', () => hide());
  window.addEventListener('scroll', event => {
    if (event.target === window || !panel.contains(event.target)) hide();
  }, true);
}

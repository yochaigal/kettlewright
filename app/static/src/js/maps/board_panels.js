// The whiteboard's two floating panels, the Warden's Dungeon and Fog tools and the dice roller, can be hidden
// (Discord feedback): × on the panel hides it, its button in the top bar shows it again (pressed while shown).
// Remembered in this browser. `legacy` reads the old "minimized" setting once, as hidden.
export function hideablePanel({panel, hide, toggle, key, legacy = null, onHide, storage = () => globalThis.localStorage}) {
  if (!panel) return null;
  const read = name => {try {return storage()?.getItem(name) ?? null;} catch (_) {return null;}};
  const write = value => {try {storage()?.setItem(key, value);} catch (_) { /* Optional preference. */ }};
  const isHidden = () => Boolean(panel.classList?.contains('is-user-hidden'));
  function set(hidden, {save = true, focus = false} = {}) {
    panel.classList?.toggle('is-user-hidden', hidden);
    toggle?.setAttribute('aria-pressed', String(!hidden));
    if (save) write(hidden ? 'hidden' : 'shown');
    if (!hidden) return;
    onHide?.();
    // Hidden from its own ×: focus goes to the button that brings it back.
    if (focus) toggle?.focus?.();
  }
  const saved = read(key);
  set(saved ? saved === 'hidden' : legacy !== null && read(legacy) === 'on', {save: false});
  const onHideClick = () => set(true, {focus: true}), onToggle = () => set(!isHidden());
  hide?.addEventListener('click', onHideClick);
  toggle?.addEventListener('click', onToggle);
  return {set, isHidden, destroy() {
    hide?.removeEventListener?.('click', onHideClick); toggle?.removeEventListener?.('click', onToggle);
  }};
}

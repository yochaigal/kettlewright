import diceModal from '../dice_modal.js';
import dice3d from '../dice3d.js';
import {actorKey} from './token_stats.js';

const MINIMIZED = 'board-rolls-minimized';
function stored(key) {try {return localStorage.getItem(key);} catch (_) {return null;}}
function store(key, value) {try {localStorage.setItem(key, value);} catch (_) { /* Optional preference. */ }}

export function createBoardRolls({config, getApi, updates, canRoll, isPlayerPreview, osd = null}) {
  const panel = document.getElementById('board-rolls');
  const name = document.getElementById('board-roll-name'), choices = document.getElementById('board-roll-actor');
  const actions = document.getElementById('board-roll-actions'), result = document.getElementById('board-roll-result');
  const publicToggle = document.getElementById('board-roll-public');
  const minimize = document.getElementById('board-roll-minimize'), toggle3d = document.getElementById('board-roll-3d');
  const modalPublic = document.getElementById('warden-public-roll');
  const modalTitle = document.querySelector('#dice-modal .modal-card-title');
  let actors = new Map(), active = null, preferred = '', modalActor = null;
  let stopped = false, rolling = false, frame = null, rendered = '', lastSelection = '';
  if (publicToggle) publicToggle.checked = false;
  if (modalPublic) modalPublic.checked = false;

  // Minimize (#385): only the heading stays, so the roller is out of the way when zoomed in. Remembered.
  function setMinimized(minimized) {
    panel.classList?.toggle('is-minimized', minimized);
    if (!minimize) return;
    minimize.setAttribute('aria-expanded', String(!minimized));
    const label = minimized ? minimize.dataset.expand : minimize.dataset.minimize;
    minimize.title = label; minimize.setAttribute('aria-label', label);
    const icon = minimize.querySelector?.('i');
    if (icon) icon.className = `fa-solid fa-chevron-${minimized ? 'up' : 'down'}`;
  }
  const onMinimize = () => {
    const minimized = !panel.classList?.contains('is-minimized');
    setMinimized(minimized); store(MINIMIZED, minimized ? 'on' : 'off');
  };
  setMinimized(stored(MINIMIZED) === 'on');
  minimize?.addEventListener('click', onMinimize);

  // 3D dice on the whiteboard only (#436): dice3d keeps this page's choice apart from the site-wide one.
  const show3d = () => {if (toggle3d) toggle3d.setAttribute('aria-pressed', String(dice3d.isEnabled()));};
  const on3d = () => dice3d.setEnabled(!dice3d.isEnabled());
  if (toggle3d) {
    toggle3d.hidden = !dice3d.isAvailable?.();
    toggle3d.addEventListener('click', on3d);
    show3d();
  }
  globalThis.addEventListener?.('dice3d-preference', show3d);

  function redraw() {if (!stopped && frame === null) frame = requestAnimationFrame(draw);}
  function draw() {
    frame = null;
    if (stopped) return;
    panel.hidden = isPlayerPreview();
    const ids = Object.keys(getApi()?.getAppState().selectedElementIds || {}).filter(id =>
      getApi()?.getSceneElements().some(element => element.id === id && !element.isDeleted));
    const selected = ids.length === 1 ? actors.get(actorKey(ids[0])) : null;
    if (config.warden) active = selected || null;
    else {
      const signature = ids.join();
      if (signature !== lastSelection && selected) preferred = selected.id;
      lastSelection = signature;
      active = actors.get(preferred) || actors.values().next().value || null;
      preferred = active?.id || '';
    }
    const signature = JSON.stringify([active, config.warden ? [] : Array.from(actors.values(), actor => [actor.id, actor.name])]);
    if (signature !== rendered) {
      const changed = (active?.id || '') !== panel.dataset.actor;
      rendered = signature; panel.dataset.actor = active?.id || '';
      if (changed) {
        result.textContent = '';
        if (publicToggle) publicToggle.checked = false;
      }
      name.textContent = active?.name || (config.warden ? config.messages.warden : config.messages.tokensEmpty);
      choices.hidden = config.warden || actors.size < 2;
      name.hidden = !choices.hidden;
      choices.replaceChildren();
      if (!choices.hidden) for (const actor of actors.values()) {
        const option = document.createElement('option'); option.value = actor.id; option.textContent = actor.name;
        choices.append(option);
      }
      choices.value = preferred;
      actions.replaceChildren();
      actions.dataset.mode = active?.kind === 'monster' ? 'monster' : config.warden ? 'warden' : 'player';
      if (active?.kind === 'monster') {
        const damage = active.damage || [];
        if (!damage.length) button(config.messages.damage, {dice: 'd4'}, true);
        for (const dice of damage) button(`${config.messages.damage} ${dice}`, {dice});
        for (const [stat, label] of [['strength', 'STR'], ['dexterity', 'DEX'], ['willpower', 'WIL']]) {
          button(label, {dice: 'd20', save: stat}, active.stats[stat] == null);
        }
        const more = button(config.messages.rollDice, {modal: true});
        more.textContent = '';
        const icon = document.createElement('i'); icon.className = 'fa-solid fa-dice'; icon.setAttribute('aria-hidden', 'true');
        more.append(icon);
      } else {
        for (const sides of [4, 6, 8, 10, 12, 20, ...(config.warden ? [100] : [])]) button(`d${sides}`, {dice: `d${sides}`});
        for (const sides of [4, 6, 8, 10, 12]) button(`d${sides}+d${sides}`, {dice: `d${sides}+d${sides}`});
        if (config.warden) {
          button(config.messages.reaction, {kind: 'reaction'});
          button(config.messages.fate, {kind: 'fate'});
        }
      }
    }
    for (const button of actions.querySelectorAll('button')) button.disabled = rolling || !canRoll()
      || (!config.warden && !active) || button.dataset.unavailable === 'true';
    choices.disabled = rolling || !canRoll();
    if (publicToggle) publicToggle.disabled = rolling || !canRoll();
  }
  function button(label, action, unavailable = false) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = label;
    button.title = button.ariaLabel = label; button.dataset.unavailable = String(unavailable);
    button.addEventListener('click', () => {
      if (action.modal) openModal(active);
      else request(active, action).catch(() => {});
    });
    actions.append(button); return button;
  }
  // The quick-roll panel animates its own rolls; the modal's rolls are animated by diceModal.showResult.
  async function request(actor, {dice = '', kind = 'dice', save = ''}, publicRoll = publicToggle?.checked, animate = true) {
    if (rolling || !canRoll() || (!config.warden && !actor)) throw new Error(config.messages.rollFailed);
    const body = new FormData();
    body.set('csrf_token', config.csrfToken); body.set('party_id', config.partyId);
    body.set('dice', dice); body.set('kind', kind);
    if (!config.warden || publicRoll) body.set('public_roll', 'on');
    if (actor) body.set(actor.kind === 'monster' ? 'companion_id' : 'character_id', actor.id.split(':').at(-1));
    if (save) body.set('save', save);
    rolling = true; draw();
    const actorId = actor?.id;
    // The name the server gives this roll, so its echo over the socket is recognised (board_roll_osd.js).
    const rollName = actor?.name || config.messages.warden;
    let released = false;
    const release = (roll = null) => {if (!released) {released = true; osd?.release(roll && rollName, roll?.result);}};
    osd?.hold();
    try {
      const response = await fetch(config.warden && !actor ? config.wardenRollUrl : config.rollUrl,
        {method: 'POST', body, cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error(config.messages.rollFailed);
      const roll = await response.json();
      release(roll);
      if (animate && !stopped) await dice3d.show(roll);
      if (!stopped && actorId === active?.id) result.textContent = roll.result;
      // Rolls from the dice modal already show their result there.
      if (animate && !stopped) osd?.own(rollName, roll.result);
      return roll;
    } catch (error) {
      if (!stopped && actorId === active?.id) result.textContent = config.messages.rollFailed;
      throw error;
    } finally {release(); rolling = false; if (!stopped) draw();}
  }
  function openModal(actor) {
    if (!canRoll() || rolling) return;
    modalActor = actor;
    if (modalTitle) modalTitle.textContent = actor?.name || config.messages.warden || config.messages.rollDice;
    if (modalPublic) modalPublic.checked = publicToggle.checked;
    document.querySelectorAll('#warden-dice [data-warden-roll]').forEach(button => {button.hidden = Boolean(actor);});
    diceModal.setMode(config.warden ? 'party' : 'character');
    diceModal.showDiceModal();
  }
  diceModal.initialize(dice => request(modalActor, {dice}, modalPublic?.checked, false));
  const special = [];
  document.querySelectorAll('#warden-dice [data-warden-roll]').forEach(button => {
    const listener = async () => {
      const label = (button.querySelector?.('span') || button).textContent?.trim() || '';
      diceModal.hold();
      diceModal.showRolling(label, button.dataset.wardenRoll === 'reaction' ? 'd6+d6' : 'd6');
      try {await diceModal.showResult(await request(null, {kind: button.dataset.wardenRoll}, modalPublic.checked, false), {label});
      } catch (_) {diceModal.showError(config.messages.rollFailed);
      } finally {diceModal.release();}
    };
    button.addEventListener('click', listener); special.push([button, listener]);
  });
  choices.addEventListener('change', () => {preferred = choices.value; redraw();});
  const unsubscribe = updates.subscribe('rollActors', data => {
    if (stopped) return;
    actors = new Map((data || []).map(actor => [actor.id, actor]));
    redraw();
  });
  redraw();
  return {redraw, destroy() {
    stopped = true; unsubscribe(); panel.hidden = true;
    minimize?.removeEventListener('click', onMinimize); toggle3d?.removeEventListener('click', on3d);
    globalThis.removeEventListener?.('dice3d-preference', show3d);
    if (frame !== null) cancelAnimationFrame(frame);
    for (const [button, listener] of special) button.removeEventListener('click', listener);
  }};
}

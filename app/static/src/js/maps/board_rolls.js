import diceModal from '../dice_modal.js';
import dice3d from '../dice3d.js';
import {actorKey} from './token_stats.js';
import {hideablePanel} from './board_panels.js';

export function createBoardRolls({config, getApi, updates, canRoll, isPlayerPreview, osd = null}) {
  const panel = document.getElementById('board-rolls');
  const name = document.getElementById('board-roll-name'), choices = document.getElementById('board-roll-actor');
  const actions = document.getElementById('board-roll-actions'), result = document.getElementById('board-roll-result');
  const publicToggle = document.getElementById('board-roll-public');
  const toggle3d = document.getElementById('board-roll-3d');
  const modalPublic = document.getElementById('warden-public-roll');
  const modalTitle = document.querySelector('#dice-modal .modal-card-title');
  let actors = new Map(), active = null, preferred = '', modalActor = null;
  let stopped = false, rolling = false, frame = null, rendered = '', lastSelection = '';
  // Rolls start private. Once the Warden makes them public they stay public, whichever token is
  // selected, until switched off again; the panel and dice-modal switches are one choice (#399).
  if (publicToggle) publicToggle.checked = false;
  if (modalPublic) modalPublic.checked = false;
  const fromPanel = () => {if (modalPublic) modalPublic.checked = publicToggle.checked;};
  const fromModal = () => {if (publicToggle) publicToggle.checked = modalPublic.checked;};
  publicToggle?.addEventListener('change', fromPanel);
  modalPublic?.addEventListener('change', fromModal);

  // Hide (Discord feedback; it was Minimize, #385): × hides the roller, Dice in the top bar shows it again.
  // Rolls still show on the board while it is hidden (board-roll-osd).
  const hiding = hideablePanel({panel, hide: document.getElementById('board-roll-hide'), toggle: document.getElementById('board-dice-toggle'),
    key: 'board-rolls-hidden', legacy: 'board-rolls-minimized', storage: () => localStorage});

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
      if (changed) result.textContent = '';
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
        for (const sides of [4, 6, 8, 10, 12, 20, ...(config.warden ? [100] : [])]) diceButton(sides, 1);
        for (const sides of [4, 6, 8, 10, 12]) diceButton(sides, 2);
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
  // Dice buttons show the die shapes of the dice modal; the label stays as their name and tooltip.
  const dieIcons = document.getElementById('board-die-icons');
  function diceButton(sides, count) {
    const label = count === 2 ? `d${sides}+d${sides}` : `d${sides}`;
    const control = button(label, {dice: label});
    const icon = dieIcons?.content?.querySelector?.(`[data-sides="${sides}"]`);
    if (!icon) return control;
    control.textContent = '';
    control.classList?.toggle('board-roll-die', true);
    control.append(...Array.from({length: count}, () => icon.cloneNode(true)));
    return control;
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
    hiding?.destroy(); toggle3d?.removeEventListener('click', on3d);
    publicToggle?.removeEventListener('change', fromPanel); modalPublic?.removeEventListener('change', fromModal);
    globalThis.removeEventListener?.('dice3d-preference', show3d);
    if (frame !== null) cancelAnimationFrame(frame);
    for (const [button, listener] of special) button.removeEventListener('click', listener);
  }};
}

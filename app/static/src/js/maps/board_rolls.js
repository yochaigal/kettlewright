import diceModal from '../dice_modal.js';
import {actorKey} from './token_stats.js';

export function createBoardRolls({config, getApi, socket, canRoll, isPlayerPreview}) {
  const panel = document.getElementById('board-rolls');
  const name = document.getElementById('board-roll-name'), choices = document.getElementById('board-roll-actor');
  const actions = document.getElementById('board-roll-actions'), result = document.getElementById('board-roll-result');
  const publicToggle = document.getElementById('board-roll-public');
  const modalPublic = document.getElementById('warden-public-roll');
  const modalTitle = document.querySelector('#dice-modal .modal-card-title');
  let actors = new Map(), active = null, preferred = '', modalActor = null;
  let stopped = false, rolling = false, epoch = 0, frame = null, rendered = '', lastSelection = '';
  if (publicToggle) publicToggle.checked = false;
  if (modalPublic) modalPublic.checked = false;

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
  async function request(actor, {dice = '', kind = 'dice', save = ''}, publicRoll = publicToggle?.checked) {
    if (rolling || !canRoll() || (!config.warden && !actor)) throw new Error(config.messages.rollFailed);
    const body = new FormData();
    body.set('csrf_token', config.csrfToken); body.set('party_id', config.partyId);
    body.set('dice', dice); body.set('kind', kind);
    if (!config.warden || publicRoll) body.set('public_roll', 'on');
    if (actor) body.set(actor.kind === 'monster' ? 'companion_id' : 'character_id', actor.id.split(':').at(-1));
    if (save) body.set('save', save);
    rolling = true; draw();
    const actorId = actor?.id;
    try {
      const response = await fetch(config.warden && !actor ? config.wardenRollUrl : config.rollUrl,
        {method: 'POST', body, cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error(config.messages.rollFailed);
      const roll = await response.json();
      if (!stopped && actorId === active?.id) result.textContent = roll.result;
      return roll;
    } catch (error) {
      if (!stopped && actorId === active?.id) result.textContent = config.messages.rollFailed;
      throw error;
    } finally {rolling = false; if (!stopped) draw();}
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
  diceModal.initialize(dice => request(modalActor, {dice}, modalPublic?.checked));
  const special = [];
  document.querySelectorAll('#warden-dice [data-warden-roll]').forEach(button => {
    const listener = async () => {
      try {const roll = await request(null, {kind: button.dataset.wardenRoll}, modalPublic.checked);
        diceModal.resultText.textContent = roll.result;
      } catch (_) {diceModal.resultText.textContent = config.messages.rollFailed;}
    };
    button.addEventListener('click', listener); special.push([button, listener]);
  });
  choices.addEventListener('change', () => {preferred = choices.value; redraw();});
  async function refresh() {
    if (stopped) return;
    const run = ++epoch;
    try {
      const response = await fetch(config.rollActorsUrl, {cache: 'no-store', signal: AbortSignal.timeout(10000)});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      if (stopped || run !== epoch) return;
      actors = new Map(data.actors.map(actor => [actor.id, actor]));
    } catch (_) {if (stopped || run !== epoch) return; actors.clear();}
    redraw();
  }
  const changed = data => {if (data.party_id === config.partyId) refresh();};
  const visible = () => {if (!document.hidden) refresh();};
  socket.on('party_actors_changed', changed); socket.on('party_members_changed', changed); socket.on('connect', refresh);
  document.addEventListener('visibilitychange', visible);
  const timer = setInterval(refresh, 5000);
  refresh(); redraw();
  return {redraw, destroy() {
    stopped = true; ++epoch; panel.hidden = true; clearInterval(timer);
    if (frame !== null) cancelAnimationFrame(frame);
    for (const [button, listener] of special) button.removeEventListener('click', listener);
    socket.off('party_actors_changed', changed); socket.off('party_members_changed', changed); socket.off('connect', refresh);
    document.removeEventListener('visibilitychange', visible);
  }};
}

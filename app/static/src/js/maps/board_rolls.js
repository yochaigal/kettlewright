import diceModal from '../dice_modal.js';
import {gameSystem} from '#kettlewright';
import dice3d from '../dice3d.js';
import {actorKey} from './token_stats.js';
import {hideablePanel} from './board_panels.js';

export function createBoardRolls({config, getApi, updates, canRoll, isPlayerPreview, osd = null, onActive = null}) {
  const panel = document.getElementById('board-rolls');
  const name = document.getElementById('board-roll-name'), choices = document.getElementById('board-roll-actor');
  const actions = document.getElementById('board-roll-actions'), result = document.getElementById('board-roll-result');
  const publicToggle = document.getElementById('board-roll-public');
  const toggle3d = document.getElementById('board-roll-3d');
  const token = document.getElementById('board-roll-token');
  let savingStat = false;
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
    // Ring the tokens of the actor this roller is for (#375), which a player may have picked from the list.
    onActive?.(isPlayerPreview() ? null : active?.id || null);
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
      drawToken();
      actions.replaceChildren();
      // A monster or a character (#532, #543): quick rolls (its damage and saves), and the full dice in the dice
      // window. The Warden with nothing selected has the dice here.
      const quick = active?.kind === 'monster' || active?.kind === 'character';
      actions.dataset.mode = quick ? 'quick' : config.warden ? 'warden' : 'player';
      if (quick) {
        const saveDice = `d${gameSystem().save?.die ?? 20}`;
        if (active.kind === 'monster') {
          const damage = active.damage || [];
          if (!damage.length) button(config.messages.damage, {dice: 'd4'}, true);
          for (const dice of damage) button(`${config.messages.damage} ${dice}`, {dice});
        } else {
          // The Warden rolls these for the selected character, as it (#543).
          for (const weapon of active.weapons || []) button(`${weapon.name} ${weapon.dice}`, {dice: weapon.dice, asActive: true});
        }
        const scores = active.kind === 'monster' ? active.stats : Object.fromEntries(
          Object.entries(active.attributes || {}).map(([stat, [current]]) => [stat, current]));
        for (const {key: stat, abbr: label} of gameSystem().attributes.filter(attribute => attribute.save)) {
          button(label, {dice: saveDice, save: stat, asActive: true}, scores[stat] == null);
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
    if (token) for (const control of token.querySelectorAll('button')) {
      const [current, maximum] = statValue(active, control.dataset.field) || [];
      control.disabled = savingStat || !canRoll() || (control.dataset.step === '-1' && current <= 0)
        || (control.dataset.step === '1' && current >= maximum);
    }
    if (publicToggle) publicToggle.disabled = rolling || !canRoll();
  }
  // The selected token's panel (#375): HP −/+, a monster at 0 HP is Down, a character's STR, DEX and WIL,
  // Deprived and Panicked, and its full sheet. Rebuilt only for another actor, so a pressed button keeps its focus.
  const statLabels = Object.fromEntries(gameSystem().attributes.map(attribute => [attribute.key, attribute.abbr]));
  const statValue = (actor, field) => field === 'hp' ? actor?.hp : actor?.attributes?.[field];
  function drawToken() {
    if (!token) return;
    token.hidden = !active?.hp;
    if (token.hidden) {token.replaceChildren(); delete token.dataset.actor; return;}
    if (token.dataset.actor !== active.id) {
      token.dataset.actor = active.id; token.replaceChildren();
      const stepper = field => {
        const box = document.createElement('span'); box.className = 'board-roll-hp';
        const name = field === 'hp' ? config.messages.hp : statLabels[field];
        const step = (delta, label, text) => {
          const control = document.createElement('button'); control.type = 'button';
          control.dataset.step = String(delta); control.dataset.field = field;
          control.textContent = text; control.title = control.ariaLabel = label.replace('{stat}', name);
          control.addEventListener('click', () => {
            const [current, maximum] = statValue(active, field);
            saveStat(field, Math.max(0, Math.min(maximum, current + delta)));
          });
          return control;
        };
        const value = document.createElement('output'); value.dataset.value = field;
        box.append(step(-1, config.messages.lowerStat, '−'), value, step(1, config.messages.raiseStat, '+'));
        token.append(box);
      };
      stepper('hp');
      for (const field of Object.keys(statLabels)) if (active.attributes?.[field]) stepper(field);
      if (active.kind === 'monster') {
        const down = document.createElement('span'); down.className = 'board-roll-down'; down.textContent = config.messages.down;
        token.append(down);
      }
      for (const condition of Object.keys(active.conditions || {})) {
        const chip = document.createElement('button'); chip.type = 'button'; chip.className = 'board-roll-condition';
        chip.dataset.condition = condition;
        chip.textContent = config.messages[condition] ?? gameSystem().conditions.find(({key}) => key === condition)?.label ?? condition;
        chip.addEventListener('click', () => saveStat(condition, active.conditions[condition] ? 0 : 1));
        token.append(chip);
      }
      if (active.sheetUrl) {
        const link = document.createElement('a'); link.className = 'board-roll-sheet'; link.href = active.sheetUrl;
        link.target = '_blank'; link.rel = 'noopener'; link.title = link.ariaLabel = config.messages.openSheet;
        const icon = document.createElement('i'); icon.className = 'fa-solid fa-arrow-up-right-from-square'; icon.setAttribute('aria-hidden', 'true');
        link.append(icon); token.append(link);
      }
    }
    for (const value of token.querySelectorAll('[data-value]')) {
      const field = value.dataset.value, [current, maximum] = statValue(active, field);
      value.textContent = `${field === 'hp' ? config.messages.hp : statLabels[field]} ${current}/${maximum}`;
    }
    const down = token.querySelector('.board-roll-down');
    if (down) down.hidden = active.hp[0] > 0;
    for (const chip of token.querySelectorAll('[data-condition]')) chip.setAttribute('aria-pressed', String(Boolean(active.conditions[chip.dataset.condition])));
  }
  async function saveStat(stat, value) {
    const actor = active;
    if (!actor?.statUrl || savingStat || !canRoll()) return;
    const body = new FormData();
    body.set('csrf_token', config.csrfToken); body.set('stat', stat); body.set('value', String(value));
    savingStat = true; redraw();
    try {
      const response = await fetch(actor.statUrl, {method: 'POST', body, cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error(config.messages.statFailed);
      // Shown at once; the party's live update brings everyone (and the token's label) the same value.
      const saved = stat === 'hp' ? {hp: [value, actor.hp[1]]}
        : stat in statLabels ? {attributes: {...actor.attributes, [stat]: [value, actor.attributes[stat][1]]}}
          : {conditions: {...actor.conditions, [stat]: Boolean(value)}};
      const next = {...actor, ...saved};
      actors.set(actor.id, next);
      if (active?.id === actor.id) active = next;
      updates.refresh?.();
    } catch (_) {
      if (!stopped && active?.id === actor.id) result.textContent = config.messages.statFailed;
    } finally {savingStat = false; if (!stopped) redraw();}
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
  // The Warden edits a selected player's character (#375) and rolls its quick rolls as it (#543); the Warden's own
  // dice (the dice window) stay the Warden's.
  const roller = () => config.warden && active?.kind === 'character' ? null : active;
  function button(label, action, unavailable = false) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = label;
    button.title = button.ariaLabel = label; button.dataset.unavailable = String(unavailable);
    button.addEventListener('click', () => {
      if (action.modal) openModal(roller());
      else request(action.asActive ? active : roller(), action).catch(() => {});
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
      if (!stopped && (actorId === roller()?.id || actorId === active?.id)) result.textContent = roll.result;
      // Rolls from the dice modal already show their result there.
      if (animate && !stopped) osd?.own(rollName, roll.result);
      return roll;
    } catch (error) {
      if (!stopped && (actorId === roller()?.id || actorId === active?.id)) result.textContent = config.messages.rollFailed;
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

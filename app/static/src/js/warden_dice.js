import diceModal from './dice_modal.js';
import notification from './notification.js';
import { refreshRollHistory } from './party_roll_history.js';

const panel = document.getElementById('warden-dice');
const form = document.getElementById('warden-dice-form');
const publicToggle = document.getElementById('warden-public-roll');
// Do not restore a public mode from browser form-state or a previous visit.
publicToggle.checked = false;
function updatePublicToggle() {
  publicToggle.disabled = !form.elements.party_id.value;
  if (publicToggle.disabled) publicToggle.checked = false;
}
let rolling = false;
let monster = null, save = null;

// Callers show the result (diceModal.showResult animates it), so this only rolls and records.
export async function requestWardenRoll(kind, dice = '') {
  if (rolling) throw new Error(panel.dataset.error);
  rolling = true;
  const buttons = panel.querySelectorAll('button');
  buttons.forEach(button => { button.disabled = true; });
  const body = new FormData(form);
  body.set('kind', kind);
  body.set('dice', dice);
  if (monster) body.set('companion_id', monster.dataset.monsterRoll);
  if (save) body.set('save', save);
  try {
    const response = await fetch(monster ? monster.dataset.rollUrl : panel.dataset.rollUrl, { method: 'POST', body, cache: 'no-store' });
    if (response.redirected) throw new Error(panel.dataset.error);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || panel.dataset.error);
    if (body.get('party_id')) refreshRollHistory(body.get('party_id'));
    return result;
  } finally {
    rolling = false; save = null;
    buttons.forEach(button => { button.disabled = false; });
  }
}

diceModal.initialize(dice => requestWardenRoll('dice', dice));
diceModal.setMode('party');
document.getElementById('warden-dice-button')?.addEventListener('click', () => {
  monster = null; save = null; publicToggle.checked = false; diceModal.showDiceModal();
});
document.addEventListener('click', async event => {
  const button = event.target.closest('[data-monster-roll]');
  if (!button || rolling) return;
  monster = button; save = button.dataset.save || null; publicToggle.checked = false;
  diceModal.showDiceModal();
  if (button.dataset.dice || save) {
    const dice = save ? 'd20' : button.dataset.dice;
    const label = button.textContent?.trim() || dice;
    diceModal.showRolling(label, dice);
    try {await diceModal.showResult(await requestWardenRoll('dice', dice), {label});}
    catch (error) {diceModal.showError(error.message); notification.showNotification(error.message);}
  }
});
panel.querySelectorAll('[data-warden-roll]').forEach(button => {
  button.addEventListener('click', async () => {
    const label = (button.querySelector?.('span') || button).textContent?.trim() || '';
    try {
      monster = null; save = null;
      diceModal.showRolling(label, button.dataset.wardenRoll === 'reaction' ? 'd6+d6' : 'd6');
      await diceModal.showResult(await requestWardenRoll(button.dataset.wardenRoll), {label});
    } catch (error) {
      diceModal.showError(error.message);
      notification.showNotification(error.message);
    }
  });
});
// Remember the selected active party for the next Tools visit.
const select = document.getElementById('warden-roll-party');
if (select) {
  try {
    const active = localStorage.getItem('warden-roll-party');
    if ([...select.options].some(option => option.value === active)) select.value = active;
  } catch (_) { /* Optional preference. */ }
  select.addEventListener('change', () => {
    try { localStorage.setItem('warden-roll-party', select.value); } catch (_) { /* Optional preference. */ }
    updatePublicToggle();
  });
} else {
  try { localStorage.setItem('warden-roll-party', form.elements.party_id.value); } catch (_) { /* Optional preference. */ }
}
updatePublicToggle();

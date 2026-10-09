import diceModal from './dice_modal.js';
import notification from './notification.js';
import { refreshRollHistory } from './party_roll_history.js';

const panel = document.getElementById('warden-dice');
const form = document.getElementById('warden-dice-form');
const publicToggle = document.getElementById('warden-public-roll');
const visibility = document.getElementById('warden-roll-visibility');
// Do not restore a public mode from browser form-state or a previous visit.
publicToggle.checked = false;
function updateVisibility() {
  publicToggle.disabled = !form.elements.party_id.value;
  if (publicToggle.disabled) publicToggle.checked = false;
  visibility.textContent = publicToggle.checked ? visibility.dataset.public : visibility.dataset.private;
}
publicToggle.addEventListener('change', updateVisibility);
let rolling = false;

export async function requestWardenRoll(kind, dice = '') {
  if (rolling) throw new Error(panel.dataset.error);
  rolling = true;
  const buttons = panel.querySelectorAll('button');
  buttons.forEach(button => { button.disabled = true; });
  const body = new FormData(form);
  body.set('kind', kind);
  body.set('dice', dice);
  try {
    const response = await fetch(panel.dataset.rollUrl, { method: 'POST', body, cache: 'no-store' });
    if (response.redirected) throw new Error(panel.dataset.error);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || panel.dataset.error);
    diceModal.resultText.textContent = result.result;
    if (body.get('party_id')) refreshRollHistory(body.get('party_id'));
    return result;
  } finally {
    rolling = false;
    buttons.forEach(button => { button.disabled = false; });
  }
}

diceModal.initialize(dice => requestWardenRoll('dice', dice));
diceModal.setMode('party');
document.getElementById('warden-dice-button').addEventListener('click', () => diceModal.showDiceModal());
panel.querySelectorAll('[data-warden-roll]').forEach(button => {
  button.addEventListener('click', async () => {
    try {
      await requestWardenRoll(button.dataset.wardenRoll);
    } catch (error) {
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
    updateVisibility();
  });
} else {
  try { localStorage.setItem('warden-roll-party', form.elements.party_id.value); } catch (_) { /* Optional preference. */ }
}
updateVisibility();

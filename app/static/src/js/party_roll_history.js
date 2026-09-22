import { styledConfirm } from './utils.js';

// Fetch authoritative snapshots so reconnects and repeated events cannot duplicate rows.
const states = new WeakMap();

function localizeTimes(panel) {
  panel.querySelectorAll('time[datetime]').forEach((time) => {
    time.textContent = new Date(time.dateTime).toLocaleString();
  });
}

export async function refreshRollHistory(partyId = null) {
  const panel = document.getElementById('party-roll-history');
  if (!panel || (partyId !== null && String(partyId) !== panel.dataset.partyId)) return;
  const state = states.get(panel) || { loading: false, dirty: false };
  states.set(panel, state);
  state.dirty = true;
  if (state.loading) return;
  state.loading = true;
  const error = panel.querySelector('.roll-history-error');
  try {
    while (state.dirty && panel.isConnected) {
      state.dirty = false;
      const response = await fetch(panel.dataset.historyUrl, { cache: 'no-store' });
      if (!response.ok || response.redirected) {
        // Do not leave private history visible after membership or login is lost.
        if (response.status === 403 || response.status === 404 || response.redirected) {
          panel.querySelector('.party-roll-entries').replaceChildren();
        }
        throw new Error('History request failed');
      }
      const html = await response.text();
      if (!panel.isConnected) return;
      panel.querySelector('.party-roll-entries').innerHTML = html;
      localizeTimes(panel);
      error.hidden = true;
    }
  } catch (_) {
    error.textContent = panel.dataset.loadError;
    error.hidden = false;
  } finally {
    state.loading = false;
  }
}

export function initializeRollHistory() {
  const panel = document.getElementById('party-roll-history');
  if (!panel || panel.dataset.initialized) return;
  panel.dataset.initialized = 'true';
  localizeTimes(panel);
  const toggle = panel.querySelector('.roll-history-toggle');
  const content = panel.querySelector('#party-roll-history-content');
  const storageKey = `party-roll-history-${panel.dataset.partyId}`;
  function setCollapsed(collapsed) {
    content.hidden = collapsed;
    toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.querySelector('i').className = `fa-solid fa-chevron-${collapsed ? 'right' : 'down'}`;
  }
  try { setCollapsed(localStorage.getItem(storageKey) === 'hidden'); } catch (_) { /* Storage may be disabled. */ }
  toggle.addEventListener('click', () => {
    setCollapsed(!content.hidden);
    try { localStorage.setItem(storageKey, content.hidden ? 'hidden' : 'visible'); } catch (_) { /* Optional preference. */ }
  });
  const form = panel.querySelector('#clear-roll-history');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const confirmed = await styledConfirm(form.dataset.confirmTitle, form.dataset.confirm,
                                          form.dataset.confirmTitle, form.dataset.cancel);
    if (!confirmed.isConfirmed) return;
    const button = form.querySelector('button');
    const error = panel.querySelector('.roll-history-error');
    button.disabled = true;
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form) });
      if (!response.ok || response.redirected) throw new Error('Clear request failed');
      await refreshRollHistory(panel.dataset.partyId);
    } catch (_) {
      error.textContent = panel.dataset.clearError;
      error.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
  refreshRollHistory();
}

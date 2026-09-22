import { initializeStatEditor, updateStatElement } from './quick_stats.js';

const states = new WeakMap();

export async function refreshCharacterStats(partyId = null) {
  const panel = document.getElementById('character-quick-stats');
  if (!panel || (partyId !== null && String(partyId) !== panel.dataset.partyId)) return;
  const state = states.get(panel) || { loading: false, dirty: false };
  states.set(panel, state);
  state.dirty = true;
  if (state.loading) return;
  state.loading = true;
  try {
    while (state.dirty && panel.isConnected) {
      state.dirty = false;
      const response = await fetch(panel.dataset.statsUrl, { cache: 'no-store' });
      if (!response.ok || response.redirected) throw new Error('Stats refresh failed');
      const template = document.createElement('template');
      template.innerHTML = await response.text();
      if (!panel.isConnected) return;
      const incoming = template.content.querySelector('#character-quick-stats');
      panel.dataset.partyId = incoming.dataset.partyId;
      const stats = panel.querySelector('.stats-stats-container');
      incoming.querySelectorAll('.stats-stats-container > [id]').forEach(stat => {
        const existing = stats.querySelector(`#${stat.id}`);
        if (!existing) return;
        if (stat.id === 'character-rest-container') {
          const button = existing.querySelector('button');
          const nextButton = stat.querySelector('button');
          if (button && nextButton) {
            // Keep the HTMX request source attached while its confirmation is open.
            button.disabled = nextButton.disabled;
            return;
          }
        }
        updateStatElement(existing, stat);
      });
      // Rest is an HTMX action and must be bound after replacing its button.
      window.htmx?.process(stats);
    }
  } catch (_) {
    panel.querySelector('.quick-stats-status').textContent = panel.dataset.loadError;
  } finally {
    state.loading = false;
  }
}

export function initializeCharacterStats() {
  const panel = document.getElementById('character-quick-stats');
  if (!panel || panel.dataset.initialized) return;
  panel.dataset.initialized = 'true';
  initializeStatEditor(panel, () => refreshCharacterStats());
  refreshCharacterStats();
}

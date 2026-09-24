const states = new WeakMap();
const valueOf = input => input.type === 'checkbox' ? String(Number(input.checked)) : input.value;
const savedValueOf = input => input.type === 'checkbox' ? String(Number(input.defaultChecked)) : input.defaultValue;
const stateFor = panel => {
  if (!states.has(panel)) states.set(panel, { loading: false, dirty: false, saving: false, revision: 0, queue: new Map() });
  return states.get(panel);
};

function updateButtons(panel) {
  panel.querySelectorAll('.stat-stepper').forEach(stepper => {
    const input = stepper.querySelector('input');
    stepper.querySelectorAll('[data-step]').forEach(button => {
      button.disabled = Number(button.dataset.step) < 0 ? Number(input.value) <= Number(input.min) : Number(input.value) >= Number(input.max);
    });
  });
}

export async function refreshCharacterStats(partyId = null) {
  const panel = document.getElementById('character-quick-stats');
  if (!panel || (partyId !== null && String(partyId) !== panel.dataset.partyId)) return;
  const state = stateFor(panel);
  state.dirty = true;
  if (state.loading || state.saving) return;
  state.loading = true;
  try {
    while (state.dirty && panel.isConnected && !state.saving) {
      state.dirty = false;
      const revision = state.revision;
      const response = await fetch(panel.dataset.statsUrl, { cache: 'no-store' });
      if (!response.ok || response.redirected) throw new Error('Stats refresh failed');
      const template = document.createElement('template');
      template.innerHTML = await response.text();
      if (!panel.isConnected) return;
      // A snapshot requested before a write must never overwrite its result.
      if (revision !== state.revision || state.saving) { state.dirty = true; continue; }
      const incoming = template.content.querySelector('#character-quick-stats');
      panel.dataset.partyId = incoming.dataset.partyId;
      incoming.querySelectorAll('.stats-stats-container > [id], .character-stat-toolbar > [id]').forEach(stat => {
        const existing = panel.querySelector(`#${stat.id}`);
        if (!existing) return;
        if (existing.querySelector('.sheet-stat-form')) {
          stat.querySelectorAll('.sheet-stat-form').forEach(nextForm => {
            const field = nextForm.elements.stat.value;
            const form = [...existing.querySelectorAll('.sheet-stat-form')].find(item => item.elements.stat.value === field);
            const input = form.elements.value;
            const next = nextForm.elements.value;
            if (!form.dataset.edited) {
              if (input.type === 'checkbox') input.checked = input.defaultChecked = next.checked;
              else input.value = input.defaultValue = next.value;
            }
            if (input.type !== 'checkbox') input.max = next.max;
          });
          const warning = existing.querySelector('.stat-warning');
          if (warning) warning.replaceChildren(...stat.querySelector('.stat-warning').childNodes);
        } else if (stat.id === 'character-rest-container') {
          // Preserve the request source while an HTMX confirmation is open.
          const button = existing.querySelector('button');
          if (button) button.disabled = stat.querySelector('button').disabled;
        } else existing.replaceWith(stat);
      });
      const badge = document.getElementById('character-dead-badge');
      if (badge) badge.replaceChildren(incoming.querySelector('[data-dead-badge]').content.cloneNode(true));
      updateButtons(panel);
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
  const state = stateFor(panel);
  const status = panel.querySelector('.quick-stats-status');
  function markEdited(form) {
    const input = form.elements.value;
    if (valueOf(input) === savedValueOf(input)) delete form.dataset.edited;
    else form.dataset.edited = 'true';
    updateButtons(panel);
  }
  async function save(form) {
    if (!form.reportValidity()) return;
    const field = form.elements.stat.value;
    const input = form.elements.value;
    // Queue even a return to the original value if an earlier write is pending.
    if (!form.dataset.edited && !state.saving) return;
    state.queue.set(field, { form, value: valueOf(input) });
    state.revision++;
    if (state.saving) return;
    state.saving = true;
    const rest = panel.querySelector('#character-rest-container button');
    if (rest) rest.disabled = true;
    let conditionsChanged = false;
    while (state.queue.size && panel.isConnected) {
      const [field, change] = state.queue.entries().next().value;
      state.queue.delete(field);
      const body = new FormData(change.form);
      body.set('value', change.value);
      try {
        const response = await fetch(change.form.action, { method: 'POST', body });
        if (!response.ok || response.redirected) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.error || panel.dataset.saveError);
        }
        const input = change.form.elements.value;
        if (input.type === 'checkbox') input.defaultChecked = change.value === '1';
        else input.defaultValue = change.value;
        // A maximum decrease also clamps current, atomically on the server.
        if (field.endsWith('_max')) {
          const current = panel.querySelector(`#character-quick-${field.slice(0, -4)}`);
          current.max = change.value;
          if (!current.form.dataset.edited && Number(current.value) > Number(change.value)) {
            current.value = current.defaultValue = change.value;
          }
        }
        markEdited(change.form);
        conditionsChanged ||= field === 'panicked';
        status.textContent = '';
      } catch (error) {
        status.textContent = error.message || panel.dataset.saveError;
        change.form.dataset.edited = 'true';
        // Keep drafts visible; a later change or Enter retries the field.
        state.queue.clear();
        break;
      }
    }
    state.saving = false;
    await refreshCharacterStats();
    if (conditionsChanged) document.dispatchEvent(new CustomEvent('character-section-saved', {
      detail: { section: 'stats', partyId: panel.dataset.partyId === 'None' ? null : panel.dataset.partyId },
    }));
  }
  panel.addEventListener('input', event => {
    const form = event.target.closest('.sheet-stat-form');
    if (form) markEdited(form);
  });
  panel.addEventListener('change', event => {
    const form = event.target.closest('.sheet-stat-form');
    if (form) { markEdited(form); save(form); }
  });
  panel.addEventListener('click', event => {
    const button = event.target.closest('[data-step]');
    if (!button) return;
    const form = button.closest('form');
    const input = form.elements.value;
    if (!input.validity.valid) { input.reportValidity(); return; }
    input.stepUp(Number(button.dataset.step));
    markEdited(form);
    save(form);
  });
  panel.addEventListener('submit', event => {
    if (!event.target.matches('.sheet-stat-form')) return;
    event.preventDefault();
    save(event.target);
  });
  panel.addEventListener('keydown', event => {
    const form = event.target.closest('.sheet-stat-form');
    if (event.key !== 'Escape' || !form || state.saving) return;
    const input = form.elements.value;
    if (input.type === 'checkbox') input.checked = input.defaultChecked;
    else input.value = input.defaultValue;
    markEdited(form);
    input.blur();
    refreshCharacterStats();
  });
  updateButtons(panel);
  refreshCharacterStats();
}

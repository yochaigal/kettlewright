export function initializeStatEditor(panel, refresh) {
  async function save(form) {
    if (form.dataset.saving || !form.reportValidity()) return;
    const input = form.querySelector('[name="value"]');
    if (input.value === input.defaultValue) {
      delete form.dataset.edited;
      return;
    }
    const body = new FormData(form);
    form.dataset.saving = 'true';
    input.readOnly = true;
    const status = panel.querySelector('.quick-stats-status');
    try {
      const response = await fetch(form.action, { method: 'POST', body });
      if (!response.ok || response.redirected) throw new Error('Stat save failed');
      input.defaultValue = input.value;
      delete form.dataset.edited;
      status.textContent = panel.dataset.saved;
    } catch (_) {
      status.textContent = panel.dataset.saveError;
    } finally {
      input.readOnly = false;
      delete form.dataset.saving;
      await refresh();
    }
  }
  panel.addEventListener('input', event => {
    const form = event.target.closest('.quick-stat-form');
    if (!form) return;
    if (event.target.value === event.target.defaultValue) delete form.dataset.edited;
    else form.dataset.edited = 'true';
  });
  panel.addEventListener('keydown', event => {
    const form = event.target.closest('.quick-stat-form');
    if (event.key !== 'Escape' || !form || form.dataset.saving) return;
    event.target.value = event.target.defaultValue;
    delete form.dataset.edited;
    event.target.blur();
  });
  panel.addEventListener('change', event => {
    const form = event.target.closest('.quick-stat-form');
    if (form) save(form);
  });
  panel.addEventListener('submit', event => {
    const form = event.target.closest('.quick-stat-form');
    if (!form) return;
    event.preventDefault();
    save(form);
  });
  panel.addEventListener('focusout', event => {
    if (event.target.matches('input[name="value"]')) {
      // Wait until the browser has moved focus to the next input.
      setTimeout(() => refresh(), 0);
    }
  });
}

// Patch one stat without replacing a focused input or discarding a draft.
export function updateStatElement(existing, incoming) {
  const form = existing.querySelector('.quick-stat-form');
  const input = form?.querySelector('[name="value"]');
  const nextInput = incoming.querySelector('[name="value"]');
  if (input && nextInput && (form.contains(document.activeElement) || form.dataset.edited || form.dataset.saving)) {
    if (!form.dataset.edited && !form.dataset.saving) {
      input.value = nextInput.value;
      input.defaultValue = nextInput.value;
      input.max = nextInput.max;
      existing.querySelector('.quick-stat-value span').textContent = incoming.querySelector('.quick-stat-value span').textContent;
    }
    // Effective HP can change with encumbrance or panic even during an edit.
    existing.querySelectorAll(':scope > small').forEach(node => node.remove());
    incoming.querySelectorAll(':scope > small').forEach(node => existing.append(node));
  } else {
    existing.replaceWith(incoming);
  }
}

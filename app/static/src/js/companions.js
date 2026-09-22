// Delegation also handles character sheets inserted through HTMX.
(() => {
  if (window.companionControlsInitialized) return;
  window.companionControlsInitialized = true;
  async function save(form) {
    const input = form.elements.value;
    if (input.disabled || !form.reportValidity()) return;
    const payload = new FormData(form);
    const status = form.querySelector('[role="status"]');
    input.disabled = true;
    status.textContent = '';
    try {
      const response = await fetch(form.action, {method: 'POST', body: payload});
      if (response.status !== 204) throw new Error('Save failed');
      input.defaultValue = input.value;
      status.textContent = form.dataset.saved;
    } catch {
      input.value = input.defaultValue;
      status.textContent = form.dataset.error;
    } finally {
      input.disabled = false;
    }
  }
  document.addEventListener('change', event => {
    const form = event.target.closest('.companion-stat-form');
    if (form) save(form);
  });
  document.addEventListener('submit', event => {
    if (event.target.matches('.companion-stat-form')) {
      event.preventDefault();
      save(event.target);
    }
  });
})();

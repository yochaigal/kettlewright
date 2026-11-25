// Forms with data-confirm="message" ask in a modal dialog (#kw-confirm-dialog) before submitting.
// data-confirm-label names the confirm button (e.g. "Hide"). A checkbox in the form with data-confirm-unchecked="message"
// asks that instead while it is unchecked (Delete campaign: Keep its parties). Submit buttons with form="…" work too:
// the event targets the form they submit. Without the dialog, forms submit as usual.
export function confirmMessage(form) {
  const unchecked = [...form.querySelectorAll('[data-confirm-unchecked]')].find(input => !input.checked);
  return unchecked ? unchecked.dataset.confirmUnchecked : form.dataset.confirm;
}

globalThis.document?.addEventListener('submit', (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.dataset.confirm) return;
  if (form.dataset.confirmed) { delete form.dataset.confirmed; return; }
  const dialog = document.getElementById('kw-confirm-dialog');
  if (!dialog?.showModal) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  dialog.querySelector('[data-confirm-message]').textContent = confirmMessage(form);
  const ok = dialog.querySelector('[data-confirm-ok]');
  ok.textContent = form.dataset.confirmLabel || ok.dataset.default;
  ok.onclick = () => {
    dialog.close();
    form.dataset.confirmed = '1';
    form.requestSubmit();
  };
  dialog.showModal();
}, true);

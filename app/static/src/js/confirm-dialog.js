// Forms with data-confirm="message" ask in a modal dialog (#kw-confirm-dialog) before submitting.
// data-confirm-label names the confirm button (e.g. "Hide"). Submit buttons with form="…" work too:
// the event targets the form they submit. Without the dialog, forms submit as usual.
//
// A form can also put choices in the dialog: a <template data-confirm-extra> with checkboxes, shown under the
// message. A checkbox with data-confirm-unchecked="message" asks that instead while unchecked (Delete campaign:
// Keep its parties). On Confirm, each checkbox's name is set in the form (a hidden field with its value) when
// checked, and removed when not; so the form says what to do by default, without the dialog.

export function confirmMessage(form, choices = []) {
  const unchecked = [...choices, ...form.querySelectorAll('[data-confirm-unchecked]')]
    .find(input => input.dataset?.confirmUnchecked && !input.checked);
  return unchecked ? unchecked.dataset.confirmUnchecked : form.dataset.confirm;
}

// The form's hidden fields follow the dialog's checkboxes (by name): present when checked, absent when not.
export function applyChoices(form, choices, document = globalThis.document) {
  for (const box of choices) {
    if (!box.name) continue;
    for (const field of form.querySelectorAll(`input[type="hidden"][name="${box.name}"]`)) field.remove();
    if (box.checked) {
      const field = document.createElement('input');
      field.type = 'hidden'; field.name = box.name; field.value = box.value || '1';
      form.append(field);
    }
  }
}

globalThis.document?.addEventListener('submit', (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.dataset.confirm) return;
  if (form.dataset.confirmed) { delete form.dataset.confirmed; return; }
  const dialog = document.getElementById('kw-confirm-dialog');
  if (!dialog?.showModal) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const message = dialog.querySelector('[data-confirm-message]');
  const slot = dialog.querySelector('[data-confirm-extra-slot]');
  const extra = form.querySelector('template[data-confirm-extra]');
  slot?.replaceChildren(...(extra && slot ? [extra.content.cloneNode(true)] : []));
  if (slot) slot.hidden = !extra;
  const choices = slot ? [...slot.querySelectorAll('input[type="checkbox"]')] : [];
  const ask = () => { message.textContent = confirmMessage(form, choices); };
  for (const box of choices) box.addEventListener('change', ask);
  ask();
  const ok = dialog.querySelector('[data-confirm-ok]');
  ok.textContent = form.dataset.confirmLabel || ok.dataset.default;
  ok.onclick = () => {
    applyChoices(form, choices);
    dialog.close();
    form.dataset.confirmed = '1';
    form.requestSubmit();
  };
  dialog.addEventListener('close', () => { if (slot) { slot.replaceChildren(); slot.hidden = true; } }, {once: true});
  dialog.showModal();
}, true);

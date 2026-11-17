import { styledConfirm } from "./utils.js";

// Monsters tab: the × on a monster card deletes it, after a confirmation.

function escapeHTML(text) {
  const element = document.createElement("div");
  element.textContent = text;
  return element.innerHTML;
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-confirm-delete]");
  if (!form) return;
  event.preventDefault();
  // The confirmation renders HTML: escape the monster's name, which is user text.
  const result = await styledConfirm(escapeHTML(form.dataset.confirmTitle), escapeHTML(form.dataset.confirm),
                                     form.dataset.confirmButton);
  if (!result.isConfirmed) return;
  form.querySelector("button[type=submit]").disabled = true;
  form.submit();
});

import utils from "./utils.js";

window.KW_alert = utils.styledAlert;

// A double click must not roll twice.
document.addEventListener('submit', event => {
  const form = event.target.closest('form[data-submit-once]');
  if (!form) return;
  if (form.dataset.submitted) { event.preventDefault(); return; }
  form.dataset.submitted = 'true';
  form.querySelectorAll('[type=submit]').forEach(button => { button.disabled = true; });
});

// Storage dialogs open in the page flow; bring them fully into view, as on Edit party.
for (const name of ['item-edit', 'container-edit']) {
  document.body.addEventListener(name, () => {
    const card = document.getElementById('modal-card');
    if (card?.scrollIntoViewIfNeeded) card.scrollIntoViewIfNeeded();
    else card?.scrollIntoView({block: 'nearest'});
  });
}

function updateWildernessAction(form) {
  const hasPC = Boolean(form.querySelector('input[name="participants"]:checked'));
  // Show the outcome of the current choices before anything is rolled or spent.
  const count = (name) => form.querySelectorAll(`input[name="${name}"]:checked`).length;
  const die = form.querySelector('[data-supply-die]');
  if (die) {
    const bonus = Math.min(4, Math.max(0, parseInt(form.elements.bonus.value, 10) || 0));
    die.textContent = hasPC ? 'd' + [4, 6, 8, 10, 12][Math.min(count('participants') - 1 + bonus, 4)] : '—';
  }
  const rations = form.querySelector('[data-camp-rations]');
  if (rations) rations.textContent = String(count('participants') + count('mounts'));
  const wrapper = form.querySelector('.wilderness-submit');
  wrapper.querySelector('button').disabled = !hasPC;
  if (hasPC) {
    wrapper.removeAttribute('title');
    wrapper.removeAttribute('aria-label');
    wrapper.removeAttribute('tabindex');
  } else {
    wrapper.title = wrapper.dataset.selectionHint;
    wrapper.setAttribute('aria-label', wrapper.dataset.selectionHint);
    wrapper.tabIndex = 0;
  }
  return hasPC;
}

// Browsers may restore checkbox values when returning through history.
window.addEventListener('pageshow', () => {
  document.querySelectorAll('.wilderness-form').forEach(updateWildernessAction);
});

document.addEventListener("DOMContentLoaded", function () {

  const tabs = Array.from(document.querySelectorAll('#party-tabs [role="tab"]'));
  function selectTab(tab) {
    tabs.forEach((item) => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
    });
  }
  function restoreTab() {
    selectTab(tabs.find(tab => '#' + tab.getAttribute('aria-controls') === location.hash) || tabs[0]);
  }
  if (tabs.length) {
    restoreTab();
    window.addEventListener('hashchange', restoreTab);
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        selectTab(tab);
        history.replaceState(null, '', '#' + tab.getAttribute('aria-controls'));
      });
      tab.addEventListener('keydown', (event) => {
        let target;
        if (event.key === 'ArrowRight') target = tabs[(index + 1) % tabs.length];
        if (event.key === 'ArrowLeft') target = tabs[(index + tabs.length - 1) % tabs.length];
        if (event.key === 'Home') target = tabs[0];
        if (event.key === 'End') target = tabs[tabs.length - 1];
        if (!target) return;
        event.preventDefault();
        target.click();
        target.focus();
      });
    });
  }


  document.querySelectorAll('.wilderness-form').forEach((form) => {
    updateWildernessAction(form);
    form.addEventListener('change', () => updateWildernessAction(form));
    form.addEventListener('input', () => updateWildernessAction(form));
    form.addEventListener('submit', (event) => {
      if (!updateWildernessAction(form)) event.preventDefault();
    });
  });

  // prepare join code button
  if (document.getElementById("join-code-button")) {
    document
      .getElementById("join-code-button")
      .addEventListener("click", function () {
        navigator.clipboard.writeText(joinCode).then(
          function () {
            utils.styledAlert(
              "Party join code",
              "Party join code copied to clipboard",
              "#party-form"
            );
          },
          function (err) {
            console.error("Could not copy text: ", err);
          }
        );
      });
  }

});

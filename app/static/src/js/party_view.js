import utils from "./utils.js";

window.KW_alert = utils.styledAlert;

function updateWildernessAction(form) {
  const hasPC = Boolean(form.querySelector('input[name="participants"]:checked'));
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

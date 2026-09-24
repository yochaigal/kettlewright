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
  console.log("DOMContentLoaded");

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

  // Initialize all collapsible sections

  function setupCollapseToggle(buttonId, contentId, iconId) {
    const button = document.getElementById(buttonId);
    const content = document.getElementById(contentId);
    const icon = document.getElementById(iconId);

    // Load initial state from localStorage
    const isHidden = localStorage.getItem(contentId) === "hidden";
    content.classList.toggle("hidden", isHidden);
    icon.classList.toggle("fa-chevron-down", !isHidden);
    icon.classList.toggle("fa-chevron-right", isHidden);

    button.addEventListener("click", function () {
      content.classList.toggle("hidden");
      icon.classList.toggle("fa-chevron-down");
      icon.classList.toggle("fa-chevron-right");

      // Save state to localStorage
      localStorage.setItem(
        contentId,
        content.classList.contains("hidden") ? "hidden" : "visible"
      );
    });
  }

  setupCollapseToggle(
    "party-members-collapse-button",
    "party-members-content",
    "party-members-collapse-icon"
  );
  setupCollapseToggle(
    "party-inventory-collapse-button",
    "inventory-container",
    "party-inventory-collapse-icon"
  );
});

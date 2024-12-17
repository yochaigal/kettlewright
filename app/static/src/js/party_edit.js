import utils from "./utils.js";

htmx.on("container-edit", function (evt) {
  document.getElementById("modal-card").scrollIntoViewIfNeeded();
});

htmx.on("item-edit", function (evt) {
  document.getElementById("modal-card").scrollIntoViewIfNeeded();
});

window.KW_alert = utils.styledAlert;

htmx.on("party-edit", function (evt) {
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

window.onscrollend = function () {
  let actionPad = document.getElementById("action-pad");
  if (window.scrollY != 0) {
    actionPad.classList.add("charedit-action-pad-top");
    actionPad.classList.remove("charedit-action-pad");
  } else {
    actionPad.classList.remove("charedit-action-pad-top");
    actionPad.classList.add("charedit-action-pad");
  }
};

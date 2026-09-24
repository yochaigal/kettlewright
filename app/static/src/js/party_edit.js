import utils from "./utils.js";

htmx.on("container-edit", function (evt) {
  document.getElementById("modal-card").scrollIntoViewIfNeeded();
});

htmx.on("item-edit", function (evt) {
  document.getElementById("modal-card").scrollIntoViewIfNeeded();
});

window.KW_alert = utils.styledAlert;

window.onscroll = function () {
  let actionPad = document.getElementById("action-pad");
  if (
    window.scrollY != 0 &&
    actionPad.classList.contains("charedit-action-pad")
  ) {
    actionPad.classList.add("charedit-action-pad-top");
    actionPad.classList.remove("charedit-action-pad");
    return;
  }
  if (
    window.scrollY == 0 &&
    actionPad.classList.contains("charedit-action-pad-top")
  ) {
    actionPad.classList.remove("charedit-action-pad-top");
    actionPad.classList.add("charedit-action-pad");
  }
};

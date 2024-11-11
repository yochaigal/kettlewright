import { handleClick, styledAlert, styledConfirm } from "./utils.js";

const redirectToCharacterPage = (element) => {
  const url = element.getAttribute("data-character");
  window.location.href = `${url}`;
}

const copyLink = (element) => {
  const urlName = element.dataset.urlName;
  const ownerUsername = element.dataset.ownerUsername;
  const link = `https://kettlewright.cairnrpg.com/users/${ownerUsername}/characters/${urlName}/`;
  navigator.clipboard.writeText(link);
}

document.addEventListener("DOMContentLoaded", function () {

  handleClick(".character-card", (event, element) => {
    if (!event.target.closest(".character-card-footer")) {
      redirectToCharacterPage(element);
    }
  });

  handleClick(".card-link-button", (event, element) => {
    event.stopPropagation();
    copyLink(element);
    styledAlert("Copy character link", "Link copied to clipboard");
  });

  handleClick(".card-delete-character-button", (event, element) => {
    event.stopPropagation(); // only to prevent opening character sheet
  });

});

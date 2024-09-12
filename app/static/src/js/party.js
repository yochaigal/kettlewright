// let editMode = false;
let characterList = [];

import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";

inventory.setItems(data);
inventory.setContainers(containersData);
inventoryUI.initialize("party");
inventoryModalUI.initialize("party");

function redirectToCharacterPage(element) {
  const owner = element.getAttribute("data-character-owner");
  const characterUrl = element.getAttribute("data-character-url");

  window.location = `${base_url}/users/${owner}/characters/${characterUrl}/`;
}

document.addEventListener("DOMContentLoaded", function () {
  // for every character card show the remove button if in edit mode

  // document.querySelectorAll(".character-card").forEach((element) => {
  //   if (editMode) {
  //     element.querySelector(".character-remove-button").classList.remove("hidden");
  //   }
  // });

  if (document.getElementById("join-code-button")) {
    document.getElementById("join-code-button").addEventListener("click", function () {
      navigator.clipboard.writeText(joinCode).then(
        function () {
          alert("Join code copied to clipboard");
        },
        function (err) {
          console.error("Could not copy text: ", err);
        }
      );
    });
  }

  document.querySelectorAll(".character-card").forEach((element) => {
    // create link
    element.addEventListener("click", function () {
      redirectToCharacterPage(element);
    });

    // adjust HP if overburdened
    const slots = inventory.getPartyMemberSlotsCount(JSON.parse(element.getAttribute("data-character-items")));
    if (slots > 10) {
      const hpText = element.querySelector(".hp-text");
      hpText.textContent = "0/" + element.getAttribute("data-character-hp-max");
      hpText.classList.add("red-text");
    }

    // fill options for transfer modal
    let characterInfo = {
      id: element.getAttribute("data-character-id"),
      name: element.getAttribute("data-character-name"),
      portraitURL: element.getAttribute("data-character-portrait-url"),
    };
    characterList.push(characterInfo);
  });

  //customize inventory for parties

  document.getElementById("inventory-title").classList.add("hidden");

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
      localStorage.setItem(contentId, content.classList.contains("hidden") ? "hidden" : "visible");
    });
  }

  setupCollapseToggle("party-members-collapse-button", "party-members-content", "party-members-collapse-icon");
  setupCollapseToggle("party-inventory-collapse-button", "party-inventory-content", "party-inventory-collapse-icon");

  // Add options for transfer modal
  const transferSelect = document.getElementById("party-item-transfer-modal-select");
  for (let i = 0; i < characterList.length; i++) {
    const option = document.createElement("option");
    option.value = characterList[i].id;
    option.text = characterList[i].name;
    transferSelect.add(option);
  }
});

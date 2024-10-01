// let editMode = false;
let characterList = [];

import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";

inventory.setItems(data);
inventory.setContainers(containersData);
inventoryUI.initialize("party");
inventoryModalUI.initialize("party");
inventoryUI.setMode("edit");

function redirectToCharacterPage(element) {
  const owner = element.getAttribute("data-character-owner");
  const characterUrl = element.getAttribute("data-character-url");

  window.location = `${base_url}/users/${owner}/characters/${characterUrl}/`;
}

function removeCharacterFromParty(element, event) {
  // Display a confirmation dialog
  const userConfirmed = confirm("Remove this character from the party and save changes?");

  // Proceed only if the user confirmed the action
  if (userConfirmed) {
    console.log(element);
    const removeID = JSON.parse(element.getAttribute("data-character-id"));
    members = JSON.parse(members);
    members = members.filter((member) => member !== removeID);
    document.getElementById("members").value = JSON.stringify(members);
    document.getElementById("party-form").submit();
  }
}

// function toggleEditMode() {
//   editMode = true;
//   inventoryUI.setMode("edit");

//   document.querySelectorAll(".edit-mode").forEach((element) => {
//     element.classList.remove("hidden");
//   });

//   document.querySelectorAll(".view-mode").forEach((element) => {
//     element.classList.add("hidden");
//   });
// }

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

  if (document.getElementById("party-edit-button")) {
    document.getElementById("party-edit-button").addEventListener("click", function () {
      toggleEditMode();
    });
  }

  if (document.getElementById("cancel-button")) {
    document.getElementById("cancel-button").addEventListener("click", function () {
      window.location = `${base_url}/users/${ownername}/parties/${partyURL}/`;
    });
  }

  if (document.getElementById("delete-party-button")) {
    document.getElementById("delete-party-button").addEventListener("click", function () {
      const userConfirmed = confirm("Are you sure you want to delete this party?");

      if (userConfirmed) {
        //redirect to delete party page
        window.location = `${base_url}/delete-party/${partyID}/`;
      }
    });
  }

  document.querySelectorAll(".character-card").forEach((element) => {
    // const owner = element.getAttribute("data-character-owner");

    element.addEventListener("click", function () {
      redirectToCharacterPage(element);
    });

    const removeButton = element.querySelector(".character-remove-button");
    if (removeButton) {
      removeButton.addEventListener("click", function (event) {
        event.stopPropagation();
        removeCharacterFromParty(element, event);
      });
    }

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

  // Handle form submission
  document.getElementById("party-form").addEventListener("submit", function (event) {
    const items = inventory.getItems();
    document.querySelector('input[name="items"]').value = JSON.stringify(items);
    const containers = inventory.getContainers();
    document.querySelector('input[name="containers"]').value = JSON.stringify(containers);
    const transfer = inventory.getTransfer();
    document.getElementById("transfer").value = JSON.stringify(transfer);
    // document.getElementById("events").value = events;
  });
});

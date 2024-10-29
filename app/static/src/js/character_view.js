import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";
import utils from "./utils.js";
import diceModal from "./dice_modal.js";
import notification from "./notification.js";

document.addEventListener("DOMContentLoaded", function () {
  // Initialize Inventory
  inventory.setItems(data);
  inventory.setContainers(containersData);
  inventoryUI.initialize("character");
  inventoryModalUI.initialize();

  // Setup Dice Rolling
  if (isOwner == "True") {
    inventoryUI.setShowDice(true);

    const showRollDiceNotifcation = (roll) => {
      // If in a party, show the notification to all party members
      if (party !== "None") {
        if (window.socketNotificationManager) {
          window.socketNotificationManager.rollDice(roll, party_id, character_id);
        } else {
          console.error("SocketNotificationManager not initialized");
        }
      } else {
        // Show a notification to only the owner
        notification.showNotification(`You rolled a ${roll}`);
      }
    };

    const rollDiceCallback = (sides) => {
      let result;
      console.log("Rolling dice", sides);
      if (sides.length === 1) {
        result = utils.rollDice(sides[0]);
        showRollDiceNotifcation(`${result} (d${sides})`);
      } else if (sides.length === 2) {
        result = utils.rollDoubleDice(sides[0], sides[1]);
        showRollDiceNotifcation(`${result[0]}, ${result[1]} (d${sides[0]}+d${sides[1]})`);
      }
    };

    inventoryUI.setRollDiceCallback(rollDiceCallback);

    document.getElementById("character-dice-button").addEventListener("click", () => {
      diceModal.showDiceModal();
    });

    diceModal.initialize(showRollDiceNotifcation);
  }

  // Handle Custom Portrait Image
  if (customImage == "None") {
    console.log("No custom image found, using default portrait");
    document.getElementById("portrait-image").src = "/static/images/portraits/default-portrait.webp";
  } else if (customImage == "False" || customImage == "false") {
    console.log("using a default portrait");
    document.getElementById("portrait-image").src = "/static/images/portraits/" + imageURL;
  } else {
    console.log("using a custom portrait");
    console.log(customImage);
    document.getElementById("portrait-image").src = imageURL;
  }

  // Adjust HP if overburdened
  const hpText = document.getElementById("hp-view-text");
  const overBurdened = inventory.getSlotsCount(0) >= 10;

  hpText.textContent = overBurdened ? "0/" + hpMax : hp + "/" + hpMax;
  hpText.classList.toggle("red-text", overBurdened);

  // Set default text for empty fields and fix line breaks
  function setDefaultText(elementId, value, defaultText) {
    const element = document.getElementById(elementId);
    if (!value || value == "None" || value == "") {
      element.innerText = defaultText;
    } else {
      element.innerHTML = value.replace(/\n/g, "<br>");
    }
  }

  setDefaultText("character-traits-view", traits, "This character has no traits...");
  setDefaultText("character-omens-view", omens, "This character has no omens...");
  setDefaultText("character-scars-view", scars, "This character has no scars...");
  setDefaultText("character-notes-view", notes, "This character has no notes...");
  setDefaultText("character-bonds-view", bonds, "This character has no bonds...");
  setDefaultText("character-description-view", description, "This character has no description...");
});

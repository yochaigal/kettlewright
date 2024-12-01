import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";
import utils from "./utils.js";
import diceModal from "./dice_modal.js";
import notification from "./notification.js";

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
  if (sides.length === 1) {
    result = utils.rollDice(sides[0]);
    showRollDiceNotifcation(`${result} (d${sides})`);
  } else if (sides.length === 2) {
    result = utils.rollDoubleDice(sides[0], sides[1]);
    showRollDiceNotifcation(`${result[0]}, ${result[1]} (d${sides[0]}+d${sides[1]})`);
  }
};

window.KW_rollDiceCallback = rollDiceCallback;

document.addEventListener("DOMContentLoaded", function () {
  // Initialize Inventory
  // inventory.setItems(data);
  // inventory.setContainers(containersData);
  // inventoryUI.initialize("character");
  // inventoryModalUI.initialize();

  // Setup Dice Rolling
  if (isOwner == "True") {
    // inventoryUI.setShowDice(true);
    // inventoryUI.setRollDiceCallback(rollDiceCallback);

    document.getElementById("character-dice-button").addEventListener("click", () => {
      console.log("rool dice");
      diceModal.showDiceModal();
    });

    diceModal.initialize(showRollDiceNotifcation);
  }

});

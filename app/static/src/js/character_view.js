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
  // Setup Dice Rolling
  if (isOwner == "True") {
    document.getElementById("character-dice-button").addEventListener("click", () => {
      diceModal.showDiceModal();
    });
    diceModal.initialize(showRollDiceNotifcation);
  }
  // Initial state is a view mode
  document.querySelectorAll(".fa-pencil").forEach((item) => {
    item.classList.add("hidden");
  });

  // Mode switch
  document.getElementById("charsheet-mode-switch").addEventListener("click", () => {
    document.querySelectorAll(".fa-pencil").forEach((item) => {
      item.classList.toggle("hidden");
    });
    document.querySelectorAll(".fa-eye").forEach((item) => {
      item.classList.toggle("hidden");
    });
    document.querySelectorAll(".fa-pen-to-square").forEach((item) => {
      item.classList.toggle("hidden");
    });
  });

});

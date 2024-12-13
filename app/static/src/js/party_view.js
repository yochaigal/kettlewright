import utils from "./utils.js";
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
  
  // Export functions to browser, maybe not recommended but useful...
  window.KW_rollDiceCallback = rollDiceCallback;
  window.KW_alert = utils.styledAlert;
  
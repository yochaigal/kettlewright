import './inventory_slots.js';
import utils from "./utils.js";
import diceModal from "./dice_modal.js";
import notification from "./notification.js";

const showRollDiceNotifcation = (roll) => {
  // If in a party, show the notification to all party members
  if (party_id !== "None") {
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

document.addEventListener("DOMContentLoaded", function () {
  // Setup Dice Rolling
  if (isOwner == "True") {
    document.getElementById("character-dice-button").addEventListener("click", () => {
      diceModal.showDiceModal();
    });
    diceModal.initialize(showRollDiceNotifcation);
  }
});

// HTMX swaps only the edited section; keyboard users get the same entry points.
document.addEventListener('keydown', event => {
  const trigger = event.target.closest('.character-inline-trigger');
  if (trigger && event.target === trigger && ['Enter', ' '].includes(event.key)) {
    event.preventDefault();
    trigger.click();
  }
  const form = event.target.closest('.character-inline-form');
  if (form && event.key === 'Escape') {
    event.preventDefault();
    form.querySelector('[data-inline-cancel]')?.click();
  }
});

document.addEventListener('htmx:afterSwap', event => {
  const form = event.detail.target.querySelector('.character-inline-form');
  if (!form) return;
  form.querySelectorAll('textarea').forEach(window.resizeTextarea);
  form.querySelector('input:not([type="hidden"]), textarea, select')?.focus();
});
document.addEventListener('input', event => {
  if (event.target.matches('.character-inline-form textarea')) window.resizeTextarea(event.target);
});
['omen-roll', 'scar-roll'].forEach(name => {
  document.addEventListener(name, () => {
    document.querySelectorAll('.character-inline-form textarea').forEach(window.resizeTextarea);
  });
});
['htmx:responseError', 'htmx:sendError'].forEach(name => {
  document.addEventListener(name, event => {
    const form = event.detail.elt.closest('.character-inline-form');
    if (form) form.querySelector('.inline-edit-error').textContent = form.dataset.saveError;
  });
});
document.addEventListener('character-section-saved', event => {
  party_id = event.detail.partyId === null ? 'None' : String(event.detail.partyId);
  if (event.detail.section === 'party') window.htmx.trigger(document.body, 'refresh-stats');
  if (['stats', 'party'].includes(event.detail.section)) {
    const inventory = document.querySelector('.slot-inventory');
    if (inventory && !inventory.querySelector('.inventory-modal')) {
      inventory.querySelector('.inventory-container-title-selected')?.click();
    }
  }
});

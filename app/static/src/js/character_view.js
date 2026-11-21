import './inventory_slots.js';
import utils from "./utils.js";
import diceModal from "./dice_modal.js";
import dice3d from "./dice3d.js";
import notification from "./notification.js";
import ownRolls from "./own_rolls.js";

// Every roll of this page goes through ownRolls, so the party's echo of it is not shown twice.
const requestRoll = (dice, label = "") => ownRolls.track(requestRollRaw(dice, label));
const requestRollRaw = async (dice, label = "") => {
  const monster = document.getElementById('monster-roll');
  if (monster) {
    const body = new URLSearchParams({dice, companion_id: monster.dataset.id, csrf_token: monster.dataset.csrf});
    if (document.getElementById('monster-public-roll').checked) body.set('public_roll', 'on');
    const response = await fetch(monster.dataset.url, {method: 'POST', body});
    if (!response.ok || response.redirected) throw new Error('Unable to roll dice.');
    return await response.json();
  }
  const sheet = document.getElementById('character-roll');
  if (sheet && typeof companion_id === "undefined") return postSheetRoll(label ? {dice, label} : {dice});
  const manager = window.socketNotificationManager;
  if (!manager) throw new Error("Unable to roll dice. Please check your connection.");
  const result = typeof companion_id !== "undefined"
    ? await manager.rollDice(dice, party_id, null, companion_id)
    : await manager.rollDice(dice, party_id, character_id);
  return result;
};

// The character's own rolls go over HTTP: they work even when the live socket cannot connect.
const rollOnSheet = (fields) => ownRolls.track(postSheetRoll(fields));
const postSheetRoll = async (fields) => {
  const sheet = document.getElementById('character-roll');
  const body = new URLSearchParams({...fields, csrf_token: sheet.dataset.csrf});
  let response;
  try {
    response = await fetch(sheet.dataset.url, {method: 'POST', body, cache: 'no-store'});
  } catch (_) {
    throw new Error(sheet.dataset.error);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok || response.redirected || data.error) throw new Error(data.error || sheet.dataset.error);
  return data;
};

// Item and attack dice roll straight away, without the modal: the 3D dice are the feedback. A weapon's
// damage is always announced once they settle, like a save ("Sword damage: 7 (d8)").
let directRolling = false;
const rollDiceCallback = async (sides, item = "") => {
  if (directRolling) return;
  directRolling = true;
  try {
    // Dice come as [6, 8], [4] or, from the impaired icon, "4".
    const dice = [].concat(sides).map(Number).map((side) => `d${side}`).join("+");
    const result = await requestRoll(dice, item);
    const shown = await dice3d.show(result);
    const sheet = document.getElementById("character-roll");
    if (item && sheet) {
      const rolled = `${result.values.join(", ")} (${dice})`;
      notification.showNotification(`${sheet.dataset.damage.replace("{item}", item)}: ${rolled}`);
    } else {
      notification.showNotification(`You rolled ${result.result}`);
    }
  } catch (error) {
    notification.showNotification(error.message);
  } finally {
    directRolling = false;
  }
};

// Saves (#398): STR, DEX or WIL on the sheet rolls a d20 against the current value. The server
// decides the roll and the outcome, and it goes to the party's roll history like any other roll.
document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-save-roll]");
  if (!button || directRolling) return;
  directRolling = true;
  button.disabled = true;
  try {
    const result = await rollOnSheet({dice: "d20", save: button.dataset.saveRoll});
    await dice3d.show(result);
    // Always say how the save went once the dice settle: it fails when the die is higher than the value.
    const sheet = document.getElementById("character-roll");
    const save = result.save;
    if (save) {
      const outcome = save.success ? sheet.dataset.success : sheet.dataset.failure;
      notification.showNotification(`${button.dataset.saveLabel}: ${result.values[0]} vs ${save.score} — ${outcome}`);
      const card = button.closest(".character-stat-card");
      card?.classList.remove("save-success", "save-failure");
      void card?.offsetWidth;  // Restart the highlight on a repeat roll.
      card?.classList.add(save.success ? "save-success" : "save-failure");
      setTimeout(() => card?.classList.remove("save-success", "save-failure"), 2500);
    } else {
      notification.showNotification(`${button.dataset.saveLabel}: ${result.result}`);
    }
  } catch (error) {
    notification.showNotification(error.message);
  } finally {
    directRolling = false;
    button.disabled = false;
  }
});

// Party button next to the dice: a dialog to go to the party or leave it, or to join one with a code.
// A wrong code stays in the dialog; a join or leave updates the Party section and this button (out of band).
document.addEventListener("click", (event) => {
  if (event.target.closest("#character-party-button")) {
    const dialog = document.getElementById("character-party-dialog");
    dialog?.querySelector(".character-party-error")?.replaceChildren();
    dialog?.showModal();
  } else if (event.target.closest("[data-party-cancel]")) {
    event.target.closest("dialog")?.close();
  }
});
document.addEventListener("htmx:confirm", (event) => {
  // Leaving asks first: a second click in the same dialog, so nothing is lost by a slip.
  const leave = event.detail.elt?.closest?.("#character-party-dialog")?.querySelector("[data-party-leave]");
  if (!leave || leave.dataset.armed === "true") return;
  event.preventDefault();
  leave.dataset.armed = "true";
  leave.dataset.label = leave.textContent;
  leave.textContent = leave.dataset.confirmText;
  leave.classList.add("is-danger");
});
document.addEventListener("htmx:beforeSwap", (event) => {
  const dialog = event.detail.elt?.closest?.("#character-party-dialog");
  if (!dialog) return;
  const saved = (event.detail.xhr.getResponseHeader("HX-Trigger") || "").includes("character-section-saved");
  if (saved) {
    dialog.close();
    return;
  }
  event.detail.shouldSwap = false;
  const page = new DOMParser().parseFromString(event.detail.serverResponse || "", "text/html");
  const message = page.querySelector('[role="alert"] li')?.textContent
    || document.querySelector(".character-inline-form")?.dataset.saveError || "Unable to save changes. Please try again.";
  dialog.querySelector(".character-party-error").textContent = message;
});
document.addEventListener("close", (event) => {
  // Closing the dialog disarms Leave.
  const leave = event.target.querySelector?.("[data-party-leave][data-armed='true']");
  if (!leave) return;
  leave.dataset.armed = "false";
  leave.textContent = leave.dataset.label;
  leave.classList.remove("is-danger");
}, true);

// Export functions to browser, maybe not recommended but useful...
window.KW_rollDiceCallback = rollDiceCallback;
window.KW_alert = utils.styledAlert;

document.addEventListener("DOMContentLoaded", function () {
  // Setup Dice Rolling
  if (isOwner == "True") {
    const publicToggle = document.getElementById('monster-public-roll');
    if (publicToggle) {
      publicToggle.checked = false;
    }
    document.getElementById("character-dice-button").addEventListener("click", () => {
      diceModal.showDiceModal();
    });
    diceModal.initialize(requestRoll);
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

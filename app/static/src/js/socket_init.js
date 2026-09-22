// this script is called from base.html

import socketNotificationManager from "./socket_notifications.js";
import { initializeRollHistory, refreshRollHistory } from "./party_roll_history.js";
import { initializePartyMembers, refreshPartyMembers } from "./party_members.js";
import { initializeCharacterStats, refreshCharacterStats } from "./character_stats.js";

document.addEventListener("DOMContentLoaded", function () {
  socketNotificationManager.init();
  window.socketNotificationManager = socketNotificationManager;
  initializeRollHistory();
  initializePartyMembers();
  initializeCharacterStats();
});

document.addEventListener('htmx:afterSettle', initializeRollHistory);
document.addEventListener('htmx:afterSettle', initializePartyMembers);
document.addEventListener('htmx:afterSettle', initializeCharacterStats);
window.addEventListener('pageshow', refreshRollHistory.bind(null, null));
window.addEventListener('pageshow', refreshPartyMembers.bind(null, null));
window.addEventListener('pageshow', refreshCharacterStats.bind(null, null));
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) refreshRollHistory();
  if (!document.hidden) refreshPartyMembers();
  if (!document.hidden) refreshCharacterStats();
});

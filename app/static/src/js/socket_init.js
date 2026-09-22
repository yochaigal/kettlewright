// this script is called from base.html

import socketNotificationManager from "./socket_notifications.js";
import { initializeRollHistory, refreshRollHistory } from "./party_roll_history.js";

document.addEventListener("DOMContentLoaded", function () {
  socketNotificationManager.init();
  window.socketNotificationManager = socketNotificationManager;
  initializeRollHistory();
});

document.addEventListener('htmx:afterSettle', initializeRollHistory);
window.addEventListener('pageshow', refreshRollHistory.bind(null, null));
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) refreshRollHistory();
});

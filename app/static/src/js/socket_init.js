import socketNotificationManager from "./socket_notifications.js";

document.addEventListener("DOMContentLoaded", function () {
  socketNotificationManager.init();
  window.socketNotificationManager = socketNotificationManager;
});

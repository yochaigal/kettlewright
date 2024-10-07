const notification = {
  notifications: [],
  maxNotifications: 5,

  showNotification(message) {
    const notification = document.createElement("div");
    notification.className = "notification";
    notification.style.position = "fixed";
    notification.style.right = "20px";
    // notification.style.backgroundColor = "rgba(0,0,0,0.8)";
    notification.style.color = "white";
    notification.style.padding = "10px";
    notification.style.borderRadius = "5px";
    notification.style.marginBottom = "10px";
    notification.style.transition = "all 0.5s ease";
    notification.style.opacity = "0";
    notification.style.zIndex = "1000";
    notification.style.display = "flex";
    notification.style.alignItems = "center";
    notification.style.justifyContent = "space-between";
    notification.style.minHeight = "40px";
    notification.onclick = () => this.removeNotification(notification);
    notification.style.cursor = "pointer";

    const messageSpan = document.createElement("span");
    messageSpan.textContent = message;
    messageSpan.style.flex = "1";
    notification.appendChild(messageSpan);

    const closeButton = document.createElement("span");
    closeButton.innerHTML = "&#215;";

    closeButton.style.marginLeft = "10px";
    closeButton.setAttribute("aria-label", "Close notification");

    closeButton.style.cursor = "pointer";
    closeButton.style.flexShrink = "0";
    // closeButton.onclick = () => this.removeNotification(notification);
    notification.appendChild(closeButton);

    document.body.appendChild(notification);

    this.notifications.push(notification);

    if (this.notifications.length > this.maxNotifications) {
      const oldNotification = this.notifications.shift();
      oldNotification.remove();
    }

    this.updateNotificationPositions();

    setTimeout(() => {
      notification.style.opacity = "1";
    }, 10);
  },

  removeNotification(notification) {
    notification.style.opacity = "0";
    setTimeout(() => {
      const index = this.notifications.indexOf(notification);
      if (index > -1) {
        this.notifications.splice(index, 1);
      }
      notification.remove();
      this.updateNotificationPositions();
    }, 100);
  },

  updateNotificationPositions() {
    let bottomPosition = 20;
    this.notifications
      .slice()
      .reverse()
      .forEach((notification) => {
        notification.style.bottom = `${bottomPosition}px`;
        bottomPosition += notification.offsetHeight + 10;
      });
  },
};

export default notification;

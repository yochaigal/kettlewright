import notification from "./notification.js";

const socketNotificationManager = {
  socket: null,
  notifications: [],
  maxNotifications: 5,

  init() {
    this.socket = io();
    this.initializeSocketListeners();
  },

  initializeSocketListeners() {
    this.socket.on("connect", () => {
      console.log("Connected to Flask server");
      this.registerUser();
    });

    this.socket.on("disconnect", () => {
      console.log("Disconnected from Flask server");
    });

    this.socket.on("dice_rolled", (data) => {
      // console.log("Dice roll received:", data);
      notification.showNotification(data);
    });
  },

  registerUser() {
    this.socket.emit("register");
  },

  rollDice(roll, partyId, characterId) {
    const data = {
      roll: roll,
      party_id: partyId,
      character_id: characterId,
    };
    this.socket.emit("roll_dice", data);
    // console.log("Dice roll sent:", data);
  },
};

export default socketNotificationManager;

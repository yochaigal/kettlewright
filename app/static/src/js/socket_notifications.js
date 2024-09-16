import notification from "./notification.js";

const socketNotificationManager = {
  socket: null,
  notifications: [],
  connectionAttempts: 0,
  maxConnectionAttempts: 5,

  init() {
    this.connectSocket();
  },

  connectSocket() {
    if (this.connectionAttempts >= this.maxConnectionAttempts) {
      console.error("Max connection attempts reached. Please try again later.");
      return;
    }

    this.socket = io({
      transports: ["websocket"],
      upgrade: false,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: 3,
      timeout: 10000,
    });

    this.initializeSocketListeners();
    this.connectionAttempts++;
  },

  initializeSocketListeners() {
    this.socket.on("connect", () => {
      console.log("Connected to Flask server");
      this.connectionAttempts = 0;
      this.registerUser();
    });

    this.socket.on("connect_error", (error) => {
      console.error("Connection error:", error);
      setTimeout(() => this.connectSocket(), 5000);
    });

    this.socket.on("disconnect", (reason) => {
      console.log("Disconnected from Flask server:", reason);
      if (reason === "io server disconnect") {
        // the disconnection was initiated by the server, reconnect manually
        setTimeout(() => this.connectSocket(), 5000);
      }
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
    if (this.socket && this.socket.connected) {
      this.socket.emit("roll_dice", data);
      // console.log("Dice roll sent:", data);
    } else {
      console.error("Socket not connected. Unable to send dice roll.");
      notification.showNotification("Unable to send dice roll. Please check your connection.");
    }
  },
};

export default socketNotificationManager;

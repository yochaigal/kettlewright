import notification from "./notification.js";
import { refreshRollHistory } from "./party_roll_history.js";
import { refreshPartyMembers } from "./party_members.js";
import { refreshCharacterStats } from "./character_stats.js";

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
      refreshRollHistory();
      refreshPartyMembers();
      refreshCharacterStats();
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

    this.socket.on("rate_limited", (data) => {
      notification.showNotification(data.message);
    });

    this.socket.on("dice_rolled", (data) => {
      // console.log("Dice roll received:", data);
      notification.showNotification(data);
    });
    this.socket.on("roll_history_changed", (data) => {
      refreshRollHistory(data.party_id);
    });
    this.socket.on("party_members_changed", (data) => {
      refreshPartyMembers(data.party_id);
      refreshCharacterStats(data.party_id);
    });
  },

  registerUser() {
    this.socket.emit("register");
  },

  rollDice(dice, partyId, characterId) {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error("Unable to roll dice. Please check your connection."));
        return;
      }
      const timer = setTimeout(() => {
        reject(new Error("No response received. Check the party roll history before rolling again."));
      }, 5000);
      this.socket.emit("roll_dice", {
        dice, party_id: partyId, character_id: characterId,
      }, (response) => {
        clearTimeout(timer);
        if (!response || response.error) {
          reject(new Error(response?.error || "Unable to roll dice. Please try again."));
        } else {
          resolve(response);
        }
      });
    });
  },
};

export default socketNotificationManager;

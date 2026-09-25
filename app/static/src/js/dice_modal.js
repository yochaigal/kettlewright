import notification from "./notification.js";

const diceModal = {
  mode: "character",
  resultText: document.getElementById("dice-modal-roll-result"),

  initialize(rollCallback) {
    document.getElementById("dice-modal-background").addEventListener("click", () => {
      document.getElementById("dice-modal").classList.remove("is-active");
    });

    const roll = async (dice) => {
      const buttons = document.querySelectorAll("#dice-modal button");
      buttons.forEach((button) => { button.disabled = true; });
      try {
        const result = await rollCallback(dice);
        this.resultText.textContent = result.values.join(", ");
      } catch (error) {
        notification.showNotification(error.message);
      } finally {
        buttons.forEach((button) => { button.disabled = false; });
      }
    };
    [4, 6, 8, 10, 12, 20, 100].forEach((sides) => {
      document.getElementById(`dice-modal-d${sides}-button`)
        .addEventListener("click", () => roll(`d${sides}`));
    });
    [4, 6, 8, 10, 12].forEach((sides) => {
      document.getElementById(`dice-modal-d${sides}+d${sides}-button`)
        .addEventListener("click", () => roll(`d${sides}+d${sides}`));
    });

    // Show/hide d100 based on mode
    this.updateD100Visibility();

    // Install event listener for modal ESC.
    document.addEventListener('keyup', (e) => {
      const dm = document.getElementById("dice-modal");
      if (e.code != "Escape" || !dm) return;
      if (dm.classList.contains("is-active")) {
        dm.classList.remove("is-active");
      };
    });
  },

  updateD100Visibility() {
    const d100Button = document.getElementById("dice-modal-d100-button");
    d100Button.style.display = this.mode === "party" ? "inline-flex" : "none";
  },

  showDiceModal() {
    document.getElementById("dice-modal").classList.add("is-active");
    this.resultText.textContent = 0;
  },

  setMode(mode) {
    this.mode = mode;
    this.updateD100Visibility();
  },
};

export default diceModal;

import utils from "./utils.js";

const diceModal = {
  mode: "character",
  resultText: document.getElementById("dice-modal-roll-result"),

  initialize(rollCallback) {
    document.getElementById("dice-modal-background").addEventListener("click", () => {
      console.log("Background clicked");
      document.getElementById("dice-modal").classList.remove("is-active");
    });

    const singleDiceTypes = [4, 6, 8, 10, 12, 20, 100];
    singleDiceTypes.forEach((sides) => {
      const buttonId = `dice-modal-d${sides}-button`;
      document.getElementById(buttonId).addEventListener("click", () => {
        let result = utils.rollDice(sides);
        this.resultText.textContent = result.toString();
        rollCallback(`${result} (d${sides})`);
      });
    });

    const doubleDiceTypes = [4, 6, 8, 10, 12];
    doubleDiceTypes.forEach((sides) => {
      const buttonId = `dice-modal-d${sides}+d${sides}-button`;
      document.getElementById(buttonId).addEventListener("click", () => {
        let result = utils.rollDoubleDice(sides);
        rollCallback(`${result[0]}, ${result[1]} (d${sides}+d${sides})`);
      });
    });

    // Show/hide d100 based on mode
    this.updateD100Visibility();
  },

  // rollDice(sides) {
  //   const result = Math.floor(Math.random() * sides) + 1;
  //   console.log(`Rolled a d${sides} and got a ${result}`);
  //   this.resultText.textContent = result.toString();
  //   return `d${sides} (${result})`;
  // },

  // rollDoubleDice(sides) {
  //   const roll1 = Math.floor(Math.random() * sides) + 1;
  //   const roll2 = Math.floor(Math.random() * sides) + 1;
  //   console.log(`Rolled d${sides}+d${sides} and got ${roll1} and ${roll2}`);
  //   this.resultText.textContent = `${roll1}, ${roll2}`;
  //   return `d${sides}+d${sides} (${roll1}, ${roll2})`;
  // },

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

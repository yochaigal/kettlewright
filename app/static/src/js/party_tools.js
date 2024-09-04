const diceButton = document.getElementById("tools-dice-button");
const diceResult = document.getElementById("tools-dice-result");

function rollDice(roll) {
  const data = {
    roll: roll,
    username: username,
    party_id: party_id,
    user_id: user_id,
  };
  socket.emit("roll_dice", data);
}

socket.on("dice_rolled", function (data) {
  console.log(data);
});

diceButton.addEventListener("click", () => {
  // roll a random number 1-6
  const roll = Math.floor(Math.random() * 6) + 1;
  diceResult.textContent = roll;
  rollDice(roll);
});

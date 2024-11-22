// NOTE: duplicate?

// import inventory from "./inventoryData.js";
// import inventoryUI from "./inventoryUI.js";
// import inventoryModalUI from "./inventoryModalUI.js";

// let mode = "view_character";

// console.log(partyName);

// inventory.setItems(data);
// inventory.setContainers(containersData);
// inventoryUI.initialize();
// inventoryModalUI.initialize();

// // const deprivedContainer = document.getElementById("deprived-grid-container");
// // const deprivedIcon = document.getElementById("deprived-icon");
// // const hpContainer = document.getElementById("edit-page-hp-container");

// console.log("custom image", customImage);
// if (customImage == "None") {
//   document.getElementById("portrait-image").src = "/static/images/portraits/default-portrait.webp";
// } else if (customImage == "False") {
//   document.getElementById("portrait-image").src = "/static/images/portraits/" + imageURL;
// } else {
//   document.getElementById("portrait-image").src = imageURL;
// }

// // if (deprived == "True") {
// //   deprivedContainer.classList.remove("deprived-inactive");
// //   deprivedContainer.classList.add("deprived-active");
// //   deprivedIcon.classList.add("red-filter");
// //   deprivedIcon.classList.remove("invert-filter");
// //   hpContainer.classList.add("inactive");
// // } else {
// //   deprivedContainer.classList.add("deprived-inactive");
// //   deprivedContainer.classList.remove("deprived-active");
// //   deprivedIcon.classList.remove("red-filter");
// //   deprivedIcon.classList.add("invert-filter");
// //   hpContainer.classList.remove("inactive");
// // }

// const hpText = document.getElementById("hp-view-text");
// const overBurdened = inventory.getSlotsCount(0) > 10;

// hpText.textContent = overBurdened ? "0/" + hpMax : hp + "/" + hpMax;
// hpText.classList.toggle("red-text", overBurdened);

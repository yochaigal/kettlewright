import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";

// Initialize Inventory
inventory.setItems(data);
inventory.setContainers(containersData);
inventoryUI.getPrintableInventory();

// Set Portrait Image
if (customImage == "None") {
  document.getElementById("portrait-image").src = "/static/images/portraits/default-portrait.webp";
} else if (customImage == "False") {
  document.getElementById("portrait-image").src = "/static/images/portraits/" + imageURL;
} else {
  document.getElementById("portrait-image").src = imageURL;
}

// Get Armor Count
let armor = inventory.getArmorValue().armor;
document.getElementById("armor-counter").textContent = armor;

// Create Printble Inventory
const printableInventory = inventoryUI.getPrintableInventory();
const mainInventoryContainer = document.getElementById("main-inventory-container");
const additionalInventoryContainer = document.getElementById("additional-inventory-container");

printableInventory.forEach((container, index) => {
  if (index === 0) {
    mainInventoryContainer.appendChild(container);
  } else {
    additionalInventoryContainer.appendChild(container);
  }
});

// Hide unessessary elements
document.getElementById("navbar").classList.add("hidden");

if (!description || description == "None" || description == "") {
  document.getElementById("character-print-description-container").classList.add("hidden");
}

if (!scars || scars == "None" || scars == "") {
  document.getElementById("character-print-scars-container").classList.add("hidden");
}

if (!omens || omens == "None" || omens == "") {
  document.getElementById("character-print-omens-container").classList.add("hidden");
}

if (!notes || notes == "None" || notes == "") {
  document.getElementById("character-print-notes-container").classList.add("hidden");
}

// Open the print dialog
window.print();

import { createElement } from "./utils.js";
import inventoryUI from "./inventoryUI.js";

const marketplace = {
  selectedItems: [],
  gold: 0,
  initialGold: 0,
  saveItems: null,
  saveGold: null,
  addedBy: null,

  initialize(items, mode = "gear", gld = 20, saveItems = null, saveGold = null) {
    console.log("Initializing marketplace with items: ", items);

    this.gold = this.initialGold = gld;
    this.saveItems = saveItems;
    this.saveGold = saveGold;

    const categories = {
      Gear: items.Gear,
      Armor: items.Armor,
      Weapons: items.Weapons,
    };

    this.setupUI(categories, mode);
    this.populateTable(categories, mode);
    this.updateGoldDisplay();
  },

  setupUI(categories, mode) {
    const categoryToggles = document.getElementById("category-toggles");
    const clearSelectionButton = document.getElementById("clear-selection-button");
    const saveButton = document.getElementById("marketplace-save-button");
    const cancelButton = document.getElementById("marketplace-cancel-button");
    const marketplaceBackground = document.getElementById("marketplace-modal-background");

    if (mode === "gear") {
      if (categoryToggles) categoryToggles.style.display = "none";
      categories.Armor = {};
      categories.Weapons = {};
    } else {
      if (categoryToggles) {
        categoryToggles.style.display = "block";
        this.setupCategoryToggles(categories);
      }
    }

    if (clearSelectionButton) {
      clearSelectionButton.addEventListener("click", () => this.clearSelection());
    }

    if (saveButton) {
      saveButton.addEventListener("click", () => this.handleSave());
    }

    if (cancelButton) {
      cancelButton.addEventListener("click", () => this.handleCancel());
    }

    if (marketplaceBackground) {
      marketplaceBackground.addEventListener("click", () => this.handleCancel());
    }
  },

  setAddedBy(addedBy) {
    this.addedBy = addedBy;
  },

  setupCategoryToggles(categories) {
    Object.keys(categories).forEach((category) => {
      const toggleId = `toggle-${category.toLowerCase()}`;
      const toggle = document.getElementById(toggleId);
      if (toggle) {
        toggle.addEventListener("change", (event) => {
          const rows = document.querySelectorAll(`.category-${category.toLowerCase()}`);
          rows.forEach((row) => row.classList.toggle("hidden", !event.target.checked));
        });
      }
    });
  },

  populateTable(categories, mode) {
    const tableBody = document.getElementById("marketplace-table-body");
    Object.entries(categories).forEach(([category, categoryItems]) => {
      Object.entries(categoryItems).forEach(([itemName, item]) => {
        const row = this.createItemRow(itemName, item, category, mode);
        tableBody.appendChild(row);
      });
    });
  },

  createItemRow(itemName, item, category, mode) {
    const row = document.createElement("tr");
    row.classList.add(`category-${category.toLowerCase()}`);
    if (mode === "gear" && category !== "Gear") {
      row.classList.add("hidden");
    }

    row.appendChild(this.createNameCell(itemName, item));
    row.appendChild(this.createCell("item-cost", item.cost));
    row.appendChild(this.createCell("item-type", category));
    row.appendChild(this.createQuantityCell(itemName, item, category));

    return row;
  },

  createNameCell(itemName, item) {
    const nameCell = this.createCell("item-name", itemName + " ");
    if (item.tags && item.tags.length > 0) {
      nameCell.appendChild(this.createTagsSpan(item));
    }
    return nameCell;
  },

  createTagsSpan(item) {
    const tagsSpan = document.createElement("span");
    tagsSpan.appendChild(document.createTextNode("("));
    item.tags.forEach((tag, index) => {
      tagsSpan.appendChild(this.createTagElement(tag, item));
      if (index < item.tags.length - 1) {
        tagsSpan.appendChild(document.createTextNode(", "));
      }
    });
    tagsSpan.appendChild(document.createTextNode(")"));
    return tagsSpan;
  },

  createTagElement(tag, item) {
    switch (tag) {
      case "bulky":
      case "petty":
        return createElement("i", { content: tag });
      case "uses":
        return document.createTextNode(item.uses === 1 ? "1 use" : `${item.uses} uses`);
      case "charges":
        return document.createTextNode(`${item.charges}/${item.max_charges} charges`);
      default:
        return document.createTextNode(tag);
    }
  },

  createCell(className, content) {
    const cell = document.createElement("td");
    cell.className = className;
    cell.textContent = content;
    return cell;
  },

  createQuantityCell(itemName, item, category) {
    const quantityCell = document.createElement("td");
    quantityCell.className = "marketpace-item-quantity";

    const minusButton = this.createButton("-", "marketpace-quantity-button minus");
    const quantityDisplay = this.createQuantityDisplay();
    const plusButton = this.createButton("+", "marketpace-quantity-button plus");

    minusButton.addEventListener("click", () => this.updateQuantity(-1, itemName, item, category, quantityDisplay));
    plusButton.addEventListener("click", () => this.updateQuantity(1, itemName, item, category, quantityDisplay));

    quantityCell.append(minusButton, quantityDisplay, plusButton);
    return quantityCell;
  },

  createButton(text, className) {
    const button = document.createElement("span");
    button.textContent = text;
    button.className = className;
    return button;
  },

  createQuantityDisplay() {
    const display = document.createElement("span");
    display.textContent = "0";
    display.className = "marketplace-quantity-display";
    return display;
  },

  updateQuantity(change, itemName, item, category, quantityDisplay) {
    const currentQuantity = parseInt(quantityDisplay.textContent);
    const newQuantity = Math.max(0, currentQuantity + change);

    if (change > 0 && this.gold < item.cost) {
      alert("Not enough gold to purchase this item!");
      return;
    }

    quantityDisplay.textContent = newQuantity;

    if (change > 0) {
      this.selectedItems.push({ name: itemName, category, added_by: this.addedBy, ...item });
      this.gold -= item.cost;
    } else if (change < 0) {
      const index = this.selectedItems.findIndex((i) => i.name === itemName);
      if (index !== -1) {
        this.selectedItems.splice(index, 1);
        this.gold += item.cost;
      }
    }

    this.updateGoldDisplay();
  },

  getSelectedItems() {
    return this.selectedItems;
  },

  getRemainingGold() {
    return this.gold;
  },

  setGoldCallback(callback) {
    this.saveGold = callback;
  },

  updateGoldDisplay() {
    const goldDisplay = document.getElementById("gold-display");
    if (goldDisplay) {
      goldDisplay.textContent = `Gold: ${this.gold}`;
    }
  },

  setGold(gold) {
    this.initialGold = gold;
    this.gold = gold;
    this.updateGoldDisplay();
  },

  clearSelection() {
    const quantityDisplays = document.querySelectorAll(".marketplace-quantity-display");
    quantityDisplays.forEach((display) => {
      display.textContent = "0";
    });

    this.gold = this.initialGold;
    this.selectedItems = [];
    this.updateGoldDisplay();
    console.log("All selections cleared. Remaining gold:", this.gold);
  },

  handleSave() {
    if (typeof this.saveItems === "function") {
      this.saveItems(this.selectedItems);
    }

    if (typeof this.saveGold === "function") {
      this.saveGold(this.gold);
    }

    this.hideMarketplace();
    inventoryUI.refreshInventory();
  },

  handleCancel() {
    this.hideMarketplace();
  },

  showMarketplace() {
    inventoryUI.hideSaveFooter();
    this.clearSelection();
    //get the gold value if in  character edit mode
    if (document.getElementById("gold-input")) {
      this.initialGold = document.getElementById("gold-input").value;
      this.gold = this.initialGold;
    }

    this.updateGoldDisplay();
    document.getElementById("marketplace-modal").classList.add("is-active");
  },

  hideMarketplace() {
    document.getElementById("marketplace-modal").classList.remove("is-active");
    inventoryUI.showSaveFooter();
  },
};

export default marketplace;

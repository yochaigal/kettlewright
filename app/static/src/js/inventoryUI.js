import inventory from "./inventoryData.js";
import inventoryModalUI from "./inventoryModalUI.js";
import marketplace from "./marketplace.js";
import { createElement } from "./utils.js";

const inventoryUI = {
  mode: "view",
  page: "character",
  selectedContainer: 0,
  rollDiceCallback: null,
  showDice: false,

  initialize(page = "character", showDice = false) {
    this.setPage(page);
    this.showDice = showDice;
    this.refreshInventory(0);

    document.getElementById("add-item-button").addEventListener("click", () => {
      inventoryModalUI.showAddEditItemModal();
    });
    document.getElementById("add-container-button").addEventListener("click", () => {
      inventoryModalUI.showContainerModal();
    });
    document.getElementById("show-marketplace-button").addEventListener("click", () => {
      marketplace.showMarketplace();
    });

    if (page === "party") {
      document.getElementById("add-fatigue-button").classList.add("hidden");
      document.getElementById("show-marketplace-button").classList.add("hidden");
    } else {
      document.getElementById("add-fatigue-button").addEventListener("click", () => {
        inventory.addFatigue();
        this.refreshInventory();
      });
    }
  },

  setMode(mode) {
    this.mode = mode;
    this.refreshInventory();
    document.getElementById("add-item-button").classList.toggle("hidden", mode === "view");
    document.getElementById("add-container-button").classList.toggle("hidden", mode === "view");

    if (this.page !== "party") {
      document.getElementById("add-fatigue-button").classList.toggle("hidden", mode === "view");
      document.getElementById("show-marketplace-button").classList.toggle("hidden", mode === "view");
    }
  },

  setPage(page) {
    this.page = page;
  },

  addItemToDOM({ name, tags, uses, charges, max_charges, index, id, location = 0, description = "", carrying = null }) {
    // ensure that numbers are not strings
    uses = +uses;
    charges = +charges;
    id = +id;
    max_charges = +max_charges;

    // Create the item container
    const itemContainer = createElement("span", {
      classes: ["inventory-item-container"],
      // attributes: { draggable: "true" },
    });

    // Create an empty name span
    const nameDiv = document.createElement("span");
    itemContainer.appendChild(nameDiv);

    // check for dice tags, and return an array of dice values
    const extractDiceInfo = (tags) => {
      const diceRegex = /d(\d+)(?:\s*\+\s*d(\d+))?/;
      const diceTag = tags.find((tag) => diceRegex.test(tag));

      if (!diceTag) return null;

      const match = diceTag.match(diceRegex);
      if (match[2]) {
        // Dual dice case: "d4 + d6"
        return [parseInt(match[1], 10), parseInt(match[2], 10)];
      } else {
        // Single die case: "d6"
        return [parseInt(match[1], 10)];
      }
    };

    if (name !== "Fatigue" && name !== "empty slot" && carrying == null) {
      const rightSideIcons = createElement("span", {
        classes: ["inventory-item-button-container"],
      });

      // Add a dice icon
      if (this.showDice && this.mode === "view" && tags) {
        const diceInfo = extractDiceInfo(tags);
        if (diceInfo) {
          const diceIcon = createElement("i", {
            classes: ["fa-solid", "fa-dice", "inventory-dice"],
            ariaLabel: "Roll Dice",
            events: {
              click: () => {
                this.rollDiceCallback(diceInfo);
              },
            },
          });
          rightSideIcons.appendChild(diceIcon);
        }
      }

      // Add edit button in edit mode
      if (this.mode === "edit") {
        const editButton = createElement("span", {
          classes: ["inventory-item-edit-button"],
          attributes: { "data-item-id": id.toString() },
          ariaLabel: "Edit Item",
          content: "edit",
          events: {
            click: () => {
              this.editItem(id);
            },
          },
        });
        rightSideIcons.appendChild(editButton);
      }
      // Add view description button if description exists and we're not in edit mode
      else if (description !== "" && description !== "This item has no description...") {
        const infoButton = createElement("span", {
          classes: ["inventory-item-info-button"],
          ariaLabel: "View Item Description",
          content: "( i )",
          events: {
            click: () => {
              this.showItemDescription(id);
            },
          },
        });
        rightSideIcons.appendChild(infoButton);
      }

      if (rightSideIcons.children.length > 0) {
        itemContainer.appendChild(rightSideIcons);
      }

      nameDiv.innerHTML = name;
      nameDiv.id = "item-name-" + index; // Unique ID for each item
      nameDiv.classList.add("item-name", "inventory-item-text");
    } else if (name === "Fatigue" || carrying !== null) {
      if (this.mode === "edit") {
        const deleteIcon = createElement("i", {
          classes: ["inventory-item-button-container", "inventory-item-edit-button"],
          ariaLabel: "Delete Item",
          events: {
            click: () => {
              inventory.deleteItem(id);
              this.refreshInventory(location);
            },
          },
          content: "x",
        });

        itemContainer.appendChild(deleteIcon);
      }
      if (name === "Fatigue") {
        nameDiv.innerHTML = "Fatigue";
        nameDiv.classList.add("fatigue-text");
      } else if (carrying !== null) {
        nameDiv.innerHTML = name;
        nameDiv.classList.add("carrying-text");
      }
    }

    const tagSpan = createElement("span", { classes: ["item-tags"] });
    const appendedTags = [];

    if (tags) {
      let bonusDefense = tags.includes("bonus defense");
      tags.forEach((tag) => {
        let element = null;
        switch (tag) {
          case "bulky":
          case "petty":
            element = createElement("i", { content: tag });
            break;
          case "uses":
          case "charges":
            const tagName =
              tag === "uses" ? (uses === 1 ? "1 use" : `${uses} uses`) : `${charges}/${max_charges} charges`;
            element = document.createTextNode(tagName);

            if (this.mode === "edit") {
              const decrementIcon = createElement("span", {
                classes: ["inventory-item-button", "inventory-item-plus-minus"],
                ariaLabel: "Decrease Uses or Charges",
                content: "[ -",
              });
              decrementIcon.addEventListener("click", () => {
                this.updateItemUsesOrCharges(tag, id, -1, uses, charges, max_charges, location);
              });

              const slash = createElement("span", {
                content: " / ",
              });

              const incrementIcon = createElement("span", {
                classes: ["inventory-item-button", "inventory-item-plus-minus"],
                ariaLabel: "Increase Uses or Charges",
                content: "+ ]",
              });

              incrementIcon.addEventListener("click", () => {
                this.updateItemUsesOrCharges(tag, id, 1, uses, charges, max_charges, location);
              });

              const plusMinusContainer = createElement("span", { classes: ["inventory-item-plus-minus-container"] });
              plusMinusContainer.appendChild(decrementIcon);
              plusMinusContainer.appendChild(slash);
              plusMinusContainer.appendChild(incrementIcon);

              itemContainer.insertBefore(plusMinusContainer, itemContainer.lastChild);
              // itemContainer.insertBefore(decrementIcon, itemContainer.lastChild);
              // itemContainer.insertBefore(incrementIcon, itemContainer.lastChild);
            }
            break;
          case "1 Armor":
          case "2 Armor":
          case "3 Armor":
            if (bonusDefense) {
              element = document.createTextNode(`+${tag}`);
            } else {
              element = document.createTextNode(tag);
            }
            break;
          case "bonus defense":
            break;

          default:
            element = document.createTextNode(tag);
        }

        if (element) {
          appendedTags.push(element);
        }
      });

      if (appendedTags.length) {
        tagSpan.appendChild(document.createTextNode(" ("));
        appendedTags.forEach((tag, index) => {
          tagSpan.appendChild(typeof tag === "object" ? tag : document.createTextNode(tag));
          if (index !== appendedTags.length - 1) {
            tagSpan.appendChild(document.createTextNode(", "));
          }
        });
        tagSpan.appendChild(document.createTextNode(")"));
      }
    }

    nameDiv.appendChild(tagSpan);

    document.getElementById("items-container").appendChild(itemContainer);
  },

  updateItemUsesOrCharges(tag, id, increment, uses, charges, max_charges, location) {
    if (tag === "uses") {
      const newUses = uses + increment;
      if (newUses >= 0) inventory.updateItem(id, "uses", newUses);
    } else if (tag === "charges") {
      const newCharges = charges + increment;
      console.log(newCharges, max_charges);
      if (newCharges >= 0 && newCharges <= max_charges) {
        inventory.updateItem(id, "charges", newCharges);
      }
    }
    this.refreshInventory(location);
  },

  refreshInventory(container = 0) {
    let items = inventory.getItems();
    let containers = inventory.getContainers();

    document.getElementById("items-container").innerHTML = "";

    // Sort this.items so that "Carrying..." and "Fatigue" items come last
    items.sort((a, b) => {
      if (a.name === "Fatigue") return 1;
      if (b.name === "Fatigue") return -1;
      if (a.carrying !== null && b.carrying === null) return 1;
      if (a.carrying === null && b.carrying !== null) return -1;
      return 0;
    });

    let containerSlots = inventory.getSlotsCount(container);
    const containerObj = containers.find((containerObj) => containerObj.id === container);
    let containerMaxSlots = containerObj ? containerObj.slots : 10;

    // Iterate through this.items and add them to the DOM
    items.forEach((item, index) => {
      if (item.location == container) {
        //console.log("Adding item to DOM", item, index, containerSlots, containerMaxSlots);
        this.addItemToDOM({
          name: item.name,
          id: +item.id,
          tags: item.tags,
          uses: +item.uses,
          charges: +item.charges,
          max_charges: +item.max_charges,
          index: index,
          location: +item.location,
          description: item.description,
          carrying: item.carrying,
        });
      }
    });

    // Handle empty slots separately without adding them to this.items
    while (containerSlots < containerMaxSlots) {
      this.addItemToDOM({
        name: "empty slot",
        index: containerSlots, // Use containerSlots as the index for empty slots
        location: container,
      });
      containerSlots++;
    }

    // setup drag and drop
    // const draggableItems = document.querySelectorAll(".draggable-item");
    // const draggableParentContainer = document.getElementById("items-container");
    // DragAndDropModule.init(draggableItems, draggableParentContainer);

    // Update Armor Counter
    if (this.page !== "party") {
      this.updateArmor(items);
    }

    // Set the container headers
    this.setContainerHeaders(container);
  },

  showSaveFooter() {
    if (this.mode === "view") return;
    document.getElementById("save-button-footer-wrapper").classList.remove("hidden");
  },

  hideSaveFooter() {
    if (document.getElementById("save-button-footer-wrapper")) {
      document.getElementById("save-button-footer-wrapper").classList.add("hidden");
    }
  },

  showItemDescription(id) {
    let description = inventory.getItemDescription(id);
    inventoryModalUI.showItemDescriptionModal(description);
  },

  getSelectedContainer() {
    return this.selectedContainer;
  },

  editItem(id) {
    inventoryModalUI.showAddEditItemModal(inventory.getItem(id));
  },

  updateArmor() {
    let { armor, bonusDefense } = inventory.getArmorValue();

    const armorCounter = document.getElementById("armor-counter");
    // if (bonusDefense > 0) {
    //   armorCounter.textContent = "+";
    // } else {
    //   armorCounter.textContent = "";
    // }
    // armorCounter.textContent += armor;
    armorCounter.textContent = armor;
  },

  setContainerHeaders(activeContainerID) {
    this.selectedContainer = activeContainerID;
    const containerLinks = document.getElementById("inventory-header");
    containerLinks.innerHTML = "";
    const containers = inventory.getContainers();

    for (let container of containers) {
      const containerLinkText = container.name.charAt(0).toUpperCase() + container.name.slice(1);
      const slots = inventory.getSlotsCount(container.id);
      const slotsText = ` (${slots}/${container.slots})`;

      // Create the container title wrapper
      const containerTitle = createElement("div", { classes: ["inventory-container-title-container"] });

      // Create the container link
      const containerLink = createElement("a", {
        classes: [
          "inventory-container-title",
          "subtitle",
          ...(container.id === activeContainerID ? ["inventory-container-title-selected"] : []),
          ...(slots >= container.slots ? ["red-text"] : []),
        ],
        html: `${containerLinkText} ${slotsText}`,
        events: {
          click: () => {
            this.setActiveContainer(container.id);
          },
        },
      });

      // Append the container link to the container title
      containerTitle.appendChild(containerLink);

      // Conditionally add the edit icon only if in "edit" mode and container id is not 0
      if (this.mode === "edit" && container.id !== 0) {
        const editIcon = createElement("p", {
          classes: ["inventory-container-edit-button"],
          content: "edit",
          events: {
            click: () => {
              inventoryModalUI.showContainerModal(container);
            },
          },
        });
        containerTitle.appendChild(editIcon);
      }
      containerLinks.appendChild(containerTitle);
    }
  },

  setActiveContainer(activeContainer = 0) {
    this.setContainerHeaders(activeContainer);
    this.refreshInventory(activeContainer);
    //this.selectedContainer = activeContainer;
  },

  getPrintableInventory() {
    const items = inventory.getItems();
    const containers = inventory.getContainers();
    // Sort the containers array to ensure the container with ID 0 is always first
    const sortedContainers = containers.sort((a, b) => {
      if (a.id === 0) return -1;
      if (b.id === 0) return 1;
      return 0;
    });

    const printableElements = sortedContainers.map((container) => {
      const containerPanel = document.createElement("div");
      containerPanel.classList.add("inventory-container");
      containerPanel.classList.add("print-container");
      const panelHeading = document.createElement("div");
      panelHeading.classList.add("inventory-container-title-selected");
      panelHeading.classList.add("subtitle");

      panelHeading.textContent =
        container.name + " " + "(" + inventory.getSlotsCount(container.id) + "/" + container.slots + ")";
      containerPanel.appendChild(panelHeading);

      // console.log(container);

      let slotsCount = 0;

      const containerItems = items.filter((item) => item.location === container.id);
      containerItems.forEach((item) => {
        const itemElement = document.createElement("span");
        itemElement.classList.add("inventory-item-container");

        if (item.tags && item.tags.length > 0) {
          const appendTags = item.tags.map((tag) => {
            switch (tag) {
              case "bulky":
              case "petty":
                return createElement("i", { content: tag });
              case "uses":
              case "charges":
                const tagName =
                  tag === "uses"
                    ? item.uses === 1
                      ? "1 use"
                      : `${item.uses} uses`
                    : `${item.charges}/${item.max_charges} charges`;
                return document.createTextNode(tagName);
              default:
                return document.createTextNode(tag);
            }
          });
          if (item.tags.includes("bulky")) {
            slotsCount += 2;
          } else if (!item.tags.includes("petty")) {
            slotsCount++;
          }

          itemElement.textContent = `${item.name} (`;
          appendTags.forEach((tag, index) => {
            itemElement.appendChild(typeof tag === "object" ? tag : document.createTextNode(tag));
            if (index !== appendTags.length - 1) {
              itemElement.appendChild(document.createTextNode(", "));
            }
          });
          itemElement.textContent += ")";
        } else {
          itemElement.textContent = item.name;
          slotsCount++;
        }

        containerPanel.appendChild(itemElement);
      });

      console.log(slotsCount, container.slots);
      // Add empty slots
      while (slotsCount < container.slots) {
        const emptySlot = document.createElement("span");
        emptySlot.classList.add("inventory-item-container");
        emptySlot.textContent = " ";
        containerPanel.appendChild(emptySlot);
        slotsCount++;
      }

      const footer = document.createElement("div");
      footer.classList.add("panel-block", "inventory-footer");
      containerPanel.appendChild(footer);
      return containerPanel;
    });

    return printableElements;
  },

  setShowDice(showDice) {
    this.showDice = showDice;
    this.refreshInventory();
  },

  setRollDiceCallback(callback) {
    this.rollDiceCallback = callback;
  },
};
export default inventoryUI;

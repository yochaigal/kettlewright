import utils from "./utils.js";

const inventoryModule = {
  initialized: false,
  items: [],
  containers: [],
  page: "edit_character",
  selectedContainer: 0,
  armor: 0,
  mode: "view",
  selectedItemIndex: null,
  selectedItemID: null,
  selectedItem: null,
  selectedEditContainerID: null,

  initialize(items = [], containers = [{ name: "main", slots: 10, id: 0 }]) {
    if (this.initialized) {
      return;
    }
    this.initialized = true;
    this.items = items;
    this.containers = containers;

    if (this.page === "edit_character" || this.page === "party") {
      document.getElementById("add-item-button").onclick = () => {
        this.showAddItem();
      };
      document.getElementById("add-container-button").onclick = () => {
        this.showAddContainer();
      };
      document.getElementById("add-fatigue-button").onclick = () => {
        this.addItem({ name: "Fatigue", location: 0 });
      };

      this.initializeAddItemModal();
      this.initializeAddContainerModal();
      this.initializeEditContainerModal();
      this.initializeItemDescriptionModal();
    } else {
      this.initializeItemDescriptionModal();
      const inventoryFooter = document.getElementById("inventory-footer-buttons");
      if (inventoryFooter) {
        inventoryFooter.remove();
      }
    }
    this.convertLegacyData();
    this.setActiveContainer();
  },

  convertLegacyData() {},

  setPage(page) {
    this.page = page;
  },

  setMode(mode) {
    this.mode = mode;
    this.setActiveContainer(this.selectedContainer);

    if (mode === "edit") {
      document.getElementById("add-item-button").classList.remove("hidden");
      document.getElementById("add-container-button").classList.remove("hidden");
      if (this.page !== "party") {
        document.getElementById("add-fatigue-button").classList.remove("hidden");
      }
    }
  },

  // ____________________ Items ____________________

  getSlotsCount(containerID) {
    let slots = 0;
    this.items.forEach((item) => {
      if (item.location === containerID) {
        if (item.tags.includes("bulky")) {
          slots += 2;
        } else if (!item.tags.includes("petty")) {
          slots++;
        }
      }
    });
    return slots;
  },

  resetInventory() {
    this.items = [];
    this.containers = [{ name: "main", slots: 10, id: 0 }];
    this.setActiveContainer();
  },

  getItems() {
    // Called when the form is submitted
    // Sanitize data before saved in JSON
    this.items.forEach((item) => {
      item.name = utils.sanitizeStringForJSON(item.name);
      item.description = utils.sanitizeStringForJSON(item.description);
    });
    return this.items;
  },

  addItem(options) {
    let {
      name,
      tags = [],
      uses = null,
      charges = null,
      max_charges = null,
      location = 0,
      description = "This item has no description...",
      carrying = null,
      id = utils.getNextUniqueId(this.items),
    } = options;

    // Modify the damage multiplier tags
    const diceTags = ["d4", "d6", "d8", "d10", "d12"];
    if (tags.includes("dual damage")) {
      tags = tags.filter((tag) => tag !== "dual damage");
      let itemDiceTags = tags.filter((tag) => diceTags.includes(tag));
      if (itemDiceTags.length === 2) {
        // Combine the two dice tags
        tags = tags.filter((tag) => !diceTags.includes(tag)); // Remove individual dice tags
        tags.push(`${itemDiceTags[0]} + ${itemDiceTags[1]}`);
      } else if (itemDiceTags.length === 1) {
        // Double the single dice tag
        tags = tags.filter((tag) => !diceTags.includes(tag)); // Remove the dice tag
        tags.push(`${itemDiceTags[0]} + ${itemDiceTags[0]}`);
      }
    }

    // Add the item to the inventory
    this.items.push({
      name,
      tags,
      uses: +uses,
      charges: +charges,
      max_charges: +max_charges,
      location: location,
      description,
      carrying,
      id,
    });

    this.setActiveContainer(location);
  },

  updateItem(item, options) {
    // find the item based on its id property. If it exists, update it with only the used options
    const index = this.items.findIndex((i) => i.id === item.id);
    if (index !== -1) {
      this.items[index] = { ...this.items[index], ...options };
    }
  },

  refreshInventory(container) {
    // Clear items from DOM
    document.getElementById("items-container").innerHTML = "";

    // Sort this.items so that "Fatigue" items come last
    this.items.sort((a, b) => {
      if (a.name === "Fatigue") return 1;
      if (b.name === "Fatigue") return -1;

      // Sort items with 'carrying' not set to null after all others, except "Fatigue"
      if (a.carrying !== null && b.carrying === null) return 1;
      if (a.carrying === null && b.carrying !== null) return -1;
      return 0;
    });

    let containerSlots = this.getSlotsCount(container);
    const containerObj = this.containers.find((containerObj) => containerObj.id === container);
    let containerMaxSlots = containerObj ? containerObj.slots : 10;

    // Iterate through this.items and add them to the DOM
    this.items.forEach((item, index) => {
      if (item.location === container) {
        this.addItemToDOM({
          name: item.name,
          tags: item.tags,
          uses: item.uses,
          charges: item.charges,
          max_charges: item.max_charges,
          index: index,
          location: item.location,
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

    if (this.page !== "party") this.updateArmor();
  },

  showDescriptionModal(description) {
    document.getElementById("item-description-modal").classList.add("is-active");
    document.getElementById("item-description-modal-content").textContent = description;
  },

  addItemToDOM({ name, tags, uses, charges, max_charges, index, location = 0, description = "", carrying = null }) {
    // Create the item container
    const itemContainer = document.createElement("a");
    itemContainer.classList.add("panel-block");

    // Create an empty name span
    const nameDiv = document.createElement("span");
    itemContainer.appendChild(nameDiv);

    // Create the item and edit icon
    if (name !== "Fatigue" && name !== "empty slot" && carrying == null) {
      if (this.mode === "edit") {
        const usesButtonContainer = document.createElement("div");
        itemContainer.appendChild(usesButtonContainer);

        const editIcon = document.createElement("i");
        editIcon.classList.add("fa-solid", "fa-pen-to-square", "item-edit-icon");
        editIcon.onclick = () => {
          this.editItem(index);
        };

        itemContainer.appendChild(editIcon);
      } else if (description !== "" && description !== "This item has no description...") {
        const infoIcon = document.createElement("i");
        infoIcon.classList.add("fa-solid", "fa-info-circle", "item-info-icon");
        infoIcon.onclick = () => {
          this.showDescriptionModal(description);
        };
        itemContainer.appendChild(infoIcon);
      }
      nameDiv.innerHTML = name;
      nameDiv.id = "item-name-" + index; // Unique ID for each item
      nameDiv.classList.add("item-name");
    }
    // Create the fatigue item and trash icon
    else if (name === "Fatigue") {
      if (this.mode === "edit") {
        const deleteIcon = document.createElement("i");
        deleteIcon.classList.add("fa-solid", "fa-trash", "item-delete-icon");
        deleteIcon.onclick = () => {
          this.deleteItem(index);
        };
        itemContainer.appendChild(deleteIcon);
      }
      nameDiv.innerHTML = "Fatigue";
      nameDiv.classList.add("fatigue-text");
    }
    // Create carrying container item
    else if (carrying !== null) {
      nameDiv.innerHTML = name;
      nameDiv.classList.add("carrying-text");
    }

    // Create span for tags
    const tagSpan = document.createElement("span");
    tagSpan.classList.add("item-tags");
    const appendedTags = [];

    if (tags) {
      tags.forEach((tag) => {
        if (tag === "bulky" || tag === "petty") {
          const italicTag = document.createElement("i");
          italicTag.textContent = tag;
          appendedTags.push(italicTag);
        } else if (tag === "uses" || tag == "charges") {
          let tagName = "";
          if (tag == "uses") {
            tagName = uses == 1 ? "1 use" : uses + " " + tag;
          } else if (tag === "charges") {
            tagName = charges + "/" + max_charges + " charges";
          }
          appendedTags.push(tagName);
          if (this.mode == "edit") {
            const decrementIcon = document.createElement("i");
            decrementIcon.classList.add("fa-solid", "fa-minus-circle", "item-uses-icon", "item-uses-decrement-icon");
            decrementIcon.onclick = () => {
              if (tag == "uses" && uses > 0) {
                this.items[index].uses--;
              } else if (tag == "charges" && charges > 0) {
                this.items[index].charges--;
              }

              this.refreshInventory(location);
            };

            const incrementIcon = document.createElement("i");
            incrementIcon.classList.add("fa-solid", "fa-plus-circle", "item-uses-icon");
            incrementIcon.onclick = () => {
              if (tag === "uses") {
                this.items[index].uses++;
              } else if (tag === "charges" && charges < max_charges) {
                this.items[index].charges++;
              }

              this.refreshInventory(location);
            };

            // Identify the reference node (the last child of itemContainer)
            const referenceNode = itemContainer.lastChild;

            // Insert the decrementIcon and incrementIcon before the referenceNode
            itemContainer.insertBefore(decrementIcon, referenceNode);
            itemContainer.insertBefore(incrementIcon, referenceNode);
          }
        } else if (tag === "bonus defense") {
        } else if (tag === "1 Armor" || tag === "2 Armor" || tag === "3 Armor") {
          if (tags.includes("bonus defense")) {
            let tagName = "+" + tag;
            appendedTags.push(tagName);
          } else {
            appendedTags.push(tag);
          }
        } else {
          appendedTags.push(tag);
        }
      });

      // If there are tags, append the opening parenthesis
      if (appendedTags.length) {
        tagSpan.appendChild(document.createTextNode(" ("));
      }

      appendedTags.forEach((tag, index) => {
        if (typeof tag === "string") {
          tagSpan.appendChild(document.createTextNode(tag));
        } else {
          // if it's an element (like the italic tag)
          tagSpan.appendChild(tag.cloneNode(true)); // cloneNode is used to ensure the original tag is not modified
        }
        if (index !== appendedTags.length - 1) {
          tagSpan.appendChild(document.createTextNode(", "));
        }
      });

      // If there are tags, append the closing parenthesis
      if (appendedTags.length) {
        tagSpan.appendChild(document.createTextNode(")"));
      }
    }
    nameDiv.appendChild(tagSpan);

    // Add the item to the DOM
    document.getElementById("items-container").appendChild(itemContainer);
  },

  updateArmor() {
    let armor = 0;
    let bonusDefense = 0;

    this.items.forEach((item) => {
      if (item.tags.includes("1 Armor")) {
        armor++;
      } else if (item.tags.includes("2 Armor")) {
        armor += 2;
      } else if (item.tags.includes("3 Armor")) {
        armor += 3;
      }

      if (item.tags.includes("bonus defense")) {
        bonusDefense++;
      }
    });

    const armorCounter = document.getElementById("armor-counter");
    if (bonusDefense > 0) {
      armorCounter.textContent = "+";
    } else {
      armorCounter.textContent = "";
    }
    armorCounter.textContent += armor;
  },

  // ____________________ Containers ____________________

  setActiveContainer(activeContainer = 0) {
    this.setContainerHeaders(activeContainer);
    this.refreshInventory(activeContainer);
    this.selectedContainer = activeContainer;
  },

  getContainers() {
    return this.containers;
  },

  setContainers(containers) {
    this.containers = containers;
  },

  isContainer(name) {
    return this.containers.some((container) => container.name.toLowerCase() === name.toLowerCase());
  },

  getContainerID(name) {
    return this.containers.find((container) => container.name.toLowerCase() === name.toLowerCase())?.id ?? null;
  },

  convertCarriedByToID() {
    // this function is used durring character creation
    // it allows the  background json files to store the name of the container that is carrying the item
    // rather than the id of the container

    this.containers.forEach((container) => {
      if (typeof container.carriedBy === "string") {
        this.getContainerID(container.carriedBy);
        let carriedBy = this.getContainerID(container.carriedBy);
        if (typeof carriedBy === "number") {
          container.carriedBy = carriedBy;
        }
        if (container.load > 0 && typeof container.carriedBy === "number") {
          for (let i = 0; i < container.load; i++) {
            this.addItem({
              name: `Carrying ${container.name}`,
              location: carriedBy,
              carrying: container.id,
            });
          }
        }
      }
    });
  },

  updateContainer(id) {
    const container = this.containers.find((container) => container.id === id);
    const containerNameField = document.getElementById("edit-container-modal-name-field");
    const containerSlotsField = document.getElementById("edit-container-modal-slots-field");
    const carriedByField = document.getElementById("edit-container-modal-carried-select");
    const loadField = document.getElementById("edit-container-modal-load-field");

    container.name = containerNameField.value;
    container.slots = containerSlotsField.value;
    container.load = loadField.value;
    container.carriedBy = carriedByField.value;

    // Clear any items that are carrying this container
    this.items = this.items.filter((item) => item.carrying !== id);

    // Add carrying items
    if (container.carriedBy !== null && container.carriedBy !== undefined && container.carriedBy !== "not carried") {
      if (container.load > 0) {
        for (let i = 0; i < container.load; i++) {
          this.addItem({
            name: `Carrying ${container.name}`,
            location: Number(container.carriedBy),
            carrying: id,
          });
        }
      }
    } else {
      this.setActiveContainer(this.selectedContainer);
    }
  },

  addContainer(name, slots, carriedBy = "not carried", load = 0) {
    let id = utils.getNextUniqueId(this.containers);

    this.containers.push({ name, slots, id, load, carriedBy });
    this.setActiveContainer(id);

    load = load > 8 ? 8 : load;

    if (typeof carriedBy === "number") {
      if (load > 0) {
        for (let i = 0; i < load; i++) {
          this.addItem({
            name: `Carrying ${name}`,
            location: carriedBy,
            carrying: id,
          });
        }
      }
    }

    this.setActiveContainer(id);
  },

  setContainerHeaders(activeContainerID) {
    const containerLinks = document.getElementById("inventory-header");
    containerLinks.innerHTML = "";

    for (let container of this.containers) {
      const containerTitle = document.createElement("div");
      containerTitle.classList.add("container-title-container");

      const containerLink = document.createElement("a");
      containerLink.classList.add("container-title");
      let containerLinkText = container.name.charAt(0).toUpperCase() + container.name.slice(1);

      if (container.id === activeContainerID) {
        containerLink.classList.add("is-active");
      }

      // Add the slots
      let slots = this.getSlotsCount(container.id);
      let slotsText = ` (${slots}/${container.slots})`;

      if (this.page == "party" && container.id === 0) {
        containerLink.innerHTML = `${containerLinkText} ${slotsText}`;
      } else {
        containerLink.innerHTML = `${containerLinkText} ${slotsText}`;

        if (slots > container.slots) {
          containerLink.classList.add("red-text");
        } else {
          containerLink.classList.remove("red-text");
        }
      }
      containerTitle.appendChild(containerLink);

      // Add edit button
      if (this.mode === "edit" && container.id !== 0) {
        const editIcon = document.createElement("i");
        editIcon.classList.add("fa-solid", "fa-pen-to-square", "container-edit-icon");

        editIcon.onclick = () => {
          this.setEditContainerModal(container.id);
        };
        containerTitle.appendChild(editIcon);
      }
      containerLink.onclick = () => {
        console.log("clicked", container.id);
        this.setActiveContainer(container.id);
      };
      containerLinks.appendChild(containerTitle);
    }
  },

  // ____________________ Modals ____________________

  toggleUses() {
    if (document.getElementById("tag-button-uses").classList.contains("selected")) {
      document.getElementById("add-item-modal-uses-container").classList.remove("inactive");
    } else {
      document.getElementById("add-item-modal-uses-container").classList.add("inactive");
    }

    if (document.getElementById("tag-button-charges").classList.contains("selected")) {
      document.getElementById("add-item-modal-charges-container").classList.remove("inactive");
    } else {
      document.getElementById("add-item-modal-charges-container").classList.add("inactive");
    }
  },

  initializeTagButtons() {
    const tagButtons = document.querySelectorAll(".tag");
    const armorTags = ["1 Armor", "2 Armor", "3 Armor"];
    const weightTags = ["petty", "bulky"];
    const damageTags = ["d4", "d6", "d8", "d10", "d12"];
    const dualDamageTags = ["d4 + d4", "d6 + d6", "d8 + d8", "d10 + d10", "d12 + d12"];
    const usesTags = ["uses", "charges"];

    tagButtons.forEach((tag) => {
      tag.addEventListener("click", () => {
        const tagText = tag.textContent.trim();

        if (weightTags.includes(tagText)) {
          handleExclusiveSelection(weightTags, tag);
        } else if (usesTags.includes(tagText)) {
          handleExclusiveSelection(usesTags, tag);

          this.toggleUses();
        } else if (armorTags.includes(tagText)) {
          handleExclusiveSelection(armorTags, tag);
        } else if (damageTags.includes(tagText)) {
          handleDamageTags(tag);
        } else if (dualDamageTags.includes(tagText)) {
          handleDamageTags(tag);
        } else {
          tag.classList.toggle("selected");
        }
      });
    });

    function handleExclusiveSelection(tagsArray, currentTag) {
      if (currentTag.classList.contains("selected")) {
        currentTag.classList.remove("selected");
      } else {
        tagButtons.forEach((tag) => {
          if (tagsArray.includes(tag.textContent.trim()) && tag !== currentTag) {
            tag.classList.remove("selected");
          }
        });
        currentTag.classList.add("selected");
      }
    }

    function handleDamageTags(currentTag) {
      // if the current tag is part of dualDamageTags
      if (dualDamageTags.includes(currentTag.textContent.trim())) {
        // deselect it and revert to signle damage tag
        currentTag.classList.remove("selected");
        currentTag.textContent = currentTag.textContent.split(" + ")[0];
      }
      // if the current tag is part of single damageTags
      else if (damageTags.includes(currentTag.textContent.trim())) {
        // if it is already selected
        if (currentTag.classList.contains("selected")) {
          // Move to modified state and deselect other damage tags
          currentTag.textContent = currentTag.textContent + " + " + currentTag.textContent;
          tagButtons.forEach((tag) => {
            if (damageTags.includes(tag.textContent.trim()) && tag !== currentTag) {
              tag.classList.remove("selected");
            }
          });
          tagButtons.forEach((tag) => {
            if (dualDamageTags.includes(tag.textContent.trim())) {
              tag.classList.remove("selected");
            }
          });
          currentTag.classList.add("selected");
        }
        // if it is not already selected
        else {
          // if there are any dual damage tags selected, convert them to single damage tags and deselect them
          tagButtons.forEach((tag) => {
            if (dualDamageTags.includes(tag.textContent.trim())) {
              tag.textContent = tag.textContent.split(" + ")[0];
              tag.classList.remove("selected");
            }
          });
          // if there are already 2 damage tags selected, deselect them
          let selectedDamageTags = Array.from(tagButtons).filter(
            (tag) => damageTags.includes(tag.textContent.trim()) && tag.classList.contains("selected")
          );
          if (selectedDamageTags.length >= 2) {
            selectedDamageTags.forEach((tag) => tag.classList.remove("selected"));
          }

          // select the damage tag
          currentTag.classList.add("selected");
        }
      }
    }
  },

  initializeAddItemModal() {
    const addItemModal = document.getElementById("add-item-modal");
    const itemNameField = document.getElementById("add-item-modal-name-field");
    const usesField = document.getElementById("add-item-modal-uses-field");
    const chargesField = document.getElementById("add-item-modal-charges-field");
    const maxChargesField = document.getElementById("add-item-modal-max-charges-field");
    const containerSelect = document.getElementById("add-item-modal-container-select");

    // Manage Tags
    let tags = [];
    const tagButtons = document.querySelectorAll(".tag");

    function updateTags() {
      tags = Array.from(tagButtons)
        .filter((button) => button.classList.contains("selected"))
        .map((button) => button.textContent.trim().replace(/[\r\n]/g, ""));
      // the regex here is to remove any newline characters that may be added by the prettier or other formatting extensions
    }

    this.initializeTagButtons();
    this.toggleUses();

    // Manage Container Selection
    this.containers.forEach((container) => {
      containerSelect.appendChild(utils.createOption(container.name, container.id));
    });

    // Manage Save / Cancel
    function clearValues() {
      itemNameField.value = "";
      tagButtons.forEach((button) => {
        button.classList.remove("selected");
      });
      usesField.value = 0;
      tags = [];
      containerSelect.value = 0;
    }

    document.getElementById("add-item-modal-save").addEventListener("click", () => {
      if (itemNameField.value.trim().length == 0) {
        document.getElementById("add-item-modal-name-field").focus();
        document.getElementById("add-item-modal-name-field").classList.add("is-danger");
        return;
      }
      updateTags();

      this.addItem({
        name: itemNameField.value,
        tags: tags,
        uses: usesField.value,
        charges: chargesField.value,
        max_charges: maxChargesField.value,
        location: Number(containerSelect.value),
        description: document.getElementById("add-item-modal-description-field").value,
      });
      addItemModal.classList.remove("is-active");
      clearValues();
      this.showSaveFooter();
      this.removeModalWarnings();
    });

    document.getElementById("add-item-modal-save-edits").addEventListener("click", () => {
      updateTags();
      this.items[this.selectedItemIndex].name = itemNameField.value;
      this.items[this.selectedItemIndex].tags = tags;
      this.items[this.selectedItemIndex].uses = usesField.value;
      this.items[this.selectedItemIndex].charges = chargesField.value;
      this.items[this.selectedItemIndex].max_charges = maxChargesField.value;
      this.items[this.selectedItemIndex].location = Number(containerSelect.value);
      this.items[this.selectedItemIndex].description = document.getElementById(
        "add-item-modal-description-field"
      ).value;
      addItemModal.classList.remove("is-active");
      clearValues();
      this.setActiveContainer(this.items[this.selectedItemIndex].location);
      this.showSaveFooter();
      this.removeModalWarnings();
    });

    document.getElementById("add-item-modal-close").addEventListener("click", () => {
      addItemModal.classList.remove("is-active");
      clearValues();
      this.showSaveFooter();
    });

    document.getElementById("add-item-modal-cancel").addEventListener("click", () => {
      addItemModal.classList.remove("is-active");
      clearValues();
      this.showSaveFooter();
      this.removeModalWarnings();
    });

    document.getElementById("add-item-modal-delete").onclick = () => {
      this.deleteItem(this.selectedItemIndex);
      addItemModal.classList.remove("is-active");
      clearValues();
      this.showSaveFooter();
      this.removeModalWarnings();
    };
  },

  initializeAddContainerModal() {
    // Add Container Modal Events

    const addContainerModal = document.getElementById("add-container-modal");
    const addContainerNameField = document.getElementById("container-modal-name-field");
    const addContainerSlotsField = document.getElementById("container-modal-slots-field");
    const carriedByField = document.getElementById("add-container-modal-carried-select");
    const loadField = document.getElementById("container-modal-load-field");

    carriedByField.addEventListener("change", () => {
      if (carriedByField.value == "not carried") {
        loadField.disabled = true;
      } else {
        loadField.disabled = false;
      }
    });

    document.getElementById("add-container-modal-close").addEventListener("click", () => {
      addContainerModal.classList.remove("is-active");
      this.showSaveFooter();
      this.removeModalWarnings();
    });
    document.getElementById("add-container-modal-cancel").addEventListener("click", () => {
      addContainerModal.classList.remove("is-active");
      this.showSaveFooter();
      this.removeModalWarnings();
    });
    document.getElementById("add-container-modal-add").addEventListener("click", () => {
      let containerName = addContainerNameField.value;
      let containerSlots = addContainerSlotsField.value;
      let carriedBy = carriedByField.value == "not carried" ? "not carried" : Number(carriedByField.value);

      let load = loadField.value;
      //check to make sure the user inputed a value for both the container name and slots)
      if (containerName.trim().length == 0 || inventory.getContainerID(containerName)) {
        addContainerNameField.focus();
        addContainerNameField.classList.add("is-danger");
        return;
      }
      if (containerSlots.length == 0 || containerSlots <= 0) {
        addContainerSlotsField.focus();
        addContainerSlotsField.classList.add("is-danger");
        return;
      }
      if (containerName !== "" && containerSlots > 0) {
        this.addContainer(containerName, containerSlots, carriedBy, load);
        this.updateAddItemContainerSelection();
      }
      addContainerModal.classList.remove("is-active");
      this.showSaveFooter();
      this.removeModalWarnings();
      this.setActiveContainer(this.getContainerID(containerName));
    });
  },

  initializeEditContainerModal() {
    const editContainerModal = document.getElementById("edit-container-modal");
    const carriedSelectField = document.getElementById("edit-container-modal-carried-select");
    const deleteCheckbox = document.getElementById("edit-container-modal-delete-checkbox");
    const removeButton = document.getElementById("edit-container-modal-remove");
    const saveButton = document.getElementById("edit-container-modal-update");

    carriedSelectField.onchange = () => {
      if (carriedSelectField.value == "not carried") {
        document.getElementById("edit-container-modal-load-field").disabled = true;
      } else {
        document.getElementById("edit-container-modal-load-field").disabled = false;
      }
    };

    deleteCheckbox.onchange = () => {
      if (deleteCheckbox.checked) {
        document.getElementById("edit-container-modal-move-items-destination").disabled = false;
        removeButton.disabled = false;
        saveButton.disabled = true;
        // updateSection.classList.add("inactive");
      } else {
        document.getElementById("edit-container-modal-move-items-destination").disabled = true;
        removeButton.disabled = true;

        saveButton.disabled = false;
        // updateSection.classList.remove("inactive");
      }
    };

    document.getElementById("edit-container-modal-close").addEventListener("click", () => {
      editContainerModal.classList.remove("is-active");
      this.showSaveFooter();
      this.removeModalWarnings();
    });

    document.getElementById("edit-container-modal-cancel").addEventListener("click", () => {
      editContainerModal.classList.remove("is-active");
      this.showSaveFooter();
      this.removeModalWarnings();
    });

    saveButton.onclick = () => {
      console.log("save container ", this.selectedEditContainerID);
      this.updateContainer(this.selectedEditContainerID);

      this.setActiveContainer(this.selectedEditContainerID);
      this.showSaveFooter();
      editContainerModal.classList.remove("is-active");
    };
    removeButton.onclick = () => {
      const containerDestinationID = document.getElementById("edit-container-modal-move-items-destination").value;

      if (containerDestinationID == "delete") {
        console.log("delete container ", containerDestinationID);
        this.deleteAllContainerItems(this.selectedEditContainerID);
        this.deleteContainer(this.selectedEditContainerID);
        this.showSaveFooter();

        editContainerModal.classList.remove("is-active");
      } else {
        this.moveAllContainerItems(this.selectedEditContainerID, Number(containerDestinationID));
        this.deleteContainer(this.selectedEditContainerID);
        this.showSaveFooter();

        editContainerModal.classList.remove("is-active");
      }
    };
  },

  setEditContainerModal(id) {
    // Function runs when the user clicks the edit button on a container

    this.selectedEditContainerID = id;
    this.hideSaveFooter();

    const container = this.containers.find((container) => container.id === id);

    const editContainerModal = document.getElementById("edit-container-modal");
    editContainerModal.classList.add("is-active");
    const containerNameField = document.getElementById("edit-container-modal-name-field");
    const containerSlotsField = document.getElementById("edit-container-modal-slots-field");
    const carriedByField = document.getElementById("edit-container-modal-carried-select");
    const loadField = document.getElementById("edit-container-modal-load-field");
    const removeContainerSelect = document.getElementById("edit-container-modal-move-items-destination");
    const deleteCheckbox = document.getElementById("edit-container-modal-delete-checkbox");
    const itemDestination = document.getElementById("edit-container-modal-move-items-destination");

    containerNameField.value = container.name;
    containerSlotsField.value = container.slots;
    loadField.value = container.load;
    carriedByField.innerHTML = "";
    carriedByField.appendChild(utils.createOption("not carried", "not carried"));
    this.containers.forEach((c) => {
      if (c.name !== container.name) {
        carriedByField.appendChild(utils.createOption(c.name, c.id));
      }
    });
    carriedByField.value = container.carriedBy;
    deleteCheckbox.checked = false;
    itemDestination.disabled = true;

    if (container.carriedBy == "not carried") {
      loadField.disabled = true;
    }

    removeContainerSelect.innerHTML = "";
    this.containers.forEach((c) => {
      if (c.id !== id) {
        removeContainerSelect.appendChild(utils.createOption(c.name, c.id));
      }
    });
    removeContainerSelect.appendChild(utils.createOption("** Delete Items **", "delete"));
  },

  initializeItemDescriptionModal() {
    const itemDescriptionModal = document.getElementById("item-description-modal");
    document.getElementById("item-description-modal-close").addEventListener("click", () => {
      itemDescriptionModal.classList.remove("is-active");
    });
  },

  showSaveFooter() {
    document.getElementById("save-button-footer-wrapper").classList.remove("hidden");
    this.removeModalWarnings();
  },

  hideSaveFooter() {
    document.getElementById("save-button-footer-wrapper").classList.add("hidden");
  },

  removeModalWarnings() {
    //check the modals for children with the is-danger class and remove it
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.querySelectorAll(".is-danger").forEach((element) => {
        if (element.tagName !== "BUTTON") {
          element.classList.remove("is-danger");
        }
      });
    });
  },

  updateAddItemContainerSelection() {
    const containerSelect = document.getElementById("add-item-modal-container-select");
    containerSelect.innerHTML = "";
    this.containers.forEach((container) => {
      containerSelect.appendChild(utils.createOption(container.name, container.id));
    });
  },

  editItem(index) {
    console.log("edit item ", index, this.items[index], this.items);
    //get item id based on index
    let item = this.items[index];
    this.showAddItem("edit", item);
  },

  deleteItem(index) {
    this.items.splice(index, 1);
    this.setActiveContainer(this.selectedContainer);
  },

  deleteAllItems(container) {
    this.items = this.items.filter((item) => item.location !== container);
    this.setActiveContainer();
  },

  deleteContainer(id) {
    this.containers = this.containers.filter((container) => container.id !== id);
    this.setActiveContainer(0);
  },

  moveAllContainerItems(fromContainer, toContainer) {
    // Clear any items that are carrying this container
    this.items = this.items.filter((item) => item.carrying !== fromContainer);

    // Move all items from one container to another
    this.items.forEach((item) => {
      if (item.location === fromContainer) {
        item.location = toContainer;
      }
    });
  },

  deleteAllContainerItems(containerID) {
    // Clear any items that are carrying this container and any items in this container
    this.items = this.items.filter((item) => item.carrying !== containerID);
    this.items = this.items.filter((item) => item.location !== containerID);
  },

  showAddItem(mode = "add", item = null, index = null) {
    this.hideSaveFooter();

    document.getElementById("add-item-modal").classList.add("is-active");
    document.getElementById("add-item-modal-container-select").value = this.selectedContainer;

    if (mode == "edit" && item !== null) {
      document.getElementById("add-item-modal-save").classList.add("hidden");
      document.getElementById("add-item-modal-save-edits").classList.remove("hidden");
      document.getElementById("add-item-modal-title").textContent = "Edit Item";
      document.getElementById("add-item-modal-delete").classList.remove("hidden");

      this.selectedItemIndex = index;
      this.selectedItemID = item.id;

      // Populate the fields with the item's data
      document.getElementById("add-item-modal-name-field").value = item.name;
      document.getElementById("add-item-modal-uses-field").value = item.uses;
      document.getElementById("add-item-modal-charges-field").value = item.charges;
      document.getElementById("add-item-modal-max-charges-field").value = item.max_charges;
      document.getElementById("add-item-modal-description-field").value = item.description;

      // Select the tags
      const tagButtons = document.querySelectorAll(".tag");
      tagButtons.forEach((button) => {
        if (item.tags.includes(button.textContent.trim())) {
          button.classList.add("selected");
        }
        if (item.tags.includes("d4 + d4")) {
          document.getElementById("tag-button-d4").classList.add("selected");
          document.getElementById("tag-button-d4").textContent = "d4 + d4";
        } else if (item.tags.includes("d6 + d6")) {
          document.getElementById("tag-button-d6").classList.add("selected");
          document.getElementById("tag-button-d6").textContent = "d6 + d6";
        } else if (item.tags.includes("d8 + d8")) {
          document.getElementById("tag-button-d8").classList.add("selected");
          document.getElementById("tag-button-d8").textContent = "d8 + d8";
        } else if (item.tags.includes("d10 + d10")) {
          document.getElementById("tag-button-d10").classList.add("selected");
          document.getElementById("tag-button-d10").textContent = "d10 + d10";
        } else if (item.tags.includes("d12 + d12")) {
          document.getElementById("tag-button-d12").classList.add("selected");
          document.getElementById("tag-button-d12").textContent = "d12 + d12";
        }
      });
      this.toggleUses();

      // Select the container
      document.getElementById("add-item-modal-container-select").value = item.location;
    } else {
      document.getElementById("add-item-modal-save").classList.remove("hidden");
      document.getElementById("add-item-modal-save-edits").classList.add("hidden");
      document.getElementById("add-item-modal-title").textContent = "Add Item";
      document.getElementById("add-item-modal-delete").classList.add("hidden");
    }
  },

  showAddContainer() {
    this.hideSaveFooter();
    document.getElementById("add-container-modal").classList.add("is-active");
    document.getElementById("container-modal-name-field").value = "";
    document.getElementById("container-modal-slots-field").value = "";
    document.getElementById("container-modal-load-field").value = "";

    const carriedBySelect = document.getElementById("add-container-modal-carried-select");
    carriedBySelect.innerHTML = "";
    let carriedByPlaceholder = utils.createOption("not carried", "not carried");
    carriedBySelect.appendChild(carriedByPlaceholder);

    this.containers.forEach((container) => {
      carriedBySelect.appendChild(utils.createOption(container.name, container.id));
    });
    carriedBySelect.value = "not carried";
  },
};

export default inventoryModule;

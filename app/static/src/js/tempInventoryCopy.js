const inventoryModule = {
  initialized: false,
  items: [],
  containers: [],
  page: "edit",
  selectedContainer: 0,
  armor: 0,
  mode: "view",
  selectedItemIndex: null,
  selectedEditContainerID: null,
  tagButtons: {
    damage: [
      {
        name: "d4",
        id: "tag-button-d4",
        state: 0,
      },
      {
        name: "d4",
        id: "tag-button-d4",
        state: 0,
      },
      {
        name: "d8",
        id: "tag-button-d4",
        state: 0,
      },
      {
        name: "d10",
        id: "tag-button-d4",
        state: 0,
      },
      {
        name: "d12",
        id: "tag-button-d4",
        state: 0,
      },
    ],
  },

  initialize(items = [], containers = [{ name: "main", slots: 10, id: 0 }]) {
    if (this.initialized) {
      return;
    }
    this.initialized = true;
    this.items = items;
    this.containers = containers;

    console.log(items, containers);

    // Convert the legacy containers and items to the new format
    // Remove this later
    this.convertLegacyContainersAndItems();

    if (this.page !== "view") {
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
      const inventoryFooter = document.getElementById(
        "inventory-footer-buttons"
      );
      if (inventoryFooter) {
        inventoryFooter.remove();
      }
    }
    this.setActiveContainer();
  },

  convertLegacyContainersAndItems() {
    // Convert containers to use IDs for reference rather than naem
    // Add IDs to items
    // Add ids to container if not present
    this.containers.forEach((container) => {
      if (!container.id) {
        if (container.name == "main") {
          container.id = 0;
        } else {
          container.id = this.getNextUniqueId(this.containers);
        }
      }
    });

    // Convert the items to the new format
    this.items.forEach((item) => {
      if (!item.location) {
        item.location = 0;
      } else if (item.location === "main") {
        item.location = 0;
      } else if (
        this.containers.find((container) => container.name === item.location)
      ) {
        item.location = this.containers.find(
          (container) => container.name === item.location
        ).id;
      }

      if (!item.id) {
        item.id = this.getNextUniqueId(this.items);
      }
    });
  },

  setPage(page) {
    this.page = page;
  },

  setMode(mode) {
    this.mode = mode;
    this.setActiveContainer(this.selectedContainer);

    if (mode === "edit") {
      document.getElementById("add-item-button").classList.remove("hidden");
      document
        .getElementById("add-container-button")
        .classList.remove("hidden");
      document.getElementById("add-fatigue-button").classList.remove("hidden");
    }
  },

  // ____________________ Utilites ____________________
  getNextUniqueId(arr) {
    // Filter out objects without an id property, then find the highest current id
    const highestId = arr
      .filter((item) => item.id !== undefined && Number.isInteger(item.id))
      .reduce((max, item) => (item.id > max ? item.id : max), 0);
    // Return the next id
    return highestId + 1;
  },

  sanitizeString(str) {
    // This regex matches any character that is NOT alphanumeric, hyphen, or space
    return str.replace(/[^\w\s-]/g, "");
  },

  createOption(text, value = "") {
    const option = document.createElement("option");
    option.value = value;
    option.text = text;
    return option;
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
    // used in character creation to reset on new rolls
    this.items = [];
    this.containers = [{ name: "main", slots: 10, id: 0 }];
    this.setActiveContainer();
  },

  getItems() {
    return this.items;
  },

  addItem(options) {
    let {
      name,
      tags = [],
      max_uses = null,
      location = 0,
      description = "This item has no description...",
      carrying = null,
      id = this.getNextUniqueId(this.items),
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
      max_uses,
      location: location,
      description,
      carrying,
      id,
    });

    this.setActiveContainer(location);
  },

  refreshInventory(container) {
    document.getElementById("items-container").innerHTML = "";

    // Sort this.items so that "Fatigue" items come last
    this.items.sort((a, b) => {
      if (a.name === "Fatigue") return 1;
      if (b.name === "Fatigue") return -1;
      return 0;
    });

    let containerSlots = this.getSlotsCount(container);
    const containerObj = this.containers.find(
      (containerObj) => containerObj.id === container
    );
    let containerMaxSlots = containerObj ? containerObj.slots : 0;

    // Iterate through this.items and add them to the DOM
    this.items.forEach((item, index) => {
      if (item.location === container) {
        this.addItemToDOM({
          name: item.name,
          tags: item.tags,
          max_uses: item.max_uses,
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

    this.updateArmor();
  },

  showDescriptionModal(description) {
    document
      .getElementById("item-description-modal")
      .classList.add("is-active");
    document.getElementById("item-description-modal-content").textContent =
      description;
  },

  addItemToDOM({
    name,
    tags,
    max_uses,
    index,
    location = 0,
    description = "",
    carrying = null,
  }) {
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
        editIcon.classList.add(
          "fa-solid",
          "fa-pen-to-square",
          "item-edit-icon"
        );
        editIcon.onclick = () => {
          this.editItem(index);
        };

        itemContainer.appendChild(editIcon);
      } else if (
        description !== "" &&
        description !== "This item has no description..."
      ) {
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
          if (max_uses === 1) {
            tag === "uses" ? (tagName = "1 use") : (tagName = "1 charge");
          } else {
            tagName = max_uses + " " + tag;
          }
          appendedTags.push(tagName);

          if (this.mode == "edit") {
            const decrementIcon = document.createElement("i");
            decrementIcon.classList.add(
              "fa-solid",
              "fa-minus-circle",
              "item-uses-icon",
              "item-uses-decrement-icon"
            );
            decrementIcon.onclick = () => {
              if (max_uses > 0) {
                this.items[index].max_uses--;
                this.refreshInventory(location);
              }
            };

            const incrementIcon = document.createElement("i");
            incrementIcon.classList.add(
              "fa-solid",
              "fa-plus-circle",
              "item-uses-icon"
            );
            incrementIcon.onclick = () => {
              this.items[index].max_uses++;
              this.refreshInventory(location);
            };

            // Identify the reference node (the last child of itemContainer)
            const referenceNode = itemContainer.lastChild;

            // Insert the decrementIcon and incrementIcon before the referenceNode
            itemContainer.insertBefore(decrementIcon, referenceNode);
            itemContainer.insertBefore(incrementIcon, referenceNode);
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

  isContainer(name) {
    return this.containers.some((container) => container.name === name);
  },

  getContainers() {
    return this.containers;
  },

  addContainer(name, slots, carriedBy = "not carried", load = 0) {
    let id = this.getNextUniqueId(this.containers);

    this.containers.push({ name, slots, id, load, carriedBy });
    this.setActiveContainer(id);

    load = load > 8 ? 8 : load;

    if (carriedBy != "not carried") {
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
      //containerLink.onclick = () => {};
      containerLink.classList.add("container-title");
      let containerLinkText = container.name;

      if (container.id === activeContainerID) {
        containerLink.classList.add("is-active");
      }

      // Add the slots
      let slots = this.getSlotsCount(container.id);

      // Add max slots
      let slotsText = ` (${slots}/${container.slots})`;

      containerLink.innerHTML = `${containerLinkText} ${slotsText}`;
      if (slots > container.slots) {
        containerLink.classList.add("red-text");
      } else {
        containerLink.classList.remove("red-text");
      }
      // }

      containerTitle.appendChild(containerLink);

      // Add edit button
      if (this.mode === "edit" && container.id !== 0) {
        const editIcon = document.createElement("i");
        editIcon.classList.add(
          "fa-solid",
          "fa-pen-to-square",
          "container-edit-icon"
        );

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
    if (document.getElementById("uses-button").classList.contains("selected")) {
      document
        .getElementById("add-item-modal-uses-container")
        .classList.remove("inactive");
    } else {
      document
        .getElementById("add-item-modal-uses-container")
        .classList.add("inactive");
    }
  },

  manageTagButtons() {
    const tagButtons = document.querySelectorAll(".tag");
    const armorTags = ["1 Armor", "2 Armor", "3 Armor"];
    const weightTags = ["petty", "bulky"];
    const damageTags = ["d4", "d6", "d8", "d10", "d12"];
    const dualDamageTags = [
      "d4 + d4",
      "d6 + d6",
      "d8 + d8",
      "d10 + d10",
      "d12 + d12",
    ];
    const usesTags = ["uses", "charges"];

    tagButtons.forEach((tag) => {
      tag.addEventListener("click", () => {
        const tagText = tag.textContent.trim();
        //remove any blank leading or trailing spaces

        console.log(tagText);
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
          if (
            tagsArray.includes(tag.textContent.trim()) &&
            tag !== currentTag
          ) {
            tag.classList.remove("selected");
          }
        });
        currentTag.classList.add("selected");
      }
    }

    function handleDamageTags(currentTag) {
      // if the current tag is part of dualDamageTags
      if (dualDamageTags.includes(currentTag.textContent)) {
        // deselect it and revert to signle damage tag
        currentTag.classList.remove("selected");
        currentTag.textContent = currentTag.textContent.split(" + ")[0];
      }
      // if the current tag is part of single damageTags
      else if (damageTags.includes(currentTag.textContent)) {
        // if it is already selected
        if (currentTag.classList.contains("selected")) {
          // Move to modified state and deselect other damage tags
          console.log("moving to modified");
          currentTag.textContent =
            currentTag.textContent + " + " + currentTag.textContent;
          tagButtons.forEach((tag) => {
            if (damageTags.includes(tag.textContent) && tag !== currentTag) {
              tag.classList.remove("selected");
            }
          });
          tagButtons.forEach((tag) => {
            if (dualDamageTags.includes(tag.textContent)) {
              tag.classList.remove("selected");
            }
          });
          currentTag.classList.add("selected");
        }
        // if it is not already selected
        else {
          // if there are any dual damage tags selected, convert them to single damage tags and deselect them
          tagButtons.forEach((tag) => {
            if (dualDamageTags.includes(tag.textContent)) {
              tag.textContent = tag.textContent.split(" + ")[0];
              tag.classList.remove("selected");
            }
          });
          // if there are already 2 damage tags selected, deselect them
          let selectedDamageTags = Array.from(tagButtons).filter(
            (tag) =>
              damageTags.includes(tag.textContent.trim()) &&
              tag.classList.contains("selected")
          );
          if (selectedDamageTags.length >= 2) {
            selectedDamageTags.forEach((tag) =>
              tag.classList.remove("selected")
            );
          }

          // select the damage tag
          currentTag.classList.add("selected");
        }
      }
    }
  },

  manageTagButtonState() {
    const damageTagButtons = this.tagButtons.damage;
    damageTagButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (button.state === 0) {
          button.state = 1;
          button.classList.add("selected");
          button.textContent = button.name;
          //check how many other damage buttons are selected
          let selectedDamageTags = damageTagButtons.filter(
            (tag) => tag.state === 1
          );
          if (selectedDamageTags.length >= 1) {
            // while there are more than 2 selected, deselect the first one
            selectedDamageTags[0].state = 0;
            selectedDamageTags[0].classList.remove("selected");
            selectedDamageTags[0].textContent = selectedDamageTags[0].name;
          }
        } else if (button.state === 1) {
          button.state = 2;
          button.classList.add("selected");
          button.textContent = button.name + " + " + button.name;
          damageTagButtons.forEach((tag) => {
            if (tag !== button) {
              tag.state = 0;
              tag.classList.remove("selected");
              tag.textContent = tag.name;
            }
          });
        } else {
          button.state = 0;
          button.classList.remove("selected");
          button.textContent = button.name;
        }
      });
    });
  },

  initializeAddItemModal() {
    const addItemModal = document.getElementById("add-item-modal");
    const itemNameField = document.getElementById("add-item-modal-name-field");
    const usesField = document.getElementById("add-item-modal-uses-field");
    const containerSelect = document.getElementById(
      "add-item-modal-container-select"
    );

    // Manage Tags
    let tags = [];
    const tagButtons = document.querySelectorAll(".tag");

    function updateTags() {
      tags = Array.from(tagButtons)
        .filter((button) => button.classList.contains("selected"))
        .map((button) => button.textContent.trim());
    }

    //this.manageTagButtons();

    this.manageTagButtonState();
    this.toggleUses();

    // Manage Container Selection
    this.containers.forEach((container) => {
      containerSelect.appendChild(
        this.createOption(container.name, container.id)
      );
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

    document
      .getElementById("add-item-modal-save")
      .addEventListener("click", () => {
        if (itemNameField.value.trim().length == 0) {
          document.getElementById("add-item-modal-name-field").focus();
          document
            .getElementById("add-item-modal-name-field")
            .classList.add("is-danger");
          return;
        }
        this.addItem({
          name: this.sanitizeString(itemNameField.value),
          tags: tags,
          max_uses: usesField.value,
          location: Number(containerSelect.value),
          description: document.getElementById(
            "add-item-modal-description-field"
          ).value,
        });
        addItemModal.classList.remove("is-active");
        clearValues();
        this.showSaveFooter();
        this.removeModalWarnings();
      });

    document
      .getElementById("add-item-modal-save-edits")
      .addEventListener("click", () => {
        updateTags();
        this.items[this.selectedItemIndex].name = this.sanitizeString(
          itemNameField.value
        );
        this.items[this.selectedItemIndex].tags = tags;
        this.items[this.selectedItemIndex].max_uses = usesField.value;
        this.items[this.selectedItemIndex].location = Number(
          containerSelect.value
        );
        this.items[this.selectedItemIndex].description =
          document.getElementById("add-item-modal-description-field").value;
        addItemModal.classList.remove("is-active");
        clearValues();
        this.setActiveContainer(this.items[this.selectedItemIndex].location);
        this.showSaveFooter();
        this.removeModalWarnings();
      });

    document
      .getElementById("add-item-modal-close")
      .addEventListener("click", () => {
        addItemModal.classList.remove("is-active");
        clearValues();
        this.showSaveFooter();
      });

    document
      .getElementById("add-item-modal-cancel")
      .addEventListener("click", () => {
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
    const addContainerNameField = document.getElementById(
      "container-modal-name-field"
    );
    const addContainerSlotsField = document.getElementById(
      "container-modal-slots-field"
    );
    const carriedByField = document.getElementById(
      "add-container-modal-carried-select"
    );
    const loadField = document.getElementById("container-modal-load-field");

    carriedByField.addEventListener("change", () => {
      if (carriedByField.value == "not carried") {
        loadField.disabled = true;
      } else {
        loadField.disabled = false;
      }
    });

    document
      .getElementById("add-container-modal-close")
      .addEventListener("click", () => {
        addContainerModal.classList.remove("is-active");
        this.showSaveFooter();
        this.removeModalWarnings();
      });
    document
      .getElementById("add-container-modal-cancel")
      .addEventListener("click", () => {
        addContainerModal.classList.remove("is-active");
        this.showSaveFooter();
        this.removeModalWarnings();
      });
    document
      .getElementById("add-container-modal-add")
      .addEventListener("click", () => {
        let containerName = addContainerNameField.value;
        let containerSlots = addContainerSlotsField.value;
        let carriedBy =
          carriedByField.value == "not carried"
            ? "not carried"
            : Number(carriedByField.value);

        let load = loadField.value;
        //check to make sure the user inputed a value for both the container name and slots)
        if (
          containerName.trim().length == 0 ||
          this.isContainer(containerName)
        ) {
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
        this.setActiveContainer();
      });
  },

  initializeEditContainerModal() {
    const editContainerModal = document.getElementById("edit-container-modal");
    const carriedSelectField = document.getElementById(
      "edit-container-modal-carried-select"
    );
    const deleteCheckbox = document.getElementById(
      "edit-container-modal-delete-checkbox"
    );
    // const updateSection = document.getElementById(
    //   "edit-container-modal-update-section"
    // );
    const removeButton = document.getElementById("edit-container-modal-remove");
    const saveButton = document.getElementById("edit-container-modal-update");

    carriedSelectField.onchange = () => {
      if (carriedSelectField.value == "not carried") {
        document.getElementById(
          "edit-container-modal-load-field"
        ).disabled = true;
      } else {
        document.getElementById(
          "edit-container-modal-load-field"
        ).disabled = false;
      }
    };

    deleteCheckbox.onchange = () => {
      if (deleteCheckbox.checked) {
        document.getElementById(
          "edit-container-modal-move-items-destination"
        ).disabled = false;
        removeButton.disabled = false;
        saveButton.disabled = true;
        // updateSection.classList.add("inactive");
      } else {
        document.getElementById(
          "edit-container-modal-move-items-destination"
        ).disabled = true;
        removeButton.disabled = true;

        saveButton.disabled = false;
        // updateSection.classList.remove("inactive");
      }
    };

    document
      .getElementById("edit-container-modal-close")
      .addEventListener("click", () => {
        editContainerModal.classList.remove("is-active");
        this.showSaveFooter();
        this.removeModalWarnings();
      });

    document
      .getElementById("edit-container-modal-cancel")
      .addEventListener("click", () => {
        editContainerModal.classList.remove("is-active");
        this.showSaveFooter();
        this.removeModalWarnings();
      });

    saveButton.onclick = () => {
      this.updateContainer(this.selectedEditContainerID);
      this.setActiveContainer(this.selectedContainer);
      this.showSaveFooter();
      this.removeModalWarnings();
      console.log(this.items, this.containers);
      editContainerModal.classList.remove("is-active");
    };
    removeButton.onclick = () => {
      const containerDestinationID = document.getElementById(
        "edit-container-modal-move-items-destination"
      ).value;

      if (containerDestinationID == "delete") {
        console.log("delete container ", containerDestinationID);
        this.deleteAllContainerItems(this.selectedEditContainerID);
        this.deleteContainer(this.selectedEditContainerID);
        this.setActiveContainer(0);
        this.showSaveFooter();
        this.removeModalWarnings();
        editContainerModal.classList.remove("is-active");
      } else {
        // containerDestinationID = Number(containerDestinationID);
        // console.log(containerDestinationID);
        this.moveAllContainerItems(
          this.selectedEditContainerID,
          Number(containerDestinationID)
        );
        this.deleteContainer(this.selectedEditContainerID);
        this.setActiveContainer(0);
        this.showSaveFooter();
        this.removeModalWarnings();
        editContainerModal.classList.remove("is-active");
      }
      //   this.containers = this.containers.filter(
      //     (container) => container.name !== containerName
      //   );
      //   this.setActiveContainer("main");
      //   this.updateAddItemContainerSelection();
      //   this.updateEditContainerSelection();
      //   addContainerModal.classList.remove("is-active");
      //   this.showSaveFooter();
      //   this.removeModalWarnings();
    };
  },

  updateContainer(id) {
    const container = this.containers.find((container) => container.id === id);
    const containerNameField = document.getElementById(
      "edit-container-modal-name-field"
    );
    const containerSlotsField = document.getElementById(
      "edit-container-modal-slots-field"
    );
    const carriedByField = document.getElementById(
      "edit-container-modal-carried-select"
    );
    const loadField = document.getElementById(
      "edit-container-modal-load-field"
    );

    container.name = containerNameField.value;
    container.slots = containerSlotsField.value;
    container.load = loadField.value;
    container.carriedBy = carriedByField.value;

    // Clear any items that are carrying this container
    this.items = this.items.filter((item) => item.carrying !== id);

    // Add carrying items
    if (
      container.carriedBy !== null &&
      container.carriedBy !== undefined &&
      container.carriedBy !== "not carried"
    ) {
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

  setEditContainerModal(id) {
    // Function runs when the user clicks the edit button on a container

    this.selectedEditContainerID = id;
    this.hideSaveFooter();

    const container = this.containers.find((container) => container.id === id);

    const editContainerModal = document.getElementById("edit-container-modal");
    editContainerModal.classList.add("is-active");
    const containerNameField = document.getElementById(
      "edit-container-modal-name-field"
    );
    const containerSlotsField = document.getElementById(
      "edit-container-modal-slots-field"
    );
    const carriedByField = document.getElementById(
      "edit-container-modal-carried-select"
    );
    const loadField = document.getElementById(
      "edit-container-modal-load-field"
    );
    const removeContainerSelect = document.getElementById(
      "edit-container-modal-move-items-destination"
    );
    const deleteCheckbox = document.getElementById(
      "edit-container-modal-delete-checkbox"
    );
    const itemDestination = document.getElementById(
      "edit-container-modal-move-items-destination"
    );

    console.log(container.carriedBy);

    containerNameField.value = container.name;
    containerSlotsField.value = container.slots;
    loadField.value = container.load;
    carriedByField.innerHTML = "";
    carriedByField.appendChild(this.createOption("not carried", "not carried"));
    this.containers.forEach((c) => {
      if (c.name !== container.name) {
        carriedByField.appendChild(this.createOption(c.name, c.id));
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
        removeContainerSelect.appendChild(this.createOption(c.name, c.id));
      }
    });
    removeContainerSelect.appendChild(
      this.createOption("** Delete Items **", "delete")
    );
  },

  initializeItemDescriptionModal() {
    const itemDescriptionModal = document.getElementById(
      "item-description-modal"
    );
    document
      .getElementById("item-description-modal-close")
      .addEventListener("click", () => {
        itemDescriptionModal.classList.remove("is-active");
      });
  },

  showSaveFooter() {
    document
      .getElementById("save-button-footer-wrapper")
      .classList.remove("hidden");
  },

  hideSaveFooter() {
    document
      .getElementById("save-button-footer-wrapper")
      .classList.add("hidden");
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
    const containerSelect = document.getElementById(
      "add-item-modal-container-select"
    );
    containerSelect.innerHTML = "";
    this.containers.forEach((container) => {
      containerSelect.appendChild(
        this.createOption(container.name, container.id)
      );
    });
  },

  editItem(index) {
    this.showAddItem("edit", index);
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
    this.containers = this.containers.filter(
      (container) => container.id !== id
    );
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

  showAddItem(mode = "add", index = null) {
    this.hideSaveFooter();

    document.getElementById("add-item-modal").classList.add("is-active");
    document.getElementById("add-item-modal-container-select").value =
      this.selectedContainer;

    if (mode == "edit" && index !== null) {
      document.getElementById("add-item-modal-save").classList.add("hidden");
      document
        .getElementById("add-item-modal-save-edits")
        .classList.remove("hidden");
      document.getElementById("add-item-modal-title").textContent = "Edit Item";
      document
        .getElementById("add-item-modal-delete")
        .classList.remove("hidden");

      this.selectedItemIndex = index;

      // Populate the fields with the item's data
      document.getElementById("add-item-modal-name-field").value =
        this.items[index].name;
      document.getElementById("add-item-modal-uses-field").value =
        this.items[index].max_uses;
      document.getElementById("add-item-modal-description-field").value =
        this.items[index].description;

      // Select the tags
      const tagButtons = document.querySelectorAll(".tag");
      tagButtons.forEach((button) => {
        if (this.items[index].tags.includes(button.textContent.trim())) {
          button.classList.add("selected");
        }
      });
      this.toggleUses();

      // Select the container
      document.getElementById("add-item-modal-container-select").value =
        this.items[index].location;
    } else {
      document.getElementById("add-item-modal-save").classList.remove("hidden");
      document
        .getElementById("add-item-modal-save-edits")
        .classList.add("hidden");
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

    const carriedBySelect = document.getElementById(
      "add-container-modal-carried-select"
    );
    carriedBySelect.innerHTML = "";
    let carriedByPlaceholder = this.createOption("not carried", "not carried");
    carriedBySelect.appendChild(carriedByPlaceholder);

    this.containers.forEach((container) => {
      carriedBySelect.appendChild(
        this.createOption(container.name, container.id)
      );
    });
    carriedBySelect.value = "not carried";
  },
};

export default inventoryModule;

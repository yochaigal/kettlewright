import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import utils, { createOption } from "./utils.js";

const inventoryModalUI = {
  openModal: "none",
  page: "character",
  item: {},
  container: {},
  itemModalMode: "add", // "add" or "edit"

  // Add/Edit Item Modal
  itemNameField: document.getElementById("add-edit-item-modal-name-field"),
  itemUsesField: document.getElementById("add-edit-item-modal-uses-field"),
  itemChargesField: document.getElementById("add-edit-item-modal-charges-field"),
  itemMaxChargesField: document.getElementById("add-edit-item-modal-max-charges-field"),
  itemDescriptionField: document.getElementById("add-edit-item-modal-description-field"),
  itemContainerSelect: document.getElementById("add-edit-item-modal-container-select"),
  itemErrorContainer: document.getElementById("add-edit-item-modal-error-container"),
  itemErrorText: document.getElementById("add-edit-item-modal-error-text"),
  itemDeleteButton: document.getElementById("add-edit-item-modal-delete"),
  itemTransferButton: document.getElementById("add-edit-item-modal-transfer"),
  itemTitleText: document.getElementById("add-edit-item-modal-title"),
  maxItemNameLength: 40,
  maxItemDescriptionLength: 1000,
  maxUsesCharges: 99,

  // Add/Edit Container Modal
  removeContainerItemDestination: document.getElementById("add-edit-container-modal-move-items-destination"),
  containerErrorContainer: document.getElementById("add-edit-container-error-container"),
  containerErrorText: document.getElementById("add-edit-container-error-text"),
  maxContainerSlots: 20,
  maxContainerLoad: 10,
  maxContainerNameLength: 30,

  initialize(page = "character") {
    this.page = page;
    this.initializeInventoryModals();
    this.initializeTagButtons();
    this.initializeAddEditItemModal();
    this.initializeContainerModal();
    this.initializeTransferItemModal();
  },

  initializeInventoryModals() {
    document.querySelectorAll(".inventory-modal-background").forEach((modal) => {
      modal.addEventListener("click", () => {
        this.closeInventoryModals();
        this.removeModalWarnings();
      });
    });
    document.querySelectorAll(".inventory-modal-cancel-button").forEach((button) => {
      button.addEventListener("click", () => {
        this.closeInventoryModals();
        this.removeModalWarnings();
      });
    });
  },

  // _____________ Shared _____________

  populateContainerOptions(selectElement, selectedID = null, excludedID = null, placeholder = null) {
    // Populate the container select element with the containers in the inventory
    // With the option to exclude a container by ID
    selectElement.innerHTML = "";
    if (placeholder) {
      selectElement.appendChild(createOption(placeholder, ""));
    }
    let containers = inventory.getContainers();
    containers.forEach((container) => {
      if (container.id !== excludedID) {
        let option = createOption(container.name, container.id);
        if (container.id === selectedID) {
          option.selected = true;
        }
        selectElement.appendChild(option);
      }
    });
  },

  closeInventoryModals() {
    document.querySelectorAll(".inventory-modal").forEach((modal) => {
      modal.classList.remove("is-active");
    });

    if (this.openModal !== "description") {
      inventoryUI.showSaveFooter();
      this.openModal = "none";
    }
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
    this.containerErrorText.textContent = "";
    this.containerErrorContainer.classList.add("hidden");
    this.itemErrorText.textContent = "";
    this.itemErrorContainer.classList.add("hidden");
  },
  // _____________ Item Description Modal _____________

  showItemDescriptionModal(description) {
    document.getElementById("item-description-modal").classList.add("is-active");
    document.getElementById("item-description-modal-content").textContent = description;
  },

  // _____________ Item Add/Edit Modal _____________
  //Add and edit item models share the same html

  initializeAddEditItemModal() {
    document.getElementById("add-edit-item-modal-save").addEventListener("click", () => {
      const showErrorMessage = (field, message) => {
        field.focus();
        field.classList.add("is-danger");
        this.itemErrorText.textContent = message;
        this.itemErrorContainer.classList.remove("hidden");
        field.scrollIntoView();
      };

      // check for errors
      if (this.itemNameField.value.trim() === "" || this.itemNameField.value.length >= this.maxItemNameLength) {
        showErrorMessage(this.itemNameField, `Item name must be between 1 and ${this.maxItemNameLength} characters`);
      } else if (this.itemDescriptionField.value.length >= this.maxItemDescriptionLength) {
        showErrorMessage(
          this.itemDescriptionField,
          `Item description must be less than ${this.maxItemDescriptionLength} characters`
        );
      } else if (this.itemUsesField.value > this.maxUsesCharges) {
        showErrorMessage(this.itemUsesField, `Uses must be less than ${this.maxUsesCharges + 1}`);
      } else if (this.itemChargesField.value > this.maxUsesCharges) {
        showErrorMessage(this.itemChargesField, `Charges must be less than ${this.maxUsesCharges + 1}`);
      } else if (this.itemMaxChargesField.value > this.maxUsesCharges) {
        showErrorMessage(this.itemMaxChargesField, `Max charges must be less than ${this.maxUsesCharges + 1}`);
      }
      // save the item
      else if (this.itemModalMode === "add" || this.itemModalMode === "edit") {
        this.saveItem(this.itemModalMode === "edit" ? this.item : undefined);
        this.closeInventoryModals();
        this.removeModalWarnings();
        inventoryUI.showSaveFooter();
      }
    });

    this.itemDeleteButton.addEventListener("click", () => {
      inventory.deleteItem(this.item.id);
      this.closeInventoryModals();
      inventoryUI.refreshInventory();
    });
    // chanage the transfer button if the page is the party page
    if (this.page === "party") {
      const transferButton = document.getElementById("add-edit-item-modal-transfer");
      const transferButtonIcon = transferButton.querySelector("i");
      transferButton.innerHTML = "";
      let transferButtonText = document.createTextNode(" Character");
      transferButton.appendChild(transferButtonIcon);
      // transferButton.appendChild(transferButtonText);
    }
    this.itemTransferButton.addEventListener("click", () => {
      if (this.page === "party") {
        this.saveItem(this.item);
        this.closeInventoryModals();
        this.showTransferItemModal(this.item);
      } else {
        this.saveItem(this.item);
        this.closeInventoryModals();
        inventory.transferItem(this.item);
        // console.log("transfering item...", inventory.getTransfer());
        inventory.deleteItem(this.item.id);
        inventoryUI.refreshInventory();
      }
    });
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
          if (selectedDamageTags.length >= 1) {
            selectedDamageTags.forEach((tag) => tag.classList.remove("selected"));
          }

          // select the damage tag
          currentTag.classList.add("selected");
        }
      }
    }
  },

  toggleUses() {
    if (document.getElementById("tag-button-uses").classList.contains("selected")) {
      document.getElementById("add-edit-item-modal-uses-container").classList.remove("inactive");
    } else {
      document.getElementById("add-edit-item-modal-uses-container").classList.add("inactive");
    }

    if (document.getElementById("tag-button-charges").classList.contains("selected")) {
      document.getElementById("add-edit-item-modal-charges-container").classList.remove("inactive");
    } else {
      document.getElementById("add-edit-item-modal-charges-container").classList.add("inactive");
    }
  },

  showAddEditItemModal(item = null) {
    this.item = item;
    if (item === null) {
      this.itemModalMode = "add";
      this.itemTitleText.textContent = "Add Item";
      let item = {
        name: "",
        uses: "",
        charges: "",
        max_charges: "",
        description: "",
        tags: [],
        location: inventoryUI.getSelectedContainer(),
      };
      this.itemDeleteButton.classList.add("hidden");
      this.itemTransferButton.classList.add("hidden");
      this.populateAddEditItemModal(item);
    } else {
      this.itemTitleText.textContent = "Edit Item";
      this.itemModalMode = "edit";
      this.itemDeleteButton.classList.remove("hidden");
      this.itemTransferButton.classList.remove("hidden");
      this.populateAddEditItemModal(item);
    }
    document.getElementById("add-edit-item-modal").classList.add("is-active");
    inventoryUI.hideSaveFooter();
    document.getElementById("add-edit-item-modal-body").scrollTop = 0;
    console.log("resizing text area");
    resizeTextarea(document.getElementById("add-edit-item-modal-description-field"));
  },

  populateAddEditItemModal(
    item = { name: "", uses: "", charges: "", max_charges: "", description: "", tags: [], location: 0 }
  ) {
    this.item = item;
    this.itemNameField.value = item.name;
    this.itemUsesField.value = item.uses;
    this.itemChargesField.value = item.charges;
    this.itemMaxChargesField.value = item.max_charges;
    this.itemDescriptionField.value = item.description;
    this.populateContainerOptions(this.itemContainerSelect, item.location);

    // Select the tags
    const tagButtons = document.querySelectorAll(".tag");
    tagButtons.forEach((button) => button.classList.remove("selected"));
    //Remove any newline characters that may be added by the prettier or other formatting extensions
    tagButtons.forEach((button) => {
      button.textContent = button.textContent.replace(/[\r\n]/g, "");
    });

    const selectButtonIfTagMatches = (tag, tagId) => {
      if (item.tags.includes(tag)) {
        const tagButton = document.getElementById(tagId);
        if (tagButton) {
          tagButton.classList.add("selected");
          tagButton.textContent = tag;
        }
      }
    };

    tagButtons.forEach((button) => {
      if (item.tags.includes(button.textContent.trim())) {
        button.classList.add("selected");
      }
    });

    selectButtonIfTagMatches("d4 + d4", "tag-button-d4");
    selectButtonIfTagMatches("d6 + d6", "tag-button-d6");
    selectButtonIfTagMatches("d8 + d8", "tag-button-d8");
    selectButtonIfTagMatches("d10 + d10", "tag-button-d10");
    selectButtonIfTagMatches("d12 + d12", "tag-button-d12");

    this.toggleUses();
  },

  saveItem() {
    // when the add/edit item modal is openend, this.item is set to the item being edited
    // this updates the item with the values from the modal
    // when editing, the item id is already set, new id's are generated by inventory.addOrUpdateItem()

    this.item.name = this.itemNameField.value;
    this.item.uses = +this.itemUsesField.value;
    this.item.charges = +this.itemChargesField.value;
    this.item.max_charges = +this.itemMaxChargesField.value;
    if (this.item.max_charges < this.item.charges) {
      this.item.max_charges = this.item.charges;
    }
    this.item.description = this.itemDescriptionField.value;
    this.item.tags = [];
    this.item.location = +this.itemContainerSelect.value;

    const tagButtons = document.querySelectorAll(".tag");
    tagButtons.forEach((button) => {
      if (button.classList.contains("selected")) {
        this.item.tags.push(button.textContent.trim());
      }
    });
    inventory.addOrUpdateItem(this.item);
    this.closeInventoryModals();
    inventoryUI.refreshInventory();
  },

  // _____________ Add/Edit Container Modal _____________

  initializeContainerModal() {
    const carriedBySelect = document.getElementById("add-edit-container-modal-carried-select");
    const containerNameField = document.getElementById("add-edit-container-modal-name-field");
    const containerSlotsField = document.getElementById("add-edit-container-modal-slots-field");
    const containerLoadField = document.getElementById("add-edit-container-modal-load-field");
    const saveButton = document.getElementById("add-edit-container-modal-save");
    const deleteCheckbox = document.getElementById("add-edit-container-modal-delete-checkbox");
    const removeButton = document.getElementById("add-edit-container-modal-remove");

    this.populateContainerOptions(carriedBySelect, null, null, "Not carried");

    saveButton.addEventListener("click", () => {
      this.removeModalWarnings();

      let containerName = containerNameField.value;
      let containerSlots = containerSlotsField.value;

      const showErrorMessage = (field, message) => {
        field.focus();
        field.classList.add("is-danger");
        this.containerErrorText.textContent = message;
        this.containerErrorContainer.classList.remove("hidden");
      };

      // Check for errors

      // Container name must be unique and under maxContainerNameLength characters
      if (
        containerName.trim().length == 0 ||
        (this.openModal === "add" && inventory.getContainerID(containerName)) ||
        (this.openModal === "edit" &&
          inventory.getContainerID(containerName) &&
          inventory.getContainerID(containerName) !== this.container.id) ||
        containerName.length >= this.maxContainerNameLength
      ) {
        showErrorMessage(
          containerNameField,
          `Container name must be unique and between 1 and ${this.maxContainerNameLength} characters`
        );
      }
      // Slots must be between 1 and maxContainerSlots
      else if (containerSlots.length == 0 || containerSlots <= 0 || containerSlots > this.maxContainerSlots) {
        showErrorMessage(containerSlotsField, `Slots must be between 1 and ${this.maxContainerSlots}`);
      }
      // Load must be between 1 and maxContainerLoad if container is carried
      else if (carriedBySelect.value !== "" && containerLoadField.value === "") {
        showErrorMessage(containerLoadField, `Load must be set if container is carried`);
      }
      // else save the container
      else {
        this.saveContainer(this.container || {});
        this.removeModalWarnings();
      }
    });

    carriedBySelect.addEventListener("change", () => {
      containerLoadField.disabled = carriedBySelect.value === "";
    });

    if (deleteCheckbox) {
      deleteCheckbox.addEventListener("change", () => {
        this.removeContainerItemDestination.disabled = !deleteCheckbox.checked;
        removeButton.disabled = !deleteCheckbox.checked;
        if (!deleteCheckbox.checked) {
          this.removeContainerItemDestination.value = "";
        }
      });
    }

    if (removeButton) {
      removeButton.addEventListener("click", () => {
        if (this.removeContainerItemDestination.value === "") {
          inventory.deleteContainer(this.container.id);
        } else {
          inventory.deleteContainer(this.container.id, this.removeContainerItemDestination.value);
        }
        this.closeInventoryModals();
        inventoryUI.refreshInventory();
      });
    }
  },

  showContainerModal(container = null) {
    this.openModal = container ? "edit" : "add";
    this.container = container;
    const modal = document.getElementById("add-edit-container-modal");
    const title = document.getElementById("add-edit-container-modal-title");
    const removeSection = document.getElementById("add-edit-container-modal-remove-section");
    const removeButton = document.getElementById("add-edit-container-modal-remove");

    modal.classList.add("is-active");

    if (container) {
      title.textContent = "Edit Container";
      removeSection.classList.remove("hidden");
      removeButton.classList.remove("hidden");
    } else {
      title.textContent = "Add Container";
      removeSection.classList.add("hidden");
      removeButton.classList.add("hidden");
    }

    inventoryUI.hideSaveFooter();
    this.populateContainerModal(container);
  },

  populateContainerModal(container) {
    const nameField = document.getElementById("add-edit-container-modal-name-field");
    const slotsField = document.getElementById("add-edit-container-modal-slots-field");
    const carriedBySelect = document.getElementById("add-edit-container-modal-carried-select");
    const loadField = document.getElementById("add-edit-container-modal-load-field");
    const removeSection = document.getElementById("add-edit-container-modal-remove-section");

    nameField.value = container ? container.name : "";
    slotsField.value = container ? container.slots : "";
    this.populateContainerOptions(
      carriedBySelect,
      container ? container.carried_by : null,
      container ? container.id : null,
      "Not carried"
    );

    if (container) {
      console.log("populating edit container modal");
      carriedBySelect.value = container.carried_by || "";
      loadField.value = container.load || "";
      loadField.disabled = !container.carried_by;
      if (removeSection) {
        removeSection.classList.remove("hidden");
        this.populateRemoveContainerDestination(container);
      }
    } else {
      loadField.value = "";
      loadField.disabled = true;
      if (removeSection) {
        removeSection.classList.add("hidden");
      }
    }
  },

  saveContainer(container) {
    container.name = document.getElementById("add-edit-container-modal-name-field").value;
    container.load = document.getElementById("add-edit-container-modal-load-field").value;
    container.slots = document.getElementById("add-edit-container-modal-slots-field").value;
    container.carried_by = document.getElementById("add-edit-container-modal-carried-select").value;
    inventory.addOrUpdateContainer(container);
    this.closeInventoryModals();
    inventoryUI.refreshInventory();
  },

  populateRemoveContainerDestination(container) {
    console.log("populating remove container destination");
    this.removeContainerItemDestination.innerHTML = "";
    utils.addOptionToSelect(this.removeContainerItemDestination, "", "Delete items");
    let containers = inventory.getContainers().filter((c) => c.id !== container.id);
    containers.forEach((c) => {
      utils.addOptionToSelect(this.removeContainerItemDestination, c.id, c.name);
    });
  },

  // _____________ Transfer Item Modal Modal _____________

  initializeTransferItemModal() {
    const transferSaveButton = document.getElementById("party-transfer-item-modal-save");
    transferSaveButton.addEventListener("click", () => {
      let destination = document.getElementById("party-item-transfer-modal-select").value;
      if (destination !== "" && destination !== "0") {
        inventory.transferPartyItem(this.item, destination);
        inventory.deleteItem(this.item.id);
        this.closeInventoryModals();
        inventoryUI.refreshInventory();
      }
    });
  },

  showTransferItemModal(item) {
    document.getElementById("party-item-transfer-modal").classList.add("is-active");
    inventoryUI.hideSaveFooter();
  },
};

export default inventoryModalUI;

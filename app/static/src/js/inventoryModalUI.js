import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import utils, { createOption } from "./utils.js";
//import { DragAndDropModule } from "./dragAndDrop.js";

const inventoryModalUI = {
  openModal: "none",
  page: "character",
  item: {},
  container: {},
  itemNameField: document.getElementById("add-item-modal-name-field"),
  itemUsesField: document.getElementById("add-item-modal-uses-field"),
  itemChargesField: document.getElementById("add-item-modal-charges-field"),
  itemMaxChargesField: document.getElementById("add-item-modal-max-charges-field"),
  itemDescriptionField: document.getElementById("add-item-modal-description-field"),
  itemContainerSelect: document.getElementById("add-item-modal-container-select"),
  removeContainerItemDestination: document.getElementById("edit-container-modal-move-items-destination"),

  initialize(page = "character") {
    this.page = page;
    this.initializeInventoryModals();
    this.initializeTagButtons();
    this.initializeAddEditItemModal();
    this.initializeAddContainerModal();
    this.initializeEditContainerModal();
    this.initializeTransferItemModal();
  },

  initializeInventoryModals() {
    document.querySelectorAll(".inventory-modal-background").forEach((modal) => {
      modal.addEventListener("click", () => {
        this.closeInventoryModals();
      });
    });
    document.querySelectorAll(".inventory-modal-cancel-button").forEach((button) => {
      button.addEventListener("click", () => {
        this.closeInventoryModals();
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
  },
  // _____________ Item Description Modal _____________

  showItemDescriptionModal(description) {
    document.getElementById("item-description-modal").classList.add("is-active");
    document.getElementById("item-description-modal-content").textContent = description;
  },

  // _____________ Item Add/Edit Modal _____________
  //Add and edit item models share the same html

  initializeAddEditItemModal() {
    document.getElementById("add-item-modal-save").addEventListener("click", () => {
      this.saveItem();
      this.closeInventoryModals();
      inventoryUI.showSaveFooter();
    });
    document.getElementById("add-item-modal-save-edits").addEventListener("click", () => {
      this.saveItem(this.item);
      this.closeInventoryModals();
      inventoryUI.showSaveFooter();
    });
    document.getElementById("add-item-modal-delete").addEventListener("click", () => {
      inventory.deleteItem(this.item.id);
      this.closeInventoryModals();
      inventoryUI.refreshInventory();
    });
    // chanage the transfer button if the page is the party page
    if (this.page === "party") {
      const transferButton = document.getElementById("add-item-modal-transfer");
      const transferButtonIcon = transferButton.querySelector("i");
      transferButton.innerHTML = "";
      let transferButtonText = document.createTextNode(" Character");
      transferButton.appendChild(transferButtonIcon);
      // transferButton.appendChild(transferButtonText);
    }
    document.getElementById("add-item-modal-transfer").addEventListener("click", () => {
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

  showAddEditItemModal(item = null) {
    this.item = item;
    if (item === null) {
      // if item is null, it is an add item modal
      document.getElementById("add-item-modal-save-edits").classList.add("hidden");
      document.getElementById("add-item-modal-save").classList.remove("hidden");
      let item = {
        name: "",
        uses: "",
        charges: "",
        max_charges: "",
        description: "",
        tags: [],
        location: inventoryUI.getSelectedContainer(),
      };
      this.populateAddEditItemModal(item);

      //resize description textbox
    } else {
      document.getElementById("add-item-modal-save-edits").classList.remove("hidden");
      document.getElementById("add-item-modal-save").classList.add("hidden");
      this.populateAddEditItemModal(item);
    }
    document.getElementById("add-edit-item-modal").classList.add("is-active");
    inventoryUI.hideSaveFooter();
    document.getElementById("add-edit-item-modal-body").scrollTop = 0;
    console.log("resizing text area");
    resizeTextarea(document.getElementById("add-item-modal-description-field"));
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
    console.log("item location", item.location);
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

  // _____________ Add Container Modal _____________

  initializeAddContainerModal() {
    const carriedBySelect = document.getElementById("add-container-modal-carried-select");
    const addContainerNameField = document.getElementById("add-container-modal-name-field");
    const addContainerSlotsField = document.getElementById("add-container-modal-slots-field");

    this.populateContainerOptions(carriedBySelect, null, null, "Not carried");
    document.getElementById("add-container-modal-save").addEventListener("click", () => {
      this.removeModalWarnings();

      let containerName = addContainerNameField.value;
      let containerSlots = addContainerSlotsField.value;

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
        this.saveContainer(this.container);
        this.removeModalWarnings();
      }
    });

    carriedBySelect.addEventListener("change", () => {
      document.getElementById("add-container-modal-load-field").disabled = carriedBySelect.value === "" ? true : false;
    });
  },

  initializeEditContainerModal() {
    const editContainerNameField = document.getElementById("edit-container-modal-name-field");
    const editContainerSlotsField = document.getElementById("edit-container-modal-slots-field");

    document.getElementById("edit-container-modal-save").addEventListener("click", () => {
      this.removeModalWarnings();

      let containerName = editContainerNameField.value;
      let containerSlots = editContainerSlotsField.value;

      //check to make sure the user inputed a value for both the container name and slots)
      if (
        containerName.trim().length == 0 ||
        (inventory.getContainerID(containerName) && inventory.getContainerID(containerName) !== this.container.id)
      ) {
        editContainerNameField.focus();
        editContainerNameField.classList.add("is-danger");
        return;
      }
      if (containerSlots.length == 0 || containerSlots <= 0) {
        editContainerSlotsField.focus();
        editContainerSlotsField.classList.add("is-danger");
        return;
      }
      if (containerName !== "" && containerSlots > 0) {
        this.saveContainerEdits(this.container);
        this.removeModalWarnings();
      }
    });

    document.getElementById("edit-container-modal-delete-checkbox").addEventListener("change", () => {
      if (document.getElementById("edit-container-modal-delete-checkbox").checked) {
        this.removeContainerItemDestination.disabled = false;
        document.getElementById("edit-container-modal-remove").disabled = false;
      } else {
        this.removeContainerItemDestination.disabled = true;
        document.getElementById("edit-container-modal-remove").disabled = true;
        this.removeContainerItemDestination.value = "";
      }
    });

    document.getElementById("edit-container-modal-remove").addEventListener("click", () => {
      if (this.removeContainerItemDestination.value === "") {
        inventory.deleteContainer(this.container.id);
      } else {
        inventory.deleteContainer(this.container.id, this.removeContainerItemDestination.value);
      }
      this.closeInventoryModals();
      inventoryUI.refreshInventory();
    });
  },

  showAddContainerModal() {
    this.openModal = "add-container";
    document.getElementById("add-container-modal").classList.add("is-active");
    inventoryUI.hideSaveFooter();
    this.clearAddContainerModal();
  },

  clearAddContainerModal() {
    document.getElementById("add-container-modal-name-field").value = "";
    document.getElementById("add-container-modal-load-field").value = "";
    document.getElementById("add-container-modal-slots-field").value = "";
  },

  showEditContainerModal(container) {
    this.openModal = "edit-container";
    this.container = container;
    document.getElementById("edit-container-modal").classList.add("is-active");
    inventoryUI.hideSaveFooter();
    this.populateEditContainerModal(container);
  },

  populateEditContainerModal(container) {
    document.getElementById("edit-container-modal-name-field").value = container.name;
    document.getElementById("edit-container-modal-slots-field").value = container.slots;
    const carriedBySelect = document.getElementById("edit-container-modal-carried-select");
    this.populateContainerOptions(carriedBySelect, container.carried_by, container.id, "Not carried");
    carriedBySelect.addEventListener("change", () => {
      document.getElementById("edit-container-modal-load-field").disabled = carriedBySelect.value === "" ? true : false;
    });
    if (container.carried_by) {
      document.getElementById("edit-container-modal-carried-select").value = container.carried_by;
      document.getElementById("edit-container-modal-load-field").value = container.load;
    } else {
      document.getElementById("edit-container-modal-load-field").disabled = true;
    }

    // Populate the move container desitnation
    this.removeContainerItemDestination.innerHTML = "";
    utils.addOptionToSelect(this.removeContainerItemDestination, "", "Delete items");
    let containers = inventory.getContainers();
    containers = containers.filter((c) => c.id !== container.id);
    containers.forEach((c) => {
      utils.addOptionToSelect(this.removeContainerItemDestination, c.id, c.name);
    });
  },

  saveContainer(container = null) {
    container = container || {};
    container.name = document.getElementById("add-container-modal-name-field").value;
    container.load = document.getElementById("add-container-modal-load-field").value;
    container.slots = document.getElementById("add-container-modal-slots-field").value;
    container.carried_by = document.getElementById("add-container-modal-carried-select").value;
    // if the container is being edited, it will have an id, if not it will be generated by addOrUpdateContainer
    inventory.addOrUpdateContainer(container);
    this.closeInventoryModals();
    inventoryUI.refreshInventory();
  },

  saveContainerEdits() {
    let container = this.container;
    container.name = document.getElementById("edit-container-modal-name-field").value;
    container.load = document.getElementById("edit-container-modal-load-field").value;
    container.slots = document.getElementById("edit-container-modal-slots-field").value;
    container.carried_by = document.getElementById("edit-container-modal-carried-select").value;
    inventory.addOrUpdateContainer(container);
    this.closeInventoryModals();
    inventoryUI.refreshInventory();
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

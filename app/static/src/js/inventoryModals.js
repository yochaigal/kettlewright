import inventoryModule from "./inventory.js";

const inventoryModals = {
  containers: [],
  initializeAddItemModal() {
    const addItemModal = document.getElementById("add-item-modal");
    const itemNameField = document.getElementById("add-item-modal-name-field");
    const usesField = document.getElementById("add-item-modal-uses-field");
    const chargesField = document.getElementById(
      "add-item-modal-charges-field"
    );
    const maxChargesField = document.getElementById(
      "add-item-modal-max-charges-field"
    );
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

    this.initializeTagButtons();
    //this.manageTagButtonState();
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
        updateTags();
        this.addItem({
          name: this.sanitizeString(itemNameField.value),
          tags: tags,
          uses: usesField.value,
          charges: chargesField.value,
          max_charges: maxChargesField.value,
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
        this.items[this.selectedItemIndex].uses = usesField.value;
        this.items[this.selectedItemIndex].charges = usesField.value;
        this.items[this.selectedItemIndex].max_charges = maxChargesField.value;
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

  initializeTagButtons() {
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
          currentTag.textContent =
            currentTag.textContent + " + " + currentTag.textContent;
          tagButtons.forEach((tag) => {
            if (
              damageTags.includes(tag.textContent.trim()) &&
              tag !== currentTag
            ) {
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

  toggleUses() {
    if (
      document.getElementById("tag-button-uses").classList.contains("selected")
    ) {
      document
        .getElementById("add-item-modal-uses-container")
        .classList.remove("inactive");
    } else {
      document
        .getElementById("add-item-modal-uses-container")
        .classList.add("inactive");
    }

    if (
      document
        .getElementById("tag-button-charges")
        .classList.contains("selected")
    ) {
      document
        .getElementById("add-item-modal-charges-container")
        .classList.remove("inactive");
    } else {
      document
        .getElementById("add-item-modal-charges-container")
        .classList.add("inactive");
    }
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
        this.items[index].uses;
      document.getElementById("add-item-modal-description-field").value =
        this.items[index].description;

      // Select the tags
      const tagButtons = document.querySelectorAll(".tag");
      tagButtons.forEach((button) => {
        if (this.items[index].tags.includes(button.textContent.trim())) {
          button.classList.add("selected");
        }
        if (this.items[index].tags.includes("d4 + d4")) {
          document.getElementById("tag-button-d4").classList.add("selected");
          document.getElementById("tag-button-d4").textContent = "d4 + d4";
        } else if (this.items[index].tags.includes("d6 + d6")) {
          document.getElementById("tag-button-d6").classList.add("selected");
          document.getElementById("tag-button-d6").textContent = "d6 + d6";
        } else if (this.items[index].tags.includes("d8 + d8")) {
          document.getElementById("tag-button-d8").classList.add("selected");
          document.getElementById("tag-button-d8").textContent = "d8 + d8";
        } else if (this.items[index].tags.includes("d10 + d10")) {
          document.getElementById("tag-button-d10").classList.add("selected");
          document.getElementById("tag-button-d10").textContent = "d10 + d10";
        } else if (this.items[index].tags.includes("d12 + d12")) {
          document.getElementById("tag-button-d12").classList.add("selected");
          document.getElementById("tag-button-d12").textContent = "d12 + d12";
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
};

export default inventoryModals;

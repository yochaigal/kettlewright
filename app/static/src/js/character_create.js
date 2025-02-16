import utils from "./utils.js";
import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";
import portraitModal from "./edit_portrait_modal.js";
import marketplace from "./marketplace.js";

// Initialize Inventory
inventoryUI.initialize();
inventoryModalUI.initialize();

// Initialize Marketplace/Gear Table
const saveMarketPlaceItems = (items) => {
  inventory.addItems(items);
  inventoryUI.refreshInventory();
};

// Track individual gold for potential gear tables, and setup callbacks to update gold
let gearTable1Gold = 0;
let gearTable2Gold = 0;
const setGearTable1Gold = (gold) => {
  gearTable1Gold = gold;
};
const setGearTable2Gold = (gold) => {
  gearTable2Gold = gold;
};

marketplace.initialize(marketplaceData, "gear", 0, saveMarketPlaceItems, setGearTable1Gold);

// Initialize the background data
let backgroundData = JSON.parse(backgroundRawData);
let description = "";
let background = "";
let gold = 0;
let bonusGold = 0;
let table1gold = 0;
let table2gold = 0;
let bondsGold = 0;

const resetInventory = () => {
  // reset the background data and clear inventory
  backgroundData = JSON.parse(backgroundRawData);
  inventory.resetInventory();
};

const removeItemsContainersByField = (field) => {
  // Remove items from inventory that were added by a specific field (e.g. "table_1")
  console.log("Removing items added by", field);
  const newItems = inventory.getItems().filter((item) => item.added_by !== field);
  inventory.setItems(newItems);

  const newContainers = inventory.getContainers().filter((container) => container.added_by !== field);
  inventory.setContainers(newContainers);

  inventoryUI.refreshInventory();
};

document.addEventListener("DOMContentLoaded", function () {
  const backgroundField = document.getElementById("background-field");
  const customBackgroundField = document.getElementById("custom-background-field");
  const backgroundTablesContainer = document.getElementById("background-tables-container");
  const backgroundTable1 = document.getElementById("background-table1-select");
  const backgroundTable2 = document.getElementById("background-table2-select");
  const nameDiv = document.getElementById("name-select-roll-container");
  const customNameField = document.getElementById("custom-name-field");
  const nameField = document.getElementById("name-field");
  const strengthField = document.getElementById("strength-max-field");
  const dexterityField = document.getElementById("dexterity-max-field");
  const willpowerField = document.getElementById("willpower-max-field");
  const swapButton = document.getElementById("swap-button");
  const hpField = document.getElementById("hp-max-field");
  const ageField = document.getElementById("age-field");
  const roll = utils.roll;
  const addOptionToSelect = utils.addOptionToSelect;
  const gearTableButton1 = document.getElementById("show-gear-table-1");
  const gearTableButton2 = document.getElementById("show-gear-table-2");

  //
  // ____________________ Edit Portrait ____________________
  //

  portraitModal.initialize("create");

  document.getElementById("create-portrait-container").addEventListener("click", () => {
    portraitModal.openModal();
  });

  //
  // ____________________ Toggles for Activating Fields ____________________
  //

  const toggleCustomBackground = (toggle) => {
    if (toggle) {
      // custom background - don't require background tables, activate custom background and name fields
      backgroundTable1.removeAttribute("required");
      backgroundTable2.removeAttribute("required");
      backgroundTablesContainer.classList.add("hidden");
      nameField.value = "Custom";
      customBackgroundField.classList.remove("inactive");
      nameDiv.classList.add("inactive");
      customNameField.classList.remove("inactive");
    } else {
      backgroundTable1.setAttribute("required", "");
      backgroundTable2.setAttribute("required", "");
      backgroundTablesContainer.classList.remove("hidden");
      customBackgroundField.classList.add("inactive");
      nameDiv.classList.remove("inactive");
      customNameField.classList.add("inactive");
    }
  };

  //
  // ____________________ Background and Name Fields ____________________
  //

  const setBackgroundDescription = (background) => {
    const backgroundDescription = document.getElementById("create-background-description");
    description = backgroundData[background]?.background_description ?? "";
    if (description == '-') description = "";
    backgroundDescription.innerHTML = description;
  };

  const addStartingItems = (background) => {
    if (background !== "Custom" && backgroundData[background]?.starting_gear) {
      backgroundData[background].starting_gear.forEach((item) => {
        const startingItem = {
          ...item,
          location: 0,
          added_by: "background",
        };

        if (!startingItem.description || startingItem.description == '-') {
          startingItem.description = "";
        }

        inventory.addItem(startingItem);
      });
    }
    inventoryUI.refreshInventory();
  };

  const addContainer = (container) => {
    inventory.addContainer(container);
    inventory.convertCarriedByToID();
    inventoryUI.setActiveContainer(0);
    console.log("Added container", inventory.getContainers());
  };

  const addStartingContainers = (background) => {
    if (background !== "Custom" && backgroundData[background]?.starting_containers) {
      backgroundData[background].starting_containers.forEach((container) => {
        addContainer({ ...container, added_by: "background" });
      });
    }
  };

  const populateNames = (background) => {
    const names = backgroundData[background]?.names ?? [];
    nameField.innerHTML = "";
    addOptionToSelect(nameField, "", "Name (d10)...", true, true);
    names.forEach((name) => addOptionToSelect(nameField, name, name));
    addOptionToSelect(nameField, "Custom", "** Custom **");
  };

  const toggleCustomField = (field, isActive) => {
    field.classList.toggle("inactive", !isActive);
  };

  backgroundField.addEventListener("change", () => {
    const background = backgroundField.value;
    populateNames(background);
    setBackgroundDescription(background);
    populateTables(background);
    resetInventory();
    addStartingContainers(background);
    addStartingItems(background);
    toggleCustomBackground(background === "Custom");
  });

  nameField.addEventListener("change", () => {
    toggleCustomField(customNameField, nameField.value === "Custom");
  });

  document.getElementById("submit-button").addEventListener("click", () => {
    if (backgroundField.value !== "Custom") {
      customBackgroundField.value = "none";
    }
    if (nameField.value !== "Custom") {
      customNameField.value = "none";
    }
  });

  //
  // ____________________ Background Tables ____________________
  //

  const populateTables = (background) => {
    if (background === "Custom") {
      return;
    }

    const tables = [
      { tableElement: backgroundTable1, data: backgroundData[background].table1, questionId: "table1-question" },
      { tableElement: backgroundTable2, data: backgroundData[background].table2, questionId: "table2-question" },
    ];

    tables.forEach(({ tableElement, data, questionId }, index) => {
      tableElement.innerHTML = "";

      addOptionToSelect(tableElement, "", "Table (d6)...", true, true);
      document.getElementById(questionId).innerHTML = data.question;

      data.options.forEach((option) => {
        addOptionToSelect(tableElement, option.description, truncateText(option.description, 36, "..."));
      });

      document.getElementById(`background-table${index + 1}-description`).innerHTML = "";
    });
  };

  // Add table result items to the inventory
  const addTableItems = (items, addedBy) => {
    if (items) {
      for (let item of items) {
        const fullItem = { ...item, location: 0, added_by: addedBy };
        inventory.addItem(fullItem);
      }
    }
    inventoryUI.refreshInventory();
  };

  const resetGold = () => {
    gold = 0;
    bonusGold = 0;
    table1gold = 0;
    table2gold = 0;
    bondsGold = 0;
    updateGold();
  };

  const updateGold = () => {
    bonusGold = table1gold + table2gold + bondsGold;
    document.getElementById("gold-field").textContent = bonusGold > 0 ? `${gold} + ${bonusGold}` : gold;
  };

  gearTableButton1.addEventListener("click", () => {
    marketplace.showMarketplace();
    marketplace.setGold(gearTable1Gold);
    marketplace.setAddedBy("table_1");
    marketplace.setGoldCallback(setGearTable1Gold);
  });
  gearTableButton2.addEventListener("click", () => {
    marketplace.showMarketplace();
    marketplace.setGold(gearTable2Gold);
    marketplace.setAddedBy("table_2");
    marketplace.setGoldCallback(setGearTable2Gold);
  });

  // Set Results of Table Selection/Roll
  const handleTableResults = (table) => {
    const tableDescriptionId = `background-table${table}-description`;
    const addedBy = `table_${table}`;

    //remove items previously added by the table
    removeItemsContainersByField(addedBy);

    const addTableContainers = (containers, addedBy) => {
      containers.forEach((container) => {
        container.added_by = addedBy;
        addContainer(container);
      });
    };

    const value = table === 1 ? backgroundTable1.selectedIndex : backgroundTable2.selectedIndex;

    if (value === 0) {
      document.getElementById(tableDescriptionId).innerHTML = "";
    } else {
      const selectedOption = backgroundData[backgroundField.value][`table${table}`].options[value - 1];
      document.getElementById(tableDescriptionId).innerHTML = selectedOption.description;
      addTableItems(selectedOption.items, `table_${table}`);
      if (selectedOption.bonus_gold) {
        if (table === 1) {
          table1gold = selectedOption.bonus_gold;
        } else {
          table2gold = selectedOption.bonus_gold;
        }
      }
      if (selectedOption.containers) {
        addTableContainers(selectedOption.containers, addedBy);
      }
      if (selectedOption.gear_table) {
        marketplace.clearSelection();
        if (table === 1) {
          gearTable1Gold = selectedOption.gear_table;
        } else {
          gearTable2Gold = selectedOption.gear_table;
        }
        marketplace.setGold(selectedOption.gear_table);

        if (table === 1) {
          document.getElementById("show-gear-table-1").classList.remove("hidden");
        } else {
          document.getElementById("show-gear-table-2").classList.remove("hidden");
        }
      } else {
        if (table === 1) {
          document.getElementById("show-gear-table-1").classList.add("hidden");
        } else {
          document.getElementById("show-gear-table-2").classList.add("hidden");
        }
      }
    }
    updateGold();
  };

  backgroundTable1.addEventListener("change", () => {
    handleTableResults(1);
    inventoryUI.refreshInventory();
    // showHideMarketplaceButton();
  });

  backgroundTable2.addEventListener("change", () => {
    handleTableResults(2);
    // showHideMarketplaceButton();
  });

  //
  // ____________________ Attributes ____________________
  //

  const checkAttributesAndActivateSwap = () => {
    if (strengthField.value && dexterityField.value && willpowerField.value) {
      // Remove the 'inactive' class from the swap-container div
      document.getElementById("swap-container").classList.remove("inactive");
    }
  };

  strengthField.addEventListener("input", checkAttributesAndActivateSwap);
  dexterityField.addEventListener("input", checkAttributesAndActivateSwap);
  willpowerField.addEventListener("input", checkAttributesAndActivateSwap);

  swapButton.addEventListener("click", function () {
    // Get the selected attributes and convert them to lower case
    const attribute1 = document.getElementById("swap-attribute-1").value.toLowerCase();
    const attribute2 = document.getElementById("swap-attribute-2").value.toLowerCase();

    // If either of the attributes is not selected, return
    if (!attribute1 || !attribute2 || attribute1 === attribute2) {
      return;
    }

    // Build the IDs of the corresponding max fields
    const attribute1FieldId = attribute1 + "-max-field";
    const attribute2FieldId = attribute2 + "-max-field";

    // Get the input fields of the selected attributes
    const attribute1Field = document.getElementById(attribute1FieldId);
    const attribute2Field = document.getElementById(attribute2FieldId);

    // Check if the fields exist
    if (!attribute1Field || !attribute2Field) return;

    // Swap the values
    const temp = attribute1Field.value;
    attribute1Field.value = attribute2Field.value;
    attribute2Field.value = temp;

    // Add the 'inactive' class to the swap button
    swapButton.classList.add("inactive");
  });

  //
  // ____________________ Traits ____________________
  //

  let traits = traitsData;
  const traitsDescription = document.getElementById("traits-description");

  for (const trait in traits) {
    if (traits.hasOwnProperty(trait)) {
      const selectBox = document.getElementById(trait);
      if (selectBox) {
        // Clear out any existing options
        selectBox.innerHTML = "";

        // Add a placeholder option
        addOptionToSelect(selectBox, "", `${trait} (d10)...`, true, true);

        // Populate the select box with new options
        traits[trait].forEach((optionValue) => {
          addOptionToSelect(selectBox, optionValue, optionValue);
        });
      } else {
        console.warn(`No select box found for trait: ${trait}`);
      }
    }
  }

  const updateTraitsDescription = () => {
    const traits = [];
    const traitSelects = document.querySelectorAll(".trait-select");

    traitSelects.forEach((select) => {
      const traitName = select.id.toLowerCase();
      const selectedOption = select.options[select.selectedIndex];
      const isPlaceholder = selectedOption.disabled && selectedOption.selected;
      const traitValue = isPlaceholder ? "_____" : selectedOption.text.toLowerCase();
      traits.push({ name: traitName, value: traitValue });
    });

    const traitsText = `You have a ${traits[0].value} ${traits[0].name}, ${traits[1].value} ${traits[1].name}, and ${traits[2].value} ${traits[2].name}. Your ${traits[3].name} is ${traits[3].value}, your ${traits[4].name} ${traits[4].value}. You have ${traits[5].value} ${traits[5].name}. You are ${traits[6].value} and ${traits[7].value}.`;

    traitsDescription.innerHTML = traitsText;
  };

  const addChangeListenerToTraitSelects = () => {
    const traitSelects = document.querySelectorAll(".trait-select");
    traitSelects.forEach((select) => {
      select.addEventListener("change", updateTraitsDescription);
    });
  };

  addChangeListenerToTraitSelects();

  //
  // ____________________ Bonds Age Omens ____________________
  //

  const bondsOmensDescription = document.getElementById("bonds-omens-description");
  const bondsSelect = document.getElementById("bonds-select");
  const omensSelect = document.getElementById("omens-select");

  const updateBondsOmensDescription = () => {
    bondsOmensDescription.innerHTML = `${bondsSelect.value}<br><br>${omensSelect.value}`;
    document.getElementById("bonds-hidden-field").value = bondsSelect.value;
    document.getElementById("omens-hidden-field").value = omensSelect.value;
  };

  const truncateText = (text, length, ending) => {
    return text.length > length ? text.substring(0, length) + ending : text;
  };

  const addBondsOmensOptions = (data, selectElement) => {
    data.forEach((item, index) => {
      addOptionToSelect(selectElement, item.description, truncateText(item.description, 60, "..."));
    });
  };

  // Populate select options
  addBondsOmensOptions(bondsData.Bonds, bondsSelect);
  addBondsOmensOptions(omensData.Omens, omensSelect);

  const handleBondsResult = (index) => {
    bondsGold = 0;
    const data = bondsData.Bonds[index - 1];
    if (data && data.items) {
      removeItemsContainersByField("bonds");
      data.items.forEach((item) => inventory.addItem({ ...item, added_by: "bonds" }));
      inventoryUI.refreshInventory();
    }
    if (data && data.gold) {
      bondsGold = data.gold;
    }
    updateGold();
    updateBondsOmensDescription();
  };

  const handleOmensResult = () => {
    updateBondsOmensDescription();
  };

  bondsSelect.addEventListener("change", () => {
    console.log(bondsSelect.selectedIndex);
    handleBondsResult(bondsSelect.selectedIndex);
  });

  omensSelect.addEventListener("change", () => {
    handleOmensResult();
  });

  //
  // ____________________ Notes ____________________
  //

  const notes = document.getElementById("notes-hidden-field");

  const updateNotes = () => {
    notes.value = "";
    if (background !== "Custom") {
      const table1question = document.getElementById("table1-question").innerHTML;
      const table1description = document.getElementById("background-table1-description").innerHTML;
      const table2question = document.getElementById("table2-question").innerHTML;
      const table2description = document.getElementById("background-table2-description").innerHTML;

      notes.value = `${table1question}\n${table1description}\n\n${table2question}\n${table2description}`;
      console.log(notes.value);
    }
  };

  //
  // ____________________ Roll Functions ____________________
  //

  const rollField = (target) => {
    let randomValue = 0;

    switch (target) {
      case "background":
        resetInventory();
        gold = 0;
        updateGold();
        const numberOfBackgrounds = Object.keys(backgroundData).length;
        randomValue = roll(1, numberOfBackgrounds);
        background = backgroundField.value;
        utils.selectOptionByIndex(backgroundField, randomValue);
        toggleCustomBackground(false);
        populateNames(backgroundField.value);
        populateTables(backgroundField.value);
        setBackgroundDescription(backgroundField.value);
        addStartingContainers(backgroundField.value);
        addStartingItems(backgroundField.value);
        handleBondsResult(bondsSelect.selectedIndex);

        break;
      case "name":
        randomValue = roll(1, 10);
        utils.selectOptionByIndex(nameField, randomValue);
        break;
      case "table1":
        randomValue = roll(1, 6);
        utils.selectOptionByIndex(backgroundTable1, randomValue);
        handleTableResults(1);
        break;
      case "table2":
        randomValue = roll(1, 6);
        utils.selectOptionByIndex(backgroundTable2, randomValue);
        handleTableResults(2);
        break;
      case "strength":
        randomValue = roll(3, 6);
        strengthField.value = randomValue;
        checkAttributesAndActivateSwap();
        break;
      case "dexterity":
        randomValue = roll(3, 6);
        dexterityField.value = randomValue;
        checkAttributesAndActivateSwap();
        break;
      case "willpower":
        randomValue = roll(3, 6);
        willpowerField.value = randomValue;
        checkAttributesAndActivateSwap();
        break;
      case "hp":
        randomValue = roll(1, 6);
        hpField.value = randomValue;
        break;
      case "traits":
        const traitSelects = document.querySelectorAll(".trait-select");
        traitSelects.forEach((select) => {
          randomValue = roll(1, 10);
          utils.selectOptionByIndex(select, randomValue);
        });
        updateTraitsDescription();
        break;
      case "bonds":
        randomValue = roll(1, 10);
        utils.selectOptionByIndex(bondsSelect, randomValue);
        handleBondsResult(bondsSelect.selectedIndex);
        break;
      case "omens":
        randomValue = roll(1, 10);
        utils.selectOptionByIndex(omensSelect, randomValue);
        handleOmensResult();
        break;
      case "age":
        randomValue = roll(2, 20) + 10;
        ageField.value = randomValue;
        break;
      case "gold":
        randomValue = roll(3, 6);
        gold = randomValue;
        updateGold();
        break;
    }
  };

  const rollAll = () => {
    omensSelect.selectedIndex = 0;
    updateBondsOmensDescription();
    resetGold();

    const fields = [
      "background",
      "name",
      "table1",
      "table2",
      "strength",
      "dexterity",
      "willpower",
      "hp",
      "traits",
      "bonds",
      "age",
      "gold",
    ];
    fields.forEach(rollField);
    portraitModal.rollPortrait();
  };

  const rollRemaining = () => {
    const fieldsToRoll = [
      { field: "background", condition: () => backgroundField.value == "" },
      { field: "name", condition: () => nameField.value == "" },
      { field: "table1", condition: () => backgroundTable1.selectedIndex == 0 },
      { field: "table2", condition: () => backgroundTable2.selectedIndex == 0 },
      { field: "strength", condition: () => strengthField.value == "" },
      { field: "dexterity", condition: () => dexterityField.value == "" },
      { field: "willpower", condition: () => willpowerField.value == "" },
      { field: "hp", condition: () => hpField.value == "" },
      {
        field: "traits",
        condition: () => document.getElementById("traits-description").innerHTML == "",
      },
      { field: "bonds", condition: () => bondsSelect.selectedIndex == 0 },
      {
        field: "age",
        condition: () => document.getElementById("age-field").value == "",
      },
      { field: "gold", condition: () => gold == 0 },
      portraitModal.getUserSelected()
        ? { field: "portrait", condition: () => false }
        : { field: "portrait", condition: () => true },
    ];

    fieldsToRoll.forEach(({ field, condition }) => {
      if (condition()) {
        rollField(field);
      }
    });

    if (!portraitModal.getUserSelected()) {
      portraitModal.rollPortrait();
    }
  };

  // Event listeners for roll buttons
  document.querySelectorAll(".roll").forEach((btn) => {
    btn.addEventListener("click", () => rollField(btn.getAttribute("data-target")));
  });
  document.getElementById("roll-all").addEventListener("click", rollAll);
  document.getElementById("roll-remaining").addEventListener("click", rollRemaining);

  //
  // ____________________ Submit Actions ____________________
  //

  document.getElementById("character-form").addEventListener("submit", function (event) {
    document.getElementById("gold-hidden-field").value = gold + bonusGold;
    document.getElementById("description-hidden-field").value = description;
    document.getElementById("traits-hidden-field").value =
      `You are ${ageField.value} years old. ` + traitsDescription.innerHTML;

    document.querySelector('input[name="items"]').value = JSON.stringify(inventory.getItems());
    const containers = inventory.getContainers();
    document.querySelector('input[name="containers"]').value = JSON.stringify(containers);
    document.getElementById("custom-image").value = portraitModal.getCustomImage();
    document.getElementById("custom-image-url").value = portraitModal.getImageURL();
    document.getElementById("armor-hidden-field").value = document.getElementById("armor-counter").textContent;
    updateNotes();
  });
});

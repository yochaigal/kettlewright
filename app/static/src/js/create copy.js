import utils from "./utils.js";
import inventory from "./inventoryData.js";
import inventoryUI from "./inventoryUI.js";
import inventoryModalUI from "./inventoryModalUI.js";
import portraitModal from "./edit_portrait_modal.js";
import marketplace from "./marketplace.js";

inventoryUI.initialize();
inventoryModalUI.initialize();
const marketplaceButton = document.getElementById("show-marketplace-button");
marketplaceButton.addEventListener("click", () => marketplace.showMarketplace());
// create a deep copy of the background data
let backgroundDataCopy = JSON.parse(JSON.stringify(backgroundData));
let description = "";
let background = "";
let gold = 0;
let bonusGold = 0;
let gearTable = false;
document.getElementById("gold-field").textContent = gold;

function resetInventory() {
  backgroundDataCopy = JSON.parse(JSON.stringify(backgroundData)); // reset the background data
  inventory.resetInventory();
}

document.addEventListener("DOMContentLoaded", function () {
  const backgroundField = document.getElementById("background-field");
  const customBackgroundField = document.getElementById("custom-background-field");
  const backgroundTablesContainer = document.getElementById("background-tables-container");
  const backgroundTable1 = document.getElementById("background-table1-select");
  const backgroundTable2 = document.getElementById("background-table2-select");
  const table1Description = document.getElementById("background-table1-description");
  const table2Description = document.getElementById("background-table2-description");
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

  function setBackgroundDescription(background) {
    const backgroundDescription = document.getElementById("create-background-description");
    description = backgroundDataCopy[background] ? backgroundDataCopy[background].background_description : "";

    backgroundDescription.innerHTML = description;
  }

  function addStartingItems(background) {
    if (background !== "Custom" && backgroundDataCopy[background].starting_gear) {
      for (let item of backgroundDataCopy[background].starting_gear) {
        if (
          !backgroundDataCopy[background].background_items[item] ||
          !backgroundDataCopy[background].background_items[item].description
        ) {
          backgroundDataCopy[background].background_items[item] = {
            ...backgroundDataCopy[background].background_items[item],
            description: "This item has no description...",
          };
        }

        let startingItem = backgroundDataCopy[background].background_items[item];
        startingItem.name = item;
        startingItem.location = 0;

        inventory.addItem(startingItem);
      }
    }
    inventoryUI.refreshInventory();
  }

  function addContainer(container) {
    inventory.addContainer(container);
    inventory.convertCarriedByToID();
    inventoryUI.setActiveContainer(0);
  }

  function addStartingContainers(background) {
    if (background !== "Custom" && backgroundDataCopy[background].starting_containers) {
      for (let container of backgroundDataCopy[background].starting_containers) {
        addContainer(container);
      }
    }
  }

  function populateNames(background) {
    const nameSelect = document.getElementById("name-field");
    const names = (backgroundDataCopy[background] && backgroundDataCopy[background].names) || [];

    // Clear previous options
    nameSelect.innerHTML = "";
    // Add placeholder
    addOptionToSelect(nameSelect, "", "Name (d10)...", true, true);
    // Add names
    names.forEach((name) => {
      addOptionToSelect(nameSelect, name, name);
    });

    addOptionToSelect(nameSelect, "Custom", "** Custom **");
  }
  backgroundField.addEventListener("change", () => {
    background = backgroundField.value;
    populateNames(background);
    setBackgroundDescription(background);
    setBackgroundTables(background);
    addStartingContainers(background);
    addStartingItems(background);

    if (background == "Custom") {
      toggleCustomBackground(true);
    } else {
      toggleCustomBackground(false);
    }
    setTables();
  });

  nameField.addEventListener("change", () => {
    if (nameField.value == "Custom") {
      customNameField.classList.remove("inactive");
    } else {
      customNameField.classList.add("inactive");
    }
  });

  document.getElementById("submit-button").addEventListener("click", function (event) {
    if (backgroundField.value != "Custom") {
      customBackgroundField.value = "none";
    }
    if (nameField.value != "Custom") {
      customNameField.value = "none";
    }
  });

  //
  // ____________________ Edit Portrait ____________________
  //

  portraitModal.initialize("create");
  document.getElementById("create-portrait-container").addEventListener("click", () => {
    portraitModal.openModal();
  });

  //
  // ____________________ Background Tables ____________________
  //

  // Setup selcts with options
  function setupTable(tableElement, tableData, descriptionElementId, questionElementId) {
    tableElement.innerHTML = "";
    // Add Placeholder
    addOptionToSelect(tableElement, "", "Table (d6)...", true, true);
    // Change the title to the question
    document.getElementById(questionElementId).innerHTML = tableData.question;
    // Add options to the table
    tableData.options.forEach((option) => {
      addOptionToSelect(tableElement, option.description, truncateText(option.description, 36, "..."));
    });
  }

  // Clear Table textboxes and add questions
  function setBackgroundTables(background) {
    if (background !== "Custom") {
      table1Description.innerHTML = "";
      table2Description.innerHTML = "";

      setupTable(
        backgroundTable1,
        backgroundDataCopy[background].table1,
        "background-table1-description",
        "table1-question"
      );
      setupTable(
        backgroundTable2,
        backgroundDataCopy[background].table2,
        "background-table2-description",
        "table2-question"
      );
    }
  }

  function addBackgroundItems(items, background) {
    if (items) {
      for (let item of items) {
        let fullItem = backgroundDataCopy[background].background_items[item];

        if (fullItem) {
          fullItem.name = item;
          fullItem.location = 0;
          inventory.addItem(fullItem);
        } else {
          console.log("item not found: ", item);
        }
      }
    }
    inventoryUI.refreshInventory();
  }

  function updateGold(newGold, newBonusGold) {
    gold = newGold;
    bonusGold = newBonusGold;
    document.getElementById("gold-field").textContent = bonusGold > 0 ? `${gold} + ${bonusGold}` : gold;
  }

  function setTables() {
    // Reset inventory and add back starting items
    resetInventory();
    updateGold(gold, 0);
    marketplaceButton.classList.add("hidden");
    gearTable = false;

    if (backgroundField.value === "Custom") {
      return;
    }

    addStartingContainers(backgroundField.value);
    addStartingItems(backgroundField.value);

    function processTableSelection(value, tableNumber) {
      const tableDescriptionId = `background-table${tableNumber}-description`;
      if (value === 0) {
        document.getElementById(tableDescriptionId).innerHTML = "";
      } else {
        const selectedOption = backgroundDataCopy[backgroundField.value][`table${tableNumber}`].options[value - 1];
        document.getElementById(tableDescriptionId).innerHTML = selectedOption.description;
        addBackgroundItems(selectedOption.items, backgroundField.value);
        if (selectedOption.bonus_gold) {
          updateGold(gold, bonusGold + selectedOption.bonus_gold);
        }
        if (selectedOption.containers) {
          addTableContainers(selectedOption.containers);
        }
        if (selectedOption.gear_table) {
          gearTable = true;
          marketplace.initialize(marketplaceData, "gear", selectedOption.gear_table, (items) =>
            inventory.addItems(items)
          );
        }
      }
    }

    // Helper function to add containers
    function addTableContainers(containers) {
      containers.forEach((container) => addContainer(container));
    }

    processTableSelection(backgroundTable1.selectedIndex, 1);
    processTableSelection(backgroundTable2.selectedIndex, 2);

    if (gearTable) {
      marketplaceButton.classList.remove("hidden");
    }
  }

  backgroundTable1.addEventListener("change", () => {
    setTables();
  });

  backgroundTable2.addEventListener("change", () => {
    setTables();
  });

  //
  // ____________________ Attributes ____________________
  //

  function checkAttributesAndActivateSwap() {
    if (strengthField.value && dexterityField.value && willpowerField.value) {
      // Remove the 'inactive' class from the swap-container div
      document.getElementById("swap-container").classList.remove("inactive");
    }
  }

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
  let traitsDescription = document.getElementById("traits-description");

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

  function updateTraitsDescription() {
    const traits = [];
    const traitSelects = document.querySelectorAll(".trait-select");

    traitSelects.forEach((select) => {
      const traitName = select.id.toLowerCase();
      const selectedOption = select.options[select.selectedIndex];
      const isPlaceholder = selectedOption.disabled && selectedOption.selected;
      const traitValue = isPlaceholder ? "_____" : selectedOption.text.toLowerCase();
      traits.push({ name: traitName, value: traitValue });
    });

    const description =
      `You have a ${traits[0].value} ${traits[0].name}, ${traits[1].value} ${traits[1].name}, and ${traits[2].value} ${traits[2].name}. ` +
      `Your ${traits[3].name} is ${traits[3].value}, your ${traits[4].name} ${traits[4].value}. ` +
      `You have ${traits[5].value} ${traits[5].name}. ` +
      `You are ${traits[6].value} and ${traits[7].value}.`;

    traitsDescription.innerHTML = description;
  }

  function addChangeListenerToTraitSelects() {
    const traitSelects = document.querySelectorAll(".trait-select");
    traitSelects.forEach((select) => {
      select.addEventListener("change", updateTraitsDescription);
    });
  }

  addChangeListenerToTraitSelects();

  //
  // ____________________ Bonds Age Omens ____________________
  //

  const bondsOmensDescription = document.getElementById("bonds-omens-description");
  let bondsDescription = "";
  let omensDescription = "";

  function updateBondsOmensDescription() {
    bondsOmensDescription.innerHTML = `${bondsDescription}<br><br>${omensDescription}`;
    document.getElementById("bonds-hidden-field").value = bondsSelect.value;
    document.getElementById("omens-hidden-field").value = omensSelect.value;
  }

  function truncateText(text, length, ending) {
    return text.length > length ? text.substring(0, length) + ending : text;
  }

  function addSelectEventListener(selectElement, descriptionSetter, indexSetter) {
    selectElement.addEventListener("change", () => {
      descriptionSetter(selectElement.value);
      updateBondsOmensDescription();
      addItemsOrGold(indexSetter(selectElement.selectedIndex), selectElement.id);
    });
  }
  function addMultipleOptionsToSelect(data, selectElement) {
    data.forEach((item, index) => {
      addOptionToSelect(selectElement, item.description, truncateText(item.description, 60, "..."));
    });
  }

  // Add bonds or omens items or gold
  function addItemsOrGold(index, type) {
    const data = type === "bonds-select" ? bondsData.Bonds[index - 1] : omensData.Omens[index - 1];
    if (data.items) {
      data.items.forEach((item) => inventory.addItem(item));
    }
    if (data.gold) {
      updateGold(gold, bonusGold + data.gold);
    }
  }

  // Setup event listeners
  const bondsSelect = document.getElementById("bonds-select");
  const omensSelect = document.getElementById("omens-select");

  addSelectEventListener(
    bondsSelect,
    (value) => (bondsDescription = value),
    (index) => index
  );
  addSelectEventListener(
    omensSelect,
    (value) => (omensDescription = value),
    (index) => index
  );

  // Populate select options
  addMultipleOptionsToSelect(bondsData.Bonds, bondsSelect);
  addMultipleOptionsToSelect(omensData.Omens, omensSelect);

  //
  // ____________________ Notes ____________________
  //

  const notes = document.getElementById("notes-hidden-field");

  function updateNotes() {
    notes.value = "";
    if (background !== "Custom") {
      const table1question = document.getElementById("table1-question").innerHTML;
      const table1description = document.getElementById("background-table1-description").innerHTML;
      const table2question = document.getElementById("table2-question").innerHTML;
      const table2description = document.getElementById("background-table2-description").innerHTML;

      notes.value = `${table1question}\n${table1description}\n\n${table2question}\n${table2description}`;
      console.log(notes.value);
    }
  }

  //
  // ____________________ Roll Functions ____________________
  //

  function rollField(target) {
    let randomValue = 0;

    switch (target) {
      case "background":
        resetInventory();
        updateGold(0, 0);
        const numberOfBackgrounds = Object.keys(backgroundDataCopy).length;
        randomValue = roll(1, numberOfBackgrounds);
        background = backgroundField.value;
        utils.selectOptionByIndex(backgroundField, randomValue);
        toggleCustomBackground(false);
        populateNames(backgroundField.value);
        setBackgroundTables(backgroundField.value);
        setBackgroundDescription(backgroundField.value);
        addStartingContainers(backgroundField.value);
        addStartingItems(backgroundField.value);

        setTables();
        break;
      case "name":
        randomValue = roll(1, 10);
        utils.selectOptionByIndex(nameField, randomValue);
        break;
      case "table1":
        randomValue = roll(1, 6);
        utils.selectOptionByIndex(backgroundTable1, randomValue);
        setTables();
        break;
      case "table2":
        randomValue = roll(1, 6);
        utils.selectOptionByIndex(backgroundTable2, randomValue);
        setTables();
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
        bondsDescription = bondsSelect.value;
        updateBondsOmensDescription();
        addItemsOrGold(bondsSelect.selectedIndex, bondsSelect.id);
        break;
      case "omens":
        randomValue = roll(1, 10);
        utils.selectOptionByIndex(omensSelect, randomValue);
        omensDescription = omensSelect.value;
        updateBondsOmensDescription();
        addItemsOrGold(omensSelect.selectedIndex, omensSelect.id);
        break;
      case "age":
        randomValue = roll(2, 20) + 10;
        ageField.value = randomValue;
        break;
      case "gold":
        randomValue = roll(3, 6);
        gold = randomValue;
        updateGold(gold, bonusGold);
        break;
    }
  }

  const rollAll = () => {
    omensSelect.selectedIndex = 0;
    omensDescription = "";
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
        console.log(`Rolled ${field}`);
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
  document.getElementById("reset-button").addEventListener("click", function () {
    if (confirm("Reset Character?")) {
      window.location.reload(); // Reloads the current page
    }
  });

  //
  // ____________________ Submit Actions ____________________
  //

  document.getElementById("character-form").addEventListener("submit", function (event) {
    document.getElementById("gold-hidden-field").value = gold + bonusGold;
    // description += `<br><br>You are ${ageField.value} years old. ${traitsDescription.innerHTML}`;
    document.getElementById("description-hidden-field").value = description;
    document.getElementById("traits-hidden-field").value =
      `You are ${ageField.value} years old. ` + traitsDescription.innerHTML;
    const items = inventory.getItems();
    document.querySelector('input[name="items"]').value = JSON.stringify(items);
    const containers = inventory.getContainers();
    document.querySelector('input[name="containers"]').value = JSON.stringify(containers);
    document.getElementById("custom-image").value = portraitModal.getCustomImage();
    document.getElementById("custom-image-url").value = portraitModal.getImageURL();
    document.getElementById("armor-hidden-field").value = document.getElementById("armor-counter").textContent;
    updateNotes();
  });
});

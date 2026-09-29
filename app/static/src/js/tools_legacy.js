import {generateWorldbuilding} from './worldbuilding.js';
import {resultText} from './content_generators.js';
import {richContentHTML} from './rich-content.js';
// Pre-campaign Tools retained while the experimental generator is allowlisted.
import utils, { handleClick, styledAlert } from "./utils.js";

window.KW_alert = utils.styledAlert;

const toolTabs = [...document.querySelectorAll(".tools-tab-list [role=tab]")];
const selectToolTab = (selected) => {
  toolTabs.forEach((tab) => {
    const active = tab === selected;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden = !active;
  });
};
toolTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectToolTab(tab));
  tab.addEventListener("keydown", (event) => {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % toolTabs.length;
    if (event.key === "ArrowLeft") next = (index + toolTabs.length - 1) % toolTabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = toolTabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    selectToolTab(toolTabs[next]);
    toolTabs[next].focus();
  });
});

const categoryButtons = document.getElementById("category-buttons");
const subcategoryButtons = document.getElementById("subcategory-buttons");
let selectedCategory = "";
let selectedSubcategory = "";
const rollButton = document.getElementById("roll-button");

const categories = {
  Monsters: {
    "Random Monster": data["Random Monster"],
    "Custom Monster": data["Custom Monster"],
    "Reaction Roll": data["Reaction Roll"],
  },
  Events: {
    "Dungeon Events": data["Dungeon Events"],
    "Wilderness Events": data["Wilderness Events"],
  },
  Weather: data.Weather.Types,
  // Names: data.Names.NameFormulas,
  Worldbuilding: {
    Dungeon: data.Dungeon,
    Forest: data.Forest,
    Realm: data.Realm,
    Faction: data.FactionGenerator,
    "Faction Actions": data.FactionActions,
    NPC: data.NPCGenerator,
  },
  Items: {
    Relics: data.Relics,
    Spellbooks: data.Spellbooks,
  },
};

// Keep every choice visible and expose the current selection to keyboard and screen-reader users.
const addChoiceButtons = (choices, element, onSelect) => {
  element.replaceChildren();
  Object.keys(choices).forEach((key) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "button tools-choice";
    button.textContent = key;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      element.querySelectorAll("button").forEach((choice) => {
        choice.setAttribute("aria-pressed", String(choice === button));
      });
      onSelect(key);
    });
    element.appendChild(button);
  });
};

addChoiceButtons(categories, categoryButtons, (category) => {
  selectedCategory = category;
  document.getElementById("selected-category-label").textContent = ` · ${category}`;
  document.getElementById("table-choice-hint").hidden = true;
  selectedSubcategory = "";
  rollButton.disabled = true;
  addChoiceButtons(categories[category], subcategoryButtons, (subcategory) => {
    selectedSubcategory = subcategory;
    rollButton.disabled = false;
  });
});

rollButton.addEventListener("click", () => {
  const category = selectedCategory;
  const subcategory = selectedSubcategory;
  if (!category || !subcategory) return;

  switch (category) {
    case "Monsters":
      rollMonsters(categories.Monsters, subcategory);
      break;
    case "Events":
      rollEvents(categories.Events, subcategory);
      break;
    case "Weather":
      rollWeather(data.Weather, subcategory);
      break;
    case "Realm":
      rollRealm(categories.Realm, subcategory);
      break;
    case "Worldbuilding":
      rollWorldbuilding(categories["Worldbuilding"], subcategory);
      break;
    case "Items":
      rollRelics(categories.Items, subcategory);
      break;
  }
});

const clearResults = () => {
  const resultDisplay = document.getElementById("tools-result-display");
  resultDisplay.innerHTML = "";
};

const clearButton = document.getElementById("clear-button");
clearButton.addEventListener("click", clearResults);

const copyButton = document.getElementById("tools-copy-text-button");

handleClick("#tools-copy-text-button", (event, element) => {
  const resultDisplay = document.getElementById("tools-result-display");
  const text = resultDisplay.innerText;
  navigator.clipboard.writeText(text);
  styledAlert("Copy text", "Results copied to clipboard");
});

const roll = (sides) => {
  return Math.floor(Math.random() * sides);
};

// Output formatting functions
const formatObjectToString = (obj) => {
  return Object.entries(obj)
    .filter(([key, value]) => !(Array.isArray(value) && value.length === 0))
    .map(([key, value]) => {
      let formattedValue = Array.isArray(value) ? value.join(", ") : value;
      return `<b>${key}:</b> ${formattedValue}`;
    })
    .join("<br>");
};

const formatNumberedArrayToString = (arr) => {
  return arr.map((item, index) => `${index + 1}. ${item}`).join("<br>");
};

const convertName = (nameFormula, replacements) => {
  let name = nameFormula;

  replacements.forEach(({ type, word }) => {
    const regex = new RegExp(`\\[${type}\\]`, "g");
    name = name.replace(regex, word);
  });

  // Remove optional parts if their content wasn't replaced
  name = name.replace(/\([^()]*\[.*?\][^()]*\)/g, "");
  // Remove any remaining brackets
  name = name.replace(/[\[\]()]/g, "");
  // Trim any extra spaces
  return name.trim().replace(/\s+/g, " ");
};

const displayResult = (result) => {
  const resultDisplay = document.getElementById("tools-result-display");
  const line = "------------------------------------<br>";
  if (resultDisplay.innerHTML === "no events yet...") {
    resultDisplay.innerHTML = result + "<br><br>" + line;
  } else {
    resultDisplay.innerHTML =
      `<p>${result}</p>` + line + resultDisplay.innerHTML;
  }
  resultDisplay.scrollTop = 0;
};

// Roll functions
const rollMonsters = (data, subcategory) => {
  const Monsters = data[subcategory];
  if (subcategory === "Random Monster") {
    const result = Monsters[roll(Monsters.length)];
    const formattedTraits = result.Traits.map((trait) =>
      trait.replace(/Critical Damage/g, "<b>Critical Damage</b>")
    );
    const textResult = `<b><u>${result.Name}</u></b><br><br>HP: ${result.HP}, ${
      result.Armor ? `Armor: ${result.Armor},` : ""
    } STR: ${result.STR}, DEX: ${result.DEX}, WIL: ${result.WIL}${
      result.Attack ? `, ${result.Attack}<br><br>` : ""
    }• ${formattedTraits.join("<br>• ")}`;
    displayResult(textResult);
  } else if (subcategory === "Custom Monster") {
    const physique =
      Monsters.MonsterAppearance.Physique[
        roll(Monsters.MonsterAppearance.Physique.length)
      ];
    const feature =
      Monsters.MonsterAppearance.Feature[
        roll(Monsters.MonsterAppearance.Feature.length)
      ];
    const quirks =
      Monsters.MonsterTraits.Quirks[roll(Monsters.MonsterTraits.Quirks.length)];
    const weakness =
      Monsters.MonsterTraits.Weakness[
        roll(Monsters.MonsterTraits.Weakness.length)
      ];
    const attack =
      Monsters.MonsterAttacks.Type[roll(Monsters.MonsterAttacks.Type.length)];
    const criticalDamage =
      Monsters.MonsterAttacks.CriticalDamage[
        roll(Monsters.MonsterAttacks.CriticalDamage.length)
      ];
    const ability =
      Monsters.MonsterAbilities.Ability[
        roll(Monsters.MonsterAbilities.Ability.length)
      ];
    const target =
      Monsters.MonsterAbilities.Target[
        roll(Monsters.MonsterAbilities.Target.length)
      ];
    const textResult = `<b><u>Custom Monster</u></b><br><br><b>Physique:</b> ${physique}<br><b>Feature:</b> ${feature}<br><b>Quirks:</b> ${quirks}<br><b>Weakness:</b> ${weakness}<br><b>Attack:</b> ${attack}<br><b>Critical Damage:</b> ${criticalDamage}<br><b>Ability:</b> ${ability}<br><b>Target:</b> ${target}`;
    displayResult(textResult);
  } else if (subcategory === "Reaction Roll") {
    let roll = utils.roll(2, 6);
    const result = Monsters[roll - 2]; //2-12 -> 0-10
    const textResult = `<b><u>Reaction Roll</u></b><br><br><b>${result}</b>`;
    displayResult(textResult);
  }
};

const rollEvents = (data, subcategory) => {
  const events = data[subcategory];
  if (subcategory === "Dungeon Events") {
    const result = events[roll(events.length)];
    const textResult = `<b><u>Dungeon Event</u></b><br><br>${result.description}`;
    displayResult(textResult);
  } else if (subcategory === "Wilderness Events") {
    const result = events[roll(events.length)];
    const textResult = `<b><u>Wilderness Event</u></b><br><br>${result.description}`;
    displayResult(textResult);
  }
};

const rollWeather = (data, subcategory) => {
  console.log(data);
  const weather = data.Types[subcategory];
  const type = weather[roll(weather.length)];
  console.log(type);
  const difficulty = data.Difficulty[type];
  const textResult = `<b><u>Weather</u></b><br><br><b>Season:</b> ${subcategory}<br><b>Type:</b> ${type}<br><b>Effect:</b> ${difficulty.Effect} <br><b>Examples:</b> ${difficulty.Examples}`;
  displayResult(textResult);
};

const rollRelics = (data, subcategory) => {
  const items = data[subcategory];
  const result = items[roll(items.length)];
  let name = result.name;
  let weight = "";
  if (result.tags.includes("petty")) {
    weight = " (petty)";
  } else if (result.tags.includes("bulky")) {
    weight = " (bulky)";
  }

  let tags = [];

  // Filter and add regular tags
  const regularTags = result.tags.filter(
    (tag) =>
      !["bulky", "petty", "uses", "charges", "use", "charge"].includes(tag)
  );
  if (regularTags.length > 0) {
    tags.push(regularTags.join(", "));
  }

  // Add uses if present
  if (result.uses) {
    tags.push(`${result.uses} use${result.uses > 1 ? "s" : ""}`);
  }

  // Add charges if present
  if (result.max_charges) {
    tags.push(
      `${result.max_charges} charge${result.max_charges > 1 ? "s" : ""}`
    );
  }

  // Join all tags with proper comma placement
  const tagsString = tags.length > 0 ? `, ${tags.join(", ")}` : "";

  // Format description, splitting on "Recharge" and making only "Recharge" bold
  let descriptionText = "";
  if (result.description) {
    const parts = result.description.split(/(Recharge)/);
    descriptionText = parts
      .map((part, index) => {
        if (part === "Recharge") {
          return `<br>• <b>Recharge</b>`;
        } else if (index === 0) {
          return `• ${part}`;
        } else if (index % 2 === 0) {
          // Even indexes after 0 are text following "Recharge"
          return part;
        }
        return part; // This line should never be reached, but it's here for completeness
      })
      .join("");
  }

  // Add personality if it exists
  if (result.personality) {
    descriptionText += descriptionText ? "<br>" : ""; // Add a line break if there's already a description
    descriptionText += `• Personality: ${result.personality}`;
  }

  const textResult = `<b><u>${name}</u></b>${tagsString}<i>${weight}</i><br><br>${descriptionText}`;

  displayResult(textResult);
};

const rollWorldbuilding = (data, subcategory) => {
  const result=generateWorldbuilding(data,subcategory);
  displayResult(richContentHTML(`## ${result.title}\n\n${resultText(result)}`));
};

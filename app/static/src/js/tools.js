import utils, { styledAlert } from "./utils.js";
import {generateResult, localizeText, resultText} from "./content_generators.js";
import {richContentHTML} from "./rich-content.js";

window.KW_alert = utils.styledAlert;

const labels = JSON.parse(document.getElementById('tools-content-labels').textContent);
// Choice values stay English: they are lookup keys into the table data.
const t = (key) => Object.hasOwn(labels.terms, key) ? labels.terms[key] : key;

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
    button.textContent = t(key);
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
  document.getElementById("selected-category-label").textContent = ` · ${t(category)}`;
  document.getElementById("table-choice-hint").hidden = true;
  selectedSubcategory = "";
  rollButton.disabled = true;
  addChoiceButtons(categories[category], subcategoryButtons, (subcategory) => {
    selectedSubcategory = subcategory;
    rollButton.disabled = false;
  });
});


const resultDisplay = document.getElementById('tools-result-display');
rollButton.addEventListener('click', () => {
  if (!selectedCategory || !selectedSubcategory) return;
  const result = generateResult(data, selectedCategory, selectedSubcategory);
  const card = document.createElement('article');
  card.className = 'tools-generated-result';
  const shownTitle = localizeText(result.title, t);
  const title = document.createElement('h3'); title.textContent = shownTitle;
  const markdown = resultText(result, t);
  card.dataset.copyText = `${shownTitle}\n\n${markdown}`;
  const body = document.createElement('div'); body.className = 'rich-content'; body.innerHTML = richContentHTML(markdown);
  card.append(title, body);
  if (labels.authenticated) {
    const actions = document.createElement('div'); actions.className = 'campaign-actions';
    function action(label, map) {
      const button = document.createElement('button'); button.type = 'button'; button.textContent = label;
      button.addEventListener('click', () => {
        sessionStorage.setItem('kw-content-result', JSON.stringify({...result, title:shownTitle, body:markdown}));
        window.location.href = map ? '/materials/generate?from_tools=1' : '/materials/import';
      });
      actions.append(button);
    }
    action(labels.save, !!result.mapKind);
    card.append(actions);
  }
  resultDisplay.prepend(card);
});
document.getElementById('clear-button').addEventListener('click', () => resultDisplay.replaceChildren());
document.getElementById('tools-copy-text-button').addEventListener('click', async () => {
  await navigator.clipboard.writeText([...resultDisplay.querySelectorAll('.tools-generated-result')].map(node => node.dataset.copyText).join('\n\n'));
  styledAlert(labels.copy, labels.copied);
});

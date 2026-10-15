import {initToolsMonsters} from './tools-monsters.js';
import {initToolsResults} from './tools-results.js';
import {generateToolResult, initToolsNavigation, appendRealmNavigation} from './tools-navigation.js';
import utils, { styledAlert } from "./utils.js";
import {localizeText, resultText} from "./content_generators.js";
import {richContentHTML} from "./rich-content.js";

window.KW_alert = utils.styledAlert;

const labels = JSON.parse(document.getElementById('tools-content-labels').textContent);
// Choice values stay English: they are lookup keys into the table data.
const t = (key) => Object.hasOwn(labels.terms, key) ? labels.terms[key] : key;

let selectedTool = '';
let selectedCategory = '';
let selectedSubcategory = '';
const rollButton = document.getElementById('roll-button');

const results = initToolsResults(labels, styledAlert);
const monsters = initToolsMonsters(labels, results);
const navigation = initToolsNavigation(data, key => labels.navigation?.[key] ?? t(key), (category, subcategory, tool) => {
  selectedTool = tool;
  selectedCategory = category;
  selectedSubcategory = subcategory;
  rollButton.disabled = !subcategory;
  monsters.select(subcategory);
});
rollButton.addEventListener('click', async () => {
  if (!selectedCategory || !selectedSubcategory) return;
  if (selectedSubcategory === 'Random Monster') {monsters.random(); return;}
  if (selectedSubcategory === 'Monster picker') return;
  const canSave = labels.authenticated && !['events', 'items'].includes(selectedTool);
  let result;
  if (selectedSubcategory === 'Reaction Roll' && document.getElementById('warden-dice')) {
    rollButton.disabled = true;
    try {
      const { requestWardenRoll } = await import('./warden_dice.js');
      const rolled = await requestWardenRoll('reaction');
      result = { title: 'Reaction Roll', category: 'note', fields: { Reaction: rolled.result } };
    } catch (error) {
      styledAlert(t('Reaction Roll'), error.message);
      return;
    } finally {
      rollButton.disabled = !selectedSubcategory;
    }
  } else {
    result = generateToolResult(data, selectedCategory, selectedSubcategory);
  }
  const shownTitle = localizeText(result.title, t);
  const markdown = resultText(result, t);
  const entry = results.add({
    title: shownTitle,
    type: t(selectedSubcategory.charAt(0).toUpperCase() + selectedSubcategory.slice(1)),
    html: richContentHTML(markdown),
    copyText: `${shownTitle}\n\n${markdown}`,
    onSave: canSave ? () => {
      sessionStorage.setItem('kw-content-result', JSON.stringify({...result, title:shownTitle, body:markdown}));
      window.location.href = result.mapKind ? '/materials/generate?from_tools=1' : '/materials/import';
    } : null,
  });
  appendRealmNavigation(entry.actions, result, navigation, t, data);
});

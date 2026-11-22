import {initToolsMonsters} from './tools-monsters.js';
import {initToolsItems, itemMarkdown} from './tools-items.js';
import {initToolsResults} from './tools-results.js';
import {initToolsCharacters} from './tools-characters.js';
import {generateToolResult, initToolsNavigation, appendAreaNavigation} from './tools-navigation.js';
import utils, { styledAlert } from "./utils.js";
import {localizeText, resultText} from "./content_generators.js";
import {richContentHTML} from "./rich-content.js";

window.KW_alert = utils.styledAlert;

const labels = JSON.parse(document.getElementById('tools-content-labels').textContent);
// Choice values stay English: they are lookup keys into the table data.
const t = (key) => Object.hasOwn(labels.terms, key) ? labels.terms[key] : key;

const results = initToolsResults(labels, styledAlert);
const monsters = initToolsMonsters(labels, results);
// Save to a module: a map result opens the New map page, a relic or spellbook becomes a module item (#476),
// anything else an article draft.
function saveResult(result, title, markdown) {
  if (result.category === 'relic' || result.category === 'spellbook') {
    sessionStorage.setItem('kw-item-result', itemMarkdown(result));
    window.location.href = '/materials/import-item';
    return;
  }
  sessionStorage.setItem('kw-content-result', JSON.stringify({...result, title, body:markdown}));
  window.location.href = result.mapKind ? '/materials/generate?from_tools=1' : '/materials/import';
}
const canSave = labels.authenticated;
// Rolled mid-session, so there is nothing to keep in a module.
const unsaved = ({category, table}) => category === 'Events' || category === 'Weather' || ['Reaction Roll', 'Faction Actions'].includes(table);
const name = key => labels.navigation?.[key] ?? t(key);

// Every result goes in the one feed, the same way: a roll, a pick from Browse, a character.
function showResult(result, item) {
  const shownTitle = localizeText(result.title, t);
  const markdown = resultText(result, t);
  const entry = results.add({
    title: shownTitle,
    type: name(item.label),
    html: richContentHTML(markdown),
    markdown,
    save: canSave && !unsaved(item) ? {label:labels.save, onClick:() => saveResult(result, shownTitle, markdown)} : null,
    // A realm, dungeon or forest: see it as a complete map first, saved or not (#473). A new tab keeps
    // these results; the map page reads the result from localStorage.
    onMap: result.mapKind ? () => {
      try {localStorage.setItem('kw-tools-map', JSON.stringify({...result, title:shownTitle, body:markdown}));}
      catch {styledAlert(labels.showMap, labels.mapFailed); return;}
      window.open('/tools/map/', '_blank');
    } : null,
  });
  appendAreaNavigation(entry.actions, result, navigation, t, data);
}

const characters = initToolsCharacters(labels, results, styledAlert);
const items = initToolsItems(data, labels, results, t, {
  add: result => showResult(result, {label: result.category === 'relic' ? 'Relic' : 'Spellbook', category: 'Items'}),
  save: canSave ? saveResult : null,
});
const navigation = initToolsNavigation(data, name, {
  panels: {'Monster picker': monsters.picker, ...items.panels},
  selects: {background: characters.background},
  hints: labels.hints, intros: labels.intros,
  mapTables: ['Worldbuilding:Realm', 'Worldbuilding:Dungeon', 'Worldbuilding:Forest'],
  async onRoll(item) {
    const {category, table} = item;
    if (table === 'Random Monster') {monsters.random(); return;}
    if (category === 'Character') {await characters.roll(); return;}
    let result;
    if (table === 'Reaction Roll' && document.getElementById('warden-dice')) {
      try {
        const { requestWardenRoll } = await import('./warden_dice.js');
        const rolled = await requestWardenRoll('reaction');
        const { default: dice3d } = await import('./dice3d.js');
        await dice3d.show(rolled);
        result = { title: 'Reaction Roll', category: 'note', fields: { Reaction: rolled.result } };
      } catch (error) {
        styledAlert(t('Reaction Roll'), error.message);
        return;
      }
    } else {
      result = generateToolResult(data, category, table);
    }
    showResult(result, item);
  },
});

import {initToolsMonsters} from './tools-monsters.js';
import {initToolsResults} from './tools-results.js';
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
const navigation = initToolsNavigation(data, key => labels.navigation?.[key] ?? t(key), {
  panels: {'Monster picker': monsters.picker},
  async onRoll({category, table}, tool, button) {
    if (table === 'Random Monster') {monsters.random(); return;}
    const canSave = labels.authenticated && !['events', 'items'].includes(tool);
    let result;
    if (table === 'Reaction Roll' && document.getElementById('warden-dice')) {
      button.disabled = true;
      try {
        const { requestWardenRoll } = await import('./warden_dice.js');
        const rolled = await requestWardenRoll('reaction');
        const { default: dice3d } = await import('./dice3d.js');
        await dice3d.show(rolled);
        result = { title: 'Reaction Roll', category: 'note', fields: { Reaction: rolled.result } };
      } catch (error) {
        styledAlert(t('Reaction Roll'), error.message);
        return;
      } finally {
        button.disabled = false;
      }
    } else {
      result = generateToolResult(data, category, table);
    }
    const shownTitle = localizeText(result.title, t);
    const markdown = resultText(result, t);
    const entry = results.add({
      title: shownTitle,
      type: t(table.charAt(0).toUpperCase() + table.slice(1)),
      html: richContentHTML(markdown),
      copyText: `${shownTitle}\n\n${markdown}`,
      onSave: canSave ? () => {
        sessionStorage.setItem('kw-content-result', JSON.stringify({...result, title:shownTitle, body:markdown}));
        window.location.href = result.mapKind ? '/materials/generate?from_tools=1' : '/materials/import';
      } : null,
    });
    appendAreaNavigation(entry.actions, result, navigation, t, data);
  },
});

// Treasure, like Monster: Roll a relic or a spellbook (the Items tables), or Browse them. A pick shows the
// same actions as a rolled one, and Add to results puts it in the feed.
import {initMonsterPicker} from './monster-picker.js';
import {resultText} from './content_generators.js';
import {richContentHTML} from './rich-content.js';
import {resultActions} from './tools-results.js';

export const ITEM_PICKERS = [
  {table: 'Relic picker', group: 'Relics', category: 'relic', id: 'relic'},
  {table: 'Spellbook picker', group: 'Spellbooks', category: 'spellbook', id: 'spellbook'},
];

// A relic or spellbook as a module item (#476): '### Name [tags]', then what it does. The tables write
// uses and charges in two spellings (use/uses, charge/charges); module items say 'uses 2', 'charges 1/1'.
export function itemMarkdown(result) {
  const fields = result.fields || {};
  const tags = (fields.tags || []).map(tag => {
    if (tag === 'use' || tag === 'uses') return `uses ${fields.uses ?? fields.use ?? 1}`;
    if (tag === 'charge' || tag === 'charges') {
      const charges = fields.charges ?? fields.charge ?? 1;
      return `charges ${charges}/${fields.max_charges ?? charges}`;
    }
    return tag;
  });
  const description = [fields.description, fields.personality ? `_${fields.personality}_` : '']
    .filter(Boolean).join('\n\n');
  return `### ${result.title}${tags.length ? ` [${tags.join(', ')}]` : ''}\n${description}\n`;
}

// key -> the same result a roll on that table gives.
export function itemCatalog(data, group) {
  const {category} = ITEM_PICKERS.find(picker => picker.group === group);
  return Object.fromEntries((data[group] || []).map(item =>
    [`${category}:${item.name}`, {title: item.name, category, fields: {...item}}]));
}

// `add(result)` puts a pick in the feed, the way a roll does; `save` saves it to a module.
export function initToolsItems(data, labels, results, t, {add, save}) {
  const panels = {};
  for (const {table, group, id} of ITEM_PICKERS) {
    const panel = document.getElementById(`tools-${id}-picker`);
    const select = document.getElementById(`tools-${id}-select`);
    const preview = document.getElementById(`tools-${id}-preview`);
    const catalog = itemCatalog(data, group);
    for (const [key, result] of Object.entries(catalog)) {
      const option = document.createElement('option');
      option.value = key;
      const tags = result.fields.tags || [];
      option.textContent = tags.length ? `${result.title} · ${tags.join(', ')}` : result.title;
      select.append(option);
    }
    initMonsterPicker({
      catalog, select, search: document.getElementById(`tools-${id}-search`),
      onSelect(result) {
        preview.replaceChildren();
        if (!result) return;
        const markdown = resultText(result, t);
        const heading = document.createElement('h3');
        heading.textContent = result.title;
        const body = document.createElement('div');
        body.className = 'rich-content';
        body.innerHTML = richContentHTML(markdown);
        const actions = resultActions([
          {label:labels.addToResults, icon:'fa-solid fa-plus', onClick:() => add(result), className:'kw-add'},
          save && {label:labels.save, icon:'fa-solid fa-floppy-disk', onClick:() => save(result, result.title, markdown)},
          {label:labels.copy, icon:'fa-regular fa-copy', onClick:() => results.copy(`${result.title}\n\n${body.innerText || markdown}`)},
          {label:labels.copyMarkdown, icon:'fa-brands fa-markdown', onClick:() => results.copy(`## ${result.title}\n\n${markdown}`)},
        ]);
        preview.append(heading, actions, body);
      },
    });
    panels[table] = panel;
  }
  return {panels};
}

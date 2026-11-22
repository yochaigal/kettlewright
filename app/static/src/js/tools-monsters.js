import {initMonsterPicker, monsterPreview, monsterText} from './monster-picker.js';
import {resultActions} from './tools-results.js';

// Monster: Roll one from the bestiary, or Browse it. A pick shows the same actions as a rolled one,
// and Add to results puts it in the feed.
export function initToolsMonsters(labels, results) {
  const catalog = JSON.parse(document.getElementById('tools-monster-catalog').textContent);
  const picker = document.getElementById('tools-monster-picker');
  const preview = document.getElementById('tools-monster-preview');
  const dialog = document.getElementById('tools-attach-dialog');
  const form = document.getElementById('tools-attach-form');
  dialog?.querySelectorAll('[data-close-attach]').forEach(button => button.addEventListener('click', () => dialog.close()));
  form?.addEventListener('submit', () => {
    form.action = document.getElementById('tools-attach-party').value;
    form.querySelector('[type=submit]').disabled = true;
  });
  function attach(key) {
    document.getElementById('tools-attach-monster-name').textContent = catalog[key].name;
    if (form) document.getElementById('tools-attach-template').value = key;
    dialog.showModal();
  }
  // Copy text is what a reader sees; Copy Markdown is the stat block as written.
  const statBlock = monster => monsterText(monster).split('\n\n').slice(1).join('\n\n');
  const markdown = monster => `## ${monster.name}\n\n${statBlock(monster)}\n`;
  const save = key => dialog ? {label:labels.attach, icon:'fa-solid fa-users', onClick:() => attach(key)} : null;
  function add(key) {
    const monster = catalog[key];
    results.add({
      title: monster.name,
      type: labels.navigation.Monster,
      html: monsterPreview(monster, {title:false}).innerHTML,
      copyText: monsterText(monster),
      markdown: statBlock(monster),
      save: save(key),
    });
  }
  initMonsterPicker({
    catalog,
    select: document.getElementById('tools-monster-template'),
    search: document.getElementById('tools-monster-search'),
    onSelect(monster, key) {
      preview.replaceChildren();
      if (!monster) return;
      const content = monsterPreview(monster);
      const actions = resultActions([
        {label:labels.addToResults, icon:'fa-solid fa-plus', onClick:() => add(key), className:'kw-add'},
        save(key),
        {label:labels.copy, icon:'fa-regular fa-copy', onClick:() => results.copy(monsterText(monster))},
        {label:labels.copyMarkdown, icon:'fa-brands fa-markdown', onClick:() => results.copy(markdown(monster))},
      ]);
      const heading = content.querySelector('h3');
      if (heading) heading.after(actions); else content.prepend(actions);
      preview.append(content);
    },
  });
  return {
    picker,
    random() {
      const keys = Object.keys(catalog);
      add(keys[Math.floor(Math.random() * keys.length)]);
    },
  };
}

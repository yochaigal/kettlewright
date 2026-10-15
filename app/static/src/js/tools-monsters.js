import {initMonsterPicker, monsterPreview, monsterText} from './monster-picker.js';

export function initToolsMonsters(labels, results) {
  const catalog = JSON.parse(document.getElementById('tools-monster-catalog').textContent);
  const picker = document.getElementById('tools-monster-picker');
  const preview = document.getElementById('tools-monster-preview');
  const dialog = document.getElementById('tools-attach-dialog');
  const form = document.getElementById('tools-attach-form');
  const generate = document.getElementById('roll-button');
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
  initMonsterPicker({
    catalog,
    select: document.getElementById('tools-monster-template'),
    search: document.getElementById('tools-monster-search'),
    onSelect(monster, key) {
      preview.replaceChildren();
      if (!monster) return;
      preview.append(monsterPreview(monster));
      const actions = document.createElement('div');
      actions.className = 'tools-result-actions';
      const copy = document.createElement('button');
      copy.type = 'button';
      copy.textContent = labels.copy;
      copy.addEventListener('click', () => results.copy(monsterText(monster)));
      actions.append(copy);
      if (dialog) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = labels.attach;
        button.addEventListener('click', () => attach(key));
        actions.append(button);
      }
      preview.append(actions);
    },
  });
  return {
    select(table) {
      const active = table === 'Monster picker';
      picker.hidden = !active;
      document.getElementById('tools-table-panel').classList.toggle('tools-picker-active', active);
      generate.hidden = active;
    },
    random() {
      const keys = Object.keys(catalog), key = keys[Math.floor(Math.random() * keys.length)];
      const monster = catalog[key];
      results.add({
        title: monster.name,
        type: labels.randomMonster,
        html: monsterPreview(monster, {title:false}).innerHTML,
        copyText: monsterText(monster),
        onSave: dialog ? () => attach(key) : null,
        actionLabel: labels.attach,
      });
    },
  };
}

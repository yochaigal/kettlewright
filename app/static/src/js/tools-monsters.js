import {initMonsterPicker, monsterPreview, monsterText} from './monster-picker.js';

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
  initMonsterPicker({
    catalog,
    select: document.getElementById('tools-monster-template'),
    search: document.getElementById('tools-monster-search'),
    onSelect(monster, key) {
      preview.replaceChildren();
      if (!monster) return;
      // Like a result: its actions right under its name (Attach to party, Copy text).
      const content = monsterPreview(monster);
      const actions = document.createElement('div');
      actions.className = 'tools-result-actions tools-actions';
      const button = (label, icon, onClick) => {
        const control = document.createElement('button');
        control.type = 'button';
        control.innerHTML = `<i class="fa-solid ${icon}" aria-hidden="true"></i> `;
        control.append(label);
        control.addEventListener('click', onClick);
        actions.append(control);
      };
      if (dialog) button(labels.attach, 'fa-users', () => attach(key));
      button(labels.copy, 'fa-copy', () => results.copy(monsterText(monster)));
      const heading = content.querySelector('h3');
      if (heading) heading.after(actions); else content.prepend(actions);
      preview.append(content);
    },
  });
  return {
    picker,
    random() {
      const keys = Object.keys(catalog), key = keys[Math.floor(Math.random() * keys.length)];
      const monster = catalog[key];
      results.add({
        title: monster.name,
        type: labels.randomMonster,
        html: monsterPreview(monster, {title:false}).innerHTML,
        copyText: monsterText(monster),
        onSave: dialog ? () => attach(key) : null,
        actionLabel: labels.attach, actionIcon: 'fa-users',
      });
    },
  };
}

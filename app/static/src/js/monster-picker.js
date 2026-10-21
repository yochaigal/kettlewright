import {richContentHTML, inlineContentHTML} from './rich-content.js';

export function initMonsterBatchPicker({rows, search, selectedOnly, total, summon, empty}) {
  const choices = rows.map(row => ({row, check: row.querySelector('[name=template]'), quantity: row.querySelector('[type=number]'),
    decrease: row.querySelector('[data-quantity-step="-1"]'),
    increase: row.querySelector('[data-quantity-step="1"]')}));
  function update() {
    const query = search.value.trim().toLowerCase();
    let count = 0, valid = true;
    for (const {row, check, quantity, decrease, increase} of choices) {
      const validQuantity = quantity.validity.valid && /^[0-9]{1,3}$/.test(quantity.value);
      valid = valid && validQuantity;
      check.checked = !validQuantity || Number(quantity.value) > 0;
      row.dataset.selected = String(check.checked);
      decrease.disabled = Number(quantity.value) <= 0;
      increase.disabled = Number(quantity.value) >= 100;
      row.hidden = !row.dataset.name.includes(query) || (selectedOnly.checked && !check.checked);
      if (check.checked) {
        count += Math.max(0, Number(quantity.value) || 0);
      }
    }
    total.value = String(count);
    summon.disabled = !valid || count < 1 || count > 100;
    empty.hidden = choices.some(({row}) => !row.hidden);
  }
  for (const {quantity, decrease, increase} of choices) {
    quantity.addEventListener('input', update);
    for (const [button, step] of [[decrease, -1], [increase, 1]]) {
      button.addEventListener('click', () => {
        const current = Number(quantity.value);
        quantity.value = String(Math.min(100, Math.max(0, (Number.isFinite(current) ? Math.round(current) : 0) + step)));
        update();
      });
    }
  }
  search.addEventListener('input', update);
  selectedOnly.addEventListener('change', update);
  update();
}

// The party catalog and Tools use the same search, selection and stat-block preview.
export function initMonsterPicker({catalog, select, search, onSelect}) {
  function show() {onSelect(catalog[select.value] || null, select.value);}
  search.addEventListener('input', () => {
    const query = search.value.trim().toLowerCase();
    for (const option of select.options) option.hidden = !option.textContent.toLowerCase().includes(query);
    const visible = [...select.options].filter(option => !option.hidden);
    if (!visible.some(option => option.selected)) select.value = visible[0]?.value || '';
    show();
  });
  select.addEventListener('change', show);
  show();
}

export function monsterPreview(monster, {title = true} = {}) {
  const content = document.createElement('div');
  const portrait = document.createElement('img');
  portrait.src = new URL('../../images/portraits/' + monster.image_url, import.meta.url).href;
  portrait.alt = monster.name;
  portrait.className = 'monster-preview-portrait';
  const stats = document.createElement('p');
  stats.textContent = `${monster.hp} HP · ${monster.armor} Armor · ${monster.strength} STR · ${monster.dexterity} DEX · ${monster.willpower} WIL`;
  const attack = document.createElement('p'); attack.innerHTML = inlineContentHTML(monster.attack);
  const notes = document.createElement('div'); notes.innerHTML = richContentHTML(monster.notes);
  const source = document.createElement('a'); source.href = monster.source; source.textContent = monster.name; source.target = '_blank'; source.rel = 'noopener noreferrer';
  content.append(portrait);
  if (title) {const heading = document.createElement('h3'); heading.textContent = monster.name; content.append(heading);}
  content.append(stats, attack, notes, source);
  return content;
}

export function monsterText(monster) {
  return `${monster.name}\n\n${monster.hp} HP, ${monster.armor} Armor, ${monster.strength} STR, ${monster.dexterity} DEX, ${monster.willpower} WIL, ${monster.attack}\n\n${monster.notes}`;
}

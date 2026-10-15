import {richContentHTML, inlineContentHTML} from './rich-content.js';

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

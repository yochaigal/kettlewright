import {richContentHTML, inlineContentHTML} from './rich-content.js';
const catalog = JSON.parse(document.getElementById('monster-catalog').textContent);
const select = document.getElementById('monster-template'), search = document.getElementById('monster-search');
const preview = document.getElementById('monster-preview'), summon = document.getElementById('summon-monster');
function show() {
  const monster = catalog[select.value];
  preview.replaceChildren();
  if (!monster) return;
  const portrait = document.createElement('img');
  portrait.src = new URL('../../images/portraits/' + monster.image_url, import.meta.url).href;
  portrait.alt = monster.name;
  portrait.className = 'monster-preview-portrait';
  const title = document.createElement('h3'); title.textContent = monster.name;
  const stats = document.createElement('p');
  stats.textContent = `${monster.hp} HP · ${monster.armor} Armor · ${monster.strength} STR · ${monster.dexterity} DEX · ${monster.willpower} WIL`;
  const attack = document.createElement('p'); attack.innerHTML = inlineContentHTML(monster.attack);
  const notes = document.createElement('div'); notes.innerHTML = richContentHTML(monster.notes);
  const source = document.createElement('a'); source.href = monster.source; source.textContent = monster.name; source.target = '_blank'; source.rel = 'noopener noreferrer';
  preview.append(portrait, title, stats, attack, notes, source);
}
search.addEventListener('input', () => {
  const query = search.value.trim().toLowerCase();
  for (const option of select.options) option.hidden = !option.textContent.toLowerCase().includes(query);
  const visible = Array.from(select.options).filter(option => !option.hidden);
  if (!visible.some(option => option.selected)) select.value = visible[0]?.value || '';
  summon.disabled = visible.length === 0;
  show();
});
select.addEventListener('change', show);
show();

import {initMonsterPicker, monsterPreview} from './monster-picker.js';
const catalog = JSON.parse(document.getElementById('monster-catalog').textContent);
const preview = document.getElementById('monster-preview'), summon = document.getElementById('summon-monster');
initMonsterPicker({
  catalog,
  select: document.getElementById('monster-template'),
  search: document.getElementById('monster-search'),
  onSelect(monster) {
    preview.replaceChildren();
    summon.disabled = !monster;
    if (monster) preview.append(monsterPreview(monster));
  },
});

import {initMonsterBatchPicker, monsterPreview} from './monster-picker.js';
import {initMonsterPreviews} from './monster-previews.js';
const catalog = JSON.parse(document.getElementById('monster-catalog').textContent);
const preview = document.getElementById('monster-preview');
const previewContent = document.getElementById('monster-preview-content');
initMonsterBatchPicker({
  rows: [...document.querySelectorAll('.monster-choice')],
  search: document.getElementById('monster-search'),
  selectedOnly: document.getElementById('monster-selected-only'),
  total: document.getElementById('monster-total'),
  summon: document.getElementById('summon-monster'),
  empty: document.getElementById('monster-no-results'),
});
initMonsterPreviews({
  triggers: [...document.querySelectorAll('[data-preview]')],
  panel: preview,
  closeButton: document.getElementById('monster-close-preview'),
  render(key) { previewContent.replaceChildren(monsterPreview(catalog[key])); },
});
// Token art (Kettlewright or Oozejar): the cards and previews show the art the new monsters will get.
for (const radio of document.querySelectorAll('input[name="monster_art"]')) {
  radio.addEventListener('change', () => {
    if (!radio.checked) return;
    for (const image of document.querySelectorAll('.monster-choice img')) {
      const src = image.getAttribute('data-art-' + radio.value);
      if (src) image.src = src;
    }
    for (const monster of Object.values(catalog)) monster.image_url = monster.art?.[radio.value] || monster.image_url;
  });
}

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

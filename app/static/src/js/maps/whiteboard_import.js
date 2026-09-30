import {exportToSvg, restoreElements} from 'excalidraw';

export function setupMapImport({config, replace, tell}) {
  const dialog = document.getElementById('map-import');
  if (!dialog) return;
  const select = document.getElementById('map-source');
  const preview = document.getElementById('map-preview');
  const submit = document.getElementById('confirm-import');
  const error = document.getElementById('import-error');
  let selected = null, requestId = 0;
  async function loadPreview() {
    const id = ++requestId;
    selected = null; submit.disabled = true; preview.replaceChildren(); error.textContent = '';
    if (!select.value) return;
    try {
      const response = await fetch(`${config.sourcesUrl}/${select.value}`, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      const svg = await exportToSvg({elements: restoreElements(data.drawing.elements, null), files: data.drawing.files,
        appState: {...data.drawing.appState, exportBackground: true, exportWithDarkMode: false}});
      if (id !== requestId) return;
      svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', data.title);
      preview.replaceChildren(svg); selected = data; submit.disabled = false;
    } catch (_) {if (id === requestId) error.textContent = config.messages.importFailed;}
  }
  document.getElementById('load-map').addEventListener('click', async () => {
    dialog.showModal(); selected = null; submit.disabled = true; preview.replaceChildren(); select.replaceChildren();
    error.textContent = ''; document.getElementById('import-cover').checked = true;
    try {
      const response = await fetch(config.sourcesUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok || response.redirected) throw new Error();
      const {maps} = await response.json();
      const groups = new Map();
      for (const item of maps.sort((a, b) => (a.campaign || '').localeCompare(b.campaign || '') || a.title.localeCompare(b.title))) {
        const key = item.campaign_id || 'unfiled';
        if (!groups.has(key)) {const group = document.createElement('optgroup'); group.label = item.campaign || config.messages.unfiled;
          groups.set(key, group); select.append(group);}
        const option = document.createElement('option'); option.value = item.id; option.textContent = item.title;
        groups.get(key).append(option);
      }
      if (!maps.length) error.textContent = config.messages.noMaps;
      else await loadPreview();
    } catch (_) {error.textContent = config.messages.importFailed;}
  });
  select.addEventListener('change', loadPreview);
  document.getElementById('cancel-import').addEventListener('click', () => {++requestId; dialog.close();});
  submit.addEventListener('click', async () => {
    if (!selected) return;
    submit.disabled = true; select.disabled = true; error.textContent = '';
    try {
      await replace(selected, document.getElementById('import-cover').checked);
      dialog.close(); tell('saved');
    } catch (reason) {error.textContent = reason.message || config.messages.importFailed;}
    finally {submit.disabled = false; select.disabled = false;}
  });
}

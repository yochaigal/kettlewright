// Character: an ordinary tool. Roll asks the server for a character (the Background select picks one, or
// Random), and it goes in the shared feed like any result: Save to Party / Save as NPC, Copy text,
// Copy Markdown, then Export JSON and Print, which only a character has.
import {plainText} from './tools-results.js';

export function initToolsCharacters(labels, results, notify) {
  const config = document.getElementById('tools-character');
  const background = document.getElementById('background-select');
  const saveDialog = document.getElementById('pcgen-save-dialog');
  const options = saveDialog ? JSON.parse(document.getElementById('pcgen-save-options').textContent) : {};
  const csrf = () => document.querySelector('#pcgen-save-form [name=csrf_token], [name=csrf_token]')?.value || '';

  function exportJSON(raw, name) {
    const url = URL.createObjectURL(new Blob([raw], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${name.replace(/[\\/]/g, '-')}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // Print the same snapshot in a separate document, keeping the Tools page.
  function print(raw, button) {
    const frame = document.createElement('iframe');
    frame.name = `pcgen-print-${Date.now()}`;
    frame.className = 'tools-print-frame';
    frame.title = labels.print;
    const post = document.createElement('form');
    post.method = 'post';
    post.action = config.dataset.printUrl;
    post.target = frame.name;
    for (const [name, value] of Object.entries({json_data:raw, csrf_token:csrf()})) {
      const input = document.createElement('input');
      input.type = 'hidden'; input.name = name; input.value = value;
      post.append(input);
    }
    frame.addEventListener('load', async () => {
      const doc = frame.contentDocument;
      if (!doc.querySelector('.character-print-page')) return;
      doc.getElementById('navbar')?.classList.add('hidden');
      doc.body.classList.remove('dark-mode');
      await doc.fonts.ready;
      frame.contentWindow.addEventListener('afterprint', () => {
        frame.remove();
        button?.focus();
      }, {once:true});
      frame.contentWindow.focus();
      frame.contentWindow.print();
    });
    post.hidden = true;
    document.body.append(frame, post);
    post.submit();
    post.remove();
  }

  function openSave(kind, snapshot, name, url) {
    const choice = options[kind];
    const partySave = kind === 'party';
    const select = document.getElementById('pcgen-save-target');
    const submit = document.getElementById('pcgen-save-submit');
    document.getElementById('pcgen-save-kind-field').hidden = !partySave;
    const companion = document.getElementById('pcgen-save-kind');
    companion.disabled = !partySave;
    companion.value = 'hireling';
    document.getElementById('pcgen-save-title').textContent = choice.label;
    document.getElementById('pcgen-save-name').textContent = name;
    document.getElementById('pcgen-save-snapshot').value = snapshot;
    document.getElementById('pcgen-save-target-label').textContent = choice.target;
    select.replaceChildren();
    choice.targets.forEach((id, index) => select.append(new Option(choice.names[index], id)));
    select.hidden = !choice.targets.length;
    document.getElementById('pcgen-save-target-label').hidden = !choice.targets.length;
    const empty = document.getElementById('pcgen-save-empty');
    empty.hidden = !!choice.targets.length;
    empty.textContent = choice.empty;
    submit.hidden = !choice.targets.length;
    submit.disabled = false;
    document.getElementById('pcgen-save-form').action = url;
    saveDialog.showModal();
  }
  if (saveDialog) {
    document.getElementById('pcgen-save-cancel').addEventListener('click', () => saveDialog.close());
    document.getElementById('pcgen-save-form').addEventListener('submit', () => {
      document.getElementById('pcgen-save-submit').disabled = true;
    });
  }

  async function roll() {
    const url = new URL(config.dataset.url, window.location.href);
    url.searchParams.set('view', 'sheet');
    if (background?.value) url.searchParams.set('background', background.value);
    let html;
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(response.statusText);
      html = await response.text();
    } catch {
      notify(labels.navigation.Character, config.dataset.error);
      return;
    }
    const holder = document.createElement('div');
    holder.innerHTML = html;
    const value = id => holder.querySelector(`#${id}`)?.value || '';
    const raw = value('json_data'), snapshot = value('pcgen-snapshot'), name = value('character_name');
    const markdown = holder.querySelector('#pcgen-markdown-source')?.content.textContent || '';
    const copySource = holder.querySelector('#pcgen-copy-source');
    const copyText = copySource ? plainText(copySource.content) : '';
    // The data is read; only the sheet is shown. Several characters can be in the feed at once.
    holder.querySelectorAll('input[type=hidden], template#pcgen-markdown-source, template#pcgen-copy-source').forEach(node => node.remove());
    const save = saveDialog ? Object.entries(options).map(([kind, choice]) => ({
      label:choice.label, icon:kind === 'party' ? 'fa-solid fa-users' : 'fa-solid fa-bookmark',
      onClick:() => openSave(kind, snapshot, name, choice.url),
    })) : null;
    const entry = results.add({
      title:name, type:labels.navigation.Character, html:holder.innerHTML,
      // The server writes the character's Markdown, name included.
      copyMarkdown:markdown, copyText, save,
      extra:[
        {label:`${labels.export} JSON`, icon:'fa-solid fa-file-export', onClick:() => exportJSON(raw, name)},
        {label:labels.print, icon:'fa-solid fa-print', onClick:event => print(raw, event.currentTarget)},
      ],
    });
    // The inventory tabs switch containers inside this one result.
    entry.body.addEventListener('click', event => {
      const tab = event.target.closest('[data-preview-container]');
      if (!tab) return;
      const template = [...entry.body.querySelectorAll('template[data-pcgen-inventory]')].find(node => node.dataset.pcgenInventory === tab.dataset.previewContainer);
      const active = entry.body.querySelector('#pcgen-active-inventory');
      if (!template || !active) return;
      active.replaceChildren(template.content.cloneNode(true));
      active.querySelector('[aria-pressed="true"]')?.focus();
    });
  }

  return {roll, background};
}

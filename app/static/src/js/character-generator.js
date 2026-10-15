import {styledAlert} from './utils.js';

const form = document.getElementById('pcgen-form');
const display = document.getElementById('pcgen-result-display');
const empty = document.getElementById('pcgen-empty-state');
const error = document.getElementById('pcgen-error');
const actions = [...form.querySelectorAll('.tools-history-actions button')];

const viewTabs = [...document.querySelectorAll('[data-character-view]')];
let selectedView = 'sheet';
function showView(view) {
  selectedView = view;
  viewTabs.forEach(tab => {
    const active = tab.dataset.characterView === view;
    tab.setAttribute('aria-selected', String(active));
    tab.tabIndex = active ? 0 : -1;
    const panel = display.querySelector(`#${tab.getAttribute('aria-controls')}`);
    if (panel) panel.hidden = !active;
  });
}
viewTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => showView(tab.dataset.characterView));
  tab.addEventListener('keydown', event => {
    const next = {ArrowRight:(index + 1) % viewTabs.length, ArrowLeft:(index + viewTabs.length - 1) % viewTabs.length, Home:0, End:viewTabs.length - 1}[event.key];
    if (next === undefined) return;
    event.preventDefault();
    showView(viewTabs[next].dataset.characterView);
    viewTabs[next].focus();
  });
});

form.addEventListener('submit', event => event.preventDefault());
document.addEventListener('htmx:afterSwap', event => {
  if (event.detail.target !== display) return;
  const ready = !!display.querySelector('#json_data');
  const markdown = display.querySelector('#pcgen-markdown-panel');
  if (ready && markdown) {
    markdown.append(display.querySelector('#pcgen-copy-source').content.cloneNode(true));
    markdown.querySelectorAll('input').forEach(input => input.remove());
  }
  showView(selectedView);
  empty.hidden = ready;
  actions.forEach(button => {button.disabled = !ready;});
  error.hidden = true;
});
for (const name of ['htmx:responseError', 'htmx:sendError']) document.addEventListener(name, event => {
  if (event.detail.elt?.id !== 'pcgen-button') return;
  error.textContent = form.dataset.error;
  error.hidden = false;
});

display.addEventListener('click', event => {
  const tab = event.target.closest('[data-preview-container]');
  if (!tab) return;
  const template = [...display.querySelectorAll('template[data-pcgen-inventory]')].find(node => node.dataset.pcgenInventory === tab.dataset.previewContainer);
  if (!template) return;
  const active = display.querySelector('#pcgen-active-inventory');
  active.replaceChildren(template.content.cloneNode(true));
  active.querySelector('[aria-pressed="true"]')?.focus();
});

document.getElementById('pcgen-copy-text-button').addEventListener('click', async () => {
  try {
    const source = document.createElement('div');
    source.className = 'tools-copy-source';
    source.append(display.querySelector('#pcgen-copy-source').content.cloneNode(true));
    document.body.append(source);
    const text = source.innerText;
    source.remove();
    await navigator.clipboard.writeText(text);
    styledAlert(form.dataset.copyLabel, form.dataset.copied);
  } catch {
    styledAlert(form.dataset.copyLabel, JSON.parse(document.getElementById('tools-content-labels').textContent).copyFailed);
  }
});
document.getElementById('pcgen-json-button').addEventListener('click', () => {
  const raw = display.querySelector('#json_data')?.value;
  if (!raw) return;
  const blob = new Blob([raw], {type:'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${display.querySelector('#character_name').value.replace(/[\\/]/g, '-')}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

document.getElementById('gen-print-button').addEventListener('click', event => {
  const raw = display.querySelector('#json_data')?.value;
  if (!raw) return;
  // Print the same snapshot in a separate document, retaining the Tools page.
  const frame = document.createElement('iframe');
  frame.name = `pcgen-print-${Date.now()}`;
  frame.className = 'tools-print-frame';
  frame.title = event.currentTarget.textContent;
  const post = document.createElement('form');
  post.method = 'post';
  post.action = event.currentTarget.dataset.url;
  post.target = frame.name;
  for (const [name, value] of Object.entries({json_data:raw, csrf_token:form.querySelector('[name=csrf_token]')?.value || ''})) {
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
      document.getElementById('gen-print-button').focus();
    }, {once:true});
    frame.contentWindow.focus();
    frame.contentWindow.print();
  });
  post.hidden = true;
  document.body.append(frame, post);
  post.submit();
  post.remove();
});

const saveDialog = document.getElementById('pcgen-save-dialog');
if (saveDialog) {
  const options = JSON.parse(document.getElementById('pcgen-save-options').textContent);
  const saveForm = document.getElementById('pcgen-save-form');
  const select = document.getElementById('pcgen-save-target');
  const submit = document.getElementById('pcgen-save-submit');
  document.querySelectorAll('[data-save-kind]').forEach(button => button.addEventListener('click', () => {
    const snapshot = display.querySelector('#pcgen-snapshot')?.value;
    if (!snapshot) return;
    const choice = options[button.dataset.saveKind];
    document.getElementById('pcgen-save-title').textContent = choice.label;
    document.getElementById('pcgen-save-name').textContent = display.querySelector('#character_name').value;
    document.getElementById('pcgen-save-snapshot').value = snapshot;
    document.getElementById('pcgen-save-target-label').textContent = choice.target;
    select.replaceChildren();
    choice.targets.forEach((id, index) => {
      const option = document.createElement('option');
      option.value = id; option.textContent = choice.names[index];
      select.append(option);
    });
    select.hidden = !choice.targets.length;
    document.getElementById('pcgen-save-target-label').hidden = !choice.targets.length;
    const empty = document.getElementById('pcgen-save-empty');
    empty.hidden = !!choice.targets.length;
    empty.textContent = choice.empty;
    submit.hidden = !choice.targets.length;
    submit.disabled = false;
    saveForm.action = button.dataset.url;
    saveDialog.showModal();
  }));
  document.getElementById('pcgen-save-cancel').addEventListener('click', () => saveDialog.close());
  saveForm.addEventListener('submit', () => {submit.disabled = true;});
}

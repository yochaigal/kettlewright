// One result feed for both Tools renderers. Copy/save retain the original generated text.
export function initToolsResults(labels, notify) {
  const display = document.getElementById('tools-result-display');
  const empty = document.getElementById('tools-empty-state');
  const copyAll = document.getElementById('tools-copy-text-button');
  const clear = document.getElementById('clear-button');
  function update() {
    const hasResults = !!display.childElementCount;
    empty.hidden = hasResults;
    copyAll.disabled = clear.disabled = !hasResults;
  }
  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      notify(labels.copy, labels.copied);
    } catch {
      notify(labels.copy, labels.copyFailed);
    }
  }
  copyAll.addEventListener('click', () => copy([...display.children].map(card => card.dataset.copyText).join('\n\n')));
  clear.addEventListener('click', () => {display.replaceChildren(); update();});
  update();
  return {
    copy,
    add({title, type, html, copyText, onSave, actionLabel = labels.save}) {
      const card = document.createElement('details');
      card.className = 'tools-generated-result';
      card.open = true;

      const heading = document.createElement('summary');
      const titleBlock = document.createElement('span');
      titleBlock.className = 'tools-result-heading';
      const kind = document.createElement('span');
      kind.className = 'tools-result-type';
      kind.textContent = type;
      const name = document.createElement('span');
      name.className = 'tools-result-title';
      name.textContent = title;
      titleBlock.append(kind, name);
      heading.append(titleBlock);
      const content = document.createElement('div');
      content.className = 'tools-result-content';
      const body = document.createElement('div');
      body.className = 'rich-content';
      body.innerHTML = html;
      const actions = document.createElement('div');
      actions.className = 'tools-result-actions';
      const copyButton = document.createElement('button');
      copyButton.type = 'button';
      copyButton.textContent = labels.copy;
      copyButton.addEventListener('click', () => copy(card.dataset.copyText));
      actions.append(copyButton);
      if (onSave) {
        const save = document.createElement('button');
        save.type = 'button';
        save.textContent = actionLabel;
        save.addEventListener('click', onSave);
        actions.append(save);
      }
      content.append(body, actions);
      card.append(heading, content);
      display.prepend(card);
      card.dataset.copyText = copyText ?? `${title}\n\n${body.innerText}`;
      update();
      return {card, body, actions};
    },
  };
}

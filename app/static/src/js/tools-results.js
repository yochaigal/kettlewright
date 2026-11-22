// One result feed for every tool, characters included. Every result has the same actions, in the same
// order: Show map (when it applies) · Save · Copy text · Copy Markdown, then anything only it has.
// Desktop shows the feed beside the tools; narrower screens scroll to the new result.
export const SIDE_BY_SIDE = '(min-width: 1000px)';

// The row of actions under a result's title (#473: a long dungeon hid them at the bottom).
// Each action is {label, icon, onClick, className?}; `icon` is a full Font Awesome class list.
export function resultActions(actions) {
  const row = document.createElement('div');
  row.className = 'tools-result-actions tools-actions';
  for (const {label, icon, onClick, className = ''} of actions.filter(Boolean)) {
    const control = document.createElement('button');
    control.type = 'button';
    control.className = className;
    control.innerHTML = `<i class="${icon}" aria-hidden="true"></i> `;
    control.append(label);
    control.addEventListener('click', onClick);
    row.append(control);
  }
  return row;
}

// The plain text of rendered HTML, as a reader sees it (innerText needs the element on the page).
export function plainText(element) {
  const source = document.createElement('div');
  source.className = 'tools-copy-source';
  source.append(element.cloneNode(true));
  document.body.append(source);
  const text = source.innerText.trim();
  source.remove();
  return text;
}

export function initToolsResults(labels, notify) {
  const display = document.getElementById('tools-result-display');
  const empty = document.getElementById('tools-empty-state');
  const copyAll = document.getElementById('tools-copy-text-button');
  const clear = document.getElementById('clear-button');
  const bar = document.getElementById('tools-results-bar');
  const count = document.getElementById('tools-result-count');
  function update() {
    const hasResults = !!display.childElementCount;
    empty.hidden = hasResults;
    bar.hidden = !hasResults;
    count.textContent = hasResults ? String(display.childElementCount) : '';
  }
  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      notify(labels.copy, labels.copied);
    } catch {
      notify(labels.copy, labels.copyFailed);
    }
  }
  // The standard actions for a result: [Show map] [Save] Copy text, Copy Markdown, then `extra`.
  function standardActions({save, onMap, text, markdown, extra = []}) {
    return [
      onMap && {label:labels.showMap, icon:'fa-solid fa-map', onClick:onMap, className:'kw-add tools-show-map'},
      ...[save].flat().filter(Boolean).map(action => ({icon:'fa-solid fa-floppy-disk', ...action})),
      {label:labels.copy, icon:'fa-regular fa-copy', onClick:() => copy(text())},
      markdown && {label:labels.copyMarkdown, icon:'fa-brands fa-markdown', onClick:() => copy(markdown())},
      ...extra,
    ];
  }
  copyAll.addEventListener('click', () => copy([...display.children].map(card => card.dataset.copyText).join('\n\n')));
  clear.addEventListener('click', () => {display.replaceChildren(); update();});
  update();
  return {
    copy,
    standardActions,
    // `html` is shown; `markdown` is what Copy Markdown copies (a heading with the title, then it);
    // Copy text copies what is shown, as plain text, unless `copyText` says otherwise.
    // `copyMarkdown` replaces that when a result has its own Markdown (a character's).
    // `save` is one action or a list: {label, icon?, onClick}.
    add({title, type, html, markdown, copyMarkdown, copyText, save, onMap, extra}) {
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
      const text = () => card.dataset.copyText;
      const actions = resultActions(standardActions({
        save, onMap, text, extra,
        markdown:copyMarkdown ? () => copyMarkdown
          : markdown === undefined ? null : () => `## ${title}\n\n${markdown.trim()}\n`,
      }));
      content.append(actions, body);
      card.append(heading, content);
      display.prepend(card);
      card.dataset.copyText = copyText ?? `${title}\n\n${plainText(body)}`;
      update();
      // Beside the tools the new result is already in view at the top of the feed; below them, go to it.
      if (!window.matchMedia?.(SIDE_BY_SIDE).matches) {
        const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
        card.scrollIntoView({behavior:reduce ? 'auto' : 'smooth', block:'start'});
      } else {
        card.closest('.tools-results-island')?.scrollTo?.({top:0});
      }
      return {card, body, actions};
    },
  };
}

// A compact character sheet beside the whiteboard in a Discord Activity (#423): HP, abilities,
// conditions, armor and the inventory with its slots, uses and Fatigue. Changes are saved by the
// server with the same rules as the Discord /kw actions (app/lib/compact_sheet.py).
const STATS = [['hp', 'HP'], ['strength', 'STR'], ['dexterity', 'DEX'], ['willpower', 'WIL']];
const STAT_ACTIONS = {hp: 'hp', strength: 'str', dexterity: 'dex', willpower: 'wil'};

function element(doc, tag, props = {}, ...children) {
  const node = doc.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'dataset') Object.assign(node.dataset, value);
    else if (key in node || key === 'className' || key === 'textContent') node[key] = value;
    else node.setAttribute(key, value);
  }
  node.append(...children.filter(child => child !== null && child !== undefined));
  return node;
}

// The sheet of one character as DOM. `act(change)` saves a change; buttons are disabled meanwhile.
export function renderSheet(doc, character, messages, act, busy = false) {
  const text = (key, values = {}) => Object.entries(values).reduce((result, [name, value]) =>
    result.replace(`{${name}}`, value), messages[key] || key);
  const button = (label, change, props = {}) => {
    const node = element(doc, 'button', {type: 'button', textContent: label, ...props});
    node.disabled = busy || Boolean(props.disabled);
    node.addEventListener('click', () => act(change));
    return node;
  };
  const stats = element(doc, 'div', {className: 'sheet-stats'});
  for (const [field] of STATS) {
    const stat = character[field], label = messages[field] || field;
    // −/+ change the recorded HP; effective HP can be lower (panic, full inventory).
    const current = field === 'hp' ? stat.stored : stat.value;
    stats.append(element(doc, 'div', {className: 'sheet-stat'},
      element(doc, 'span', {className: 'sheet-stat-label', textContent: label}),
      button('−', {action: 'stat', stat: STAT_ACTIONS[field], value: -1},
        {disabled: current <= 0, 'aria-label': text('lower', {stat: label})}),
      element(doc, 'output', {textContent: `${stat.value}/${stat.max}`}),
      button('+', {action: 'stat', stat: STAT_ACTIONS[field], value: 1},
        {disabled: current >= stat.max, 'aria-label': text('raise', {stat: label})})));
  }
  stats.append(element(doc, 'div', {className: 'sheet-stat'},
    element(doc, 'span', {className: 'sheet-stat-label', textContent: messages.armor}),
    element(doc, 'output', {textContent: String(character.armor)})));
  const note = character.hp.value !== character.hp.stored
    ? element(doc, 'p', {className: 'sheet-note', textContent: text('effective', {hp: character.hp.value})}) : null;
  const conditions = element(doc, 'div', {className: 'sheet-conditions'});
  for (const condition of ['deprived', 'panicked']) {
    const box = element(doc, 'input', {type: 'checkbox', checked: character[condition]});
    box.disabled = busy;
    box.addEventListener('change', () => act({action: 'condition', condition, active: box.checked}));
    conditions.append(element(doc, 'label', {}, box, ' ' + messages[condition]));
  }
  if (character.dead) conditions.append(element(doc, 'strong', {className: 'sheet-dead', textContent: messages.dead}));
  const inventory = element(doc, 'div', {className: 'sheet-inventory'},
    element(doc, 'div', {className: 'sheet-inventory-heading'},
      element(doc, 'h3', {textContent: messages.inventory}),
      button(messages.addFatigue, {action: 'fatigue', amount: 1})));
  for (const container of character.containers) {
    const list = element(doc, 'ul');
    for (const item of container.items) {
      const counters = ['uses', 'charges'].filter(key => key in item);
      list.append(element(doc, 'li', {className: item.fatigue ? 'sheet-item is-fatigue' : 'sheet-item'},
        element(doc, 'span', {className: 'sheet-item-name', textContent: item.name}),
        // Each counter with its own Use button: an item can have both uses and charges.
        ...counters.map(key => {
          const remaining = `${item[key]}/${item['max_' + key]} ${messages[key]}`;
          return element(doc, 'span', {className: 'sheet-counter'}, remaining,
            button(messages.use, {action: 'use', item: item.id, resource: key},
              {disabled: item[key] <= 0, 'aria-label': `${messages.use}: ${item.name}, ${remaining}`}));
        }),
        item.fatigue ? button(messages.clear, {action: 'remove', item: item.id}) : null));
    }
    inventory.append(element(doc, 'section', {className: 'sheet-container'},
      element(doc, 'h4', {}, element(doc, 'span', {textContent: container.name}),
        element(doc, 'span', {className: 'sheet-slots', textContent: text('slots', {used: container.used, total: container.slots})})),
      list));
  }
  return element(doc, 'div', {className: 'sheet'}, stats, note, conditions, inventory);
}

export function setupCharacterSheet({config, socket, doc = document, request = fetch}) {
  const dialog = doc.getElementById('character-sheet'), opener = doc.getElementById('board-sheet');
  if (!dialog || !opener || !config.sheetsUrl) return {destroy() {}};
  const body = doc.getElementById('sheet-body'), status = doc.getElementById('sheet-status');
  const choice = doc.getElementById('sheet-character'), messages = config.messages.sheet;
  let characters = [], current = null, busy = false, loads = 0;
  function draw() {
    const character = characters.find(item => item.id === current) || characters[0];
    current = character?.id ?? null;
    choice.hidden = characters.length < 2;
    choice.replaceChildren(...characters.map(item => element(doc, 'option', {value: String(item.id), textContent: item.name})));
    if (current !== null) choice.value = String(current);
    body.replaceChildren(character ? renderSheet(doc, character, messages, act, busy) : '');
  }
  async function load() {
    const run = ++loads;
    if (!characters.length) status.textContent = messages.loading;
    try {
      const response = await request(config.sheetsUrl, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (run !== loads) return;
      characters = data.characters; status.textContent = ''; draw();
    } catch (_) {if (run === loads) status.textContent = messages.failed;}
  }
  async function act(change) {
    if (busy || current === null) return;
    busy = true; draw(); status.textContent = '';
    try {
      const response = await request(`${config.sheetsUrl}/${current}`, {method: 'POST',
        headers: {'Content-Type': 'application/json'}, signal: AbortSignal.timeout(15000),
        body: JSON.stringify({...change, csrf_token: config.csrfToken})});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {status.textContent = response.status === 400 && data.reason === 'invalid' ? data.message : messages.saveFailed; return;}
      characters = characters.map(item => item.id === data.id ? data : item);
    } catch (_) {
      status.textContent = messages.saveFailed;
    } finally {busy = false; draw();}
  }
  const open = () => {dialog.showModal(); opener.setAttribute('aria-expanded', 'true'); load();};
  const onClose = () => opener.setAttribute('aria-expanded', 'false');
  const onClick = event => {if (event.target === dialog) dialog.close();};
  const onChoice = () => {current = Number(choice.value); draw();};
  const close = () => dialog.close();
  // Changes from the website, Discord commands or another tab.
  const onChange = data => {if (data?.party_id === config.partyId && dialog.open) load();};
  opener.addEventListener('click', open);
  dialog.addEventListener('close', onClose);
  dialog.addEventListener('click', onClick);
  choice.addEventListener('change', onChoice);
  doc.getElementById('close-sheet')?.addEventListener('click', close);
  socket.on('party_members_changed', onChange);
  return {load, destroy() {
    opener.removeEventListener('click', open); dialog.removeEventListener('close', onClose);
    dialog.removeEventListener('click', onClick); choice.removeEventListener('change', onChoice);
    socket.off?.('party_members_changed', onChange); if (dialog.open) dialog.close();
  }};
}

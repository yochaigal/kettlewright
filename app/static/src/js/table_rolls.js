// Roll on an article's tables (#508): a table keyed by a die gets a Roll button that picks its row.
// A table is rollable when its first column numbers its rows (1, 2, 3… or ranges like 3-5) and the
// numbers cover a die exactly: a header cell like "d4" or "2d6" names the die, otherwise it is read from
// the numbers (1-6 is a d6, 2-12 is 2d6). A table laid out sideways (a header row of numbers over one
// row of results, like the Reactions table) works too. Like a save on the character sheet, the dice roll
// in 3D (when they are on) and the result comes as a notification; the rolled row is marked in the table.
// The roll is the reader's own: nothing is posted to the party.

const DIE = /^\s*(\d*)\s*d\s*(\d+)\s*$/i;
const KEY = /^\s*(\d{1,3})\s*(?:[-–—]\s*(\d{1,3}))?\s*$/;
const SIDES = [2, 3, 4, 6, 8, 10, 12, 20, 100];

// "3", "3-5", "00" (100 on a d100). Null when the cell is not a roll key.
export function parseKey(text) {
  const match = KEY.exec(String(text).replace(/\*/g, ''));
  if (!match) return null;
  const value = digits => (digits === '00' ? 100 : Number(digits));
  const min = value(match[1]), max = match[2] === undefined ? min : value(match[2]);
  return min <= max ? {min, max} : null;
}

function guessDice(min, max) {
  for (let count = 1; count <= 3; count++) {
    for (const sides of SIDES) if (count === min && count * sides === max) return {count, sides};
  }
  return null;
}

// Every value the dice can give is in exactly one key.
function covers(keys, {count, sides}) {
  const seen = new Set();
  for (const {min, max} of keys) for (let value = min; value <= max; value++) {
    if (seen.has(value)) return false;
    seen.add(value);
  }
  for (let value = count; value <= count * sides; value++) if (!seen.has(value)) return false;
  return seen.size === count * sides - count + 1;
}

// rows: the table's cell texts, header row first. Returns {dice, entries: [{min, max, index}], sideways},
// where index is the data row (or, sideways, the column) a result picks; null when it is not a roll table.
export function tableDice(rows) {
  if (!rows?.length || !rows[0]?.length) return null;
  const [header, ...body] = rows;
  const named = DIE.exec(header[0]);
  const make = (dice, entries, sideways = false) => {
    dice ||= guessDice(Math.min(...entries.map(key => key.min)), Math.max(...entries.map(key => key.max)));
    return dice && covers(entries, dice) ? {dice, entries, sideways} : null;
  };
  const namedDice = named ? {count: Number(named[1] || 1), sides: Number(named[2])} : null;
  // Down the first column: the header names the die, or is itself the first numbered row.
  const dataRows = named || !parseKey(header[0]) ? body.map((row, index) => [row, index + 1]) : rows.map((row, index) => [row, index]);
  const down = dataRows.map(([row, index]) => ({...parseKey(row[0]), index, ok: Boolean(parseKey(row[0]))}));
  if (down.length && down.every(entry => entry.ok)) {
    const result = make(namedDice, down.map(({min, max, index}) => ({min, max, index})));
    if (result) return result;
  }
  // Sideways: a header row of keys over the results.
  if (body.length >= 1 && header.every(cell => parseKey(cell))) {
    return make(null, header.map((cell, index) => ({...parseKey(cell), index})), true);
  }
  return null;
}

// Each die's value, for the 3D dice to land on.
export function rollDice({count, sides}, random = Math.random) {
  return Array.from({length: count}, () => Math.floor(random() * sides) + 1);
}

// "Encounters and Signs (d4): 3 — Infected Mossling — Nearby plant life…"
export function rollMessage(title, dice, total, result) {
  return `${title ? `${title} (${diceLabel(dice)})` : diceLabel(dice)}: ${total}${result ? ` — ${result}` : ''}`;
}

export const diceLabel = ({count, sides}) => `${count > 1 ? count : ''}d${sides}`;

function cellTexts(table) {
  return [...table.rows].map(row => [...row.cells].map(cell => cell.textContent.trim()));
}

// The text of a result: its row (or column) without the key.
function resultText(table, found, sideways) {
  const rows = [...table.rows];
  const cells = sideways ? rows.slice(1).map(row => row.cells[found.index]).filter(Boolean)
    : [...rows[found.index].cells].slice(1);
  return cells.map(cell => cell.textContent.trim()).filter(Boolean).join(' — ');
}

// What the table is called: the heading just above it, else the article's title.
function tableTitle(table) {
  for (let node = table.previousElementSibling; node; node = node.previousElementSibling) {
    if (/^H[2-6]$/.test(node.tagName)) return node.textContent.trim();
  }
  return document.querySelector('.wiki-header h1')?.textContent.trim() || '';
}

function highlight(table, found, sideways) {
  table.querySelectorAll('.is-rolled').forEach(node => node.classList.remove('is-rolled'));
  const rows = [...table.rows];
  if (sideways) rows.forEach(row => row.cells[found.index]?.classList.add('is-rolled'));
  else rows[found.index].classList.add('is-rolled');
}

export function enhanceTables(root, labels = {}) {
  for (const table of root.querySelectorAll('table')) {
    if (table.dataset.rollable) continue;
    const info = tableDice(cellTexts(table));
    if (!info) continue;
    table.dataset.rollable = diceLabel(info.dice);
    const bar = document.createElement('div');
    bar.className = 'table-roll';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'table-roll-button';
    button.innerHTML = '<i class="fa-solid fa-dice" aria-hidden="true"></i> ';
    button.append(`${labels.roll || 'Roll'} ${diceLabel(info.dice)}`);
    // Read out for screen readers; the notification is what everyone else sees.
    const status = document.createElement('span');
    status.className = 'table-roll-result sr-only';
    status.setAttribute('role', 'status');
    button.addEventListener('click', async () => {
      const values = rollDice(info.dice), total = values.reduce((sum, value) => sum + value, 0);
      const found = info.entries.find(entry => total >= entry.min && total <= entry.max);
      if (!found) return;
      button.disabled = true;
      try {
        const [{default: dice3d}, {default: notification}] = await Promise.all([import('./dice3d.js'), import('./notification.js')]);
        await dice3d.show({values, sides: values.map(() => info.dice.sides)});
        const message = rollMessage(tableTitle(table), info.dice, total, resultText(table, found, info.sideways));
        highlight(table, found, info.sideways);
        notification.showNotification(message);
        status.textContent = message;
      } finally {
        button.disabled = false;
      }
    });
    bar.append(button, status);
    // Above the table, inside its scroll wrapper when it has one.
    table.before(bar);
  }
}

if (typeof document !== 'undefined') {
  const start = () => {
    const labels = JSON.parse(document.getElementById('table-roll-labels')?.textContent || '{}');
    const enhance = () => document.querySelectorAll('.wiki-content .rich-content').forEach(root => enhanceTables(root, labels));
    enhance();
    // Party pages replace the article as the Warden reveals more (campaign_live.js): enhance the new copy too.
    const wiki = document.querySelector('.campaign-wiki');
    if (wiki) new MutationObserver(enhance).observe(wiki, {childList: true, subtree: true});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
}

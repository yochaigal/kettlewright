// The game system the page plays (kettlewright, #487): its HP, attributes and conditions. base.html puts it in
// <script id="game-system" type="application/json">; without a page (tests, an old cached page) it is Cairn.
// Each stat has its English abbreviation (abbr, e.g. 'STR') and its label in the page's language (label).

const CAIRN = {
  key: 'cairn',
  hp: {key: 'hp', abbr: 'HP', label: 'HP'},
  attributes: [
    {key: 'strength', abbr: 'STR', label: 'STR', save: true},
    {key: 'dexterity', abbr: 'DEX', label: 'DEX', save: true},
    {key: 'willpower', abbr: 'WIL', label: 'WIL', save: true},
  ],
  conditions: [{key: 'deprived', label: 'Deprived'}, {key: 'panicked', label: 'Panicked'}, {key: 'dead', label: 'Dead'}],
};

let cached = null, cachedText = null;

export function gameSystem() {
  const node = globalThis.document?.getElementById?.('game-system');
  const text = node?.textContent;
  if (!text) return CAIRN;
  if (text !== cachedText) {
    try {cached = JSON.parse(text); cachedText = text;} catch (_) {return CAIRN;}
  }
  return cached;
}

// HP, then the attributes.
export function stats() {
  const system = gameSystem();
  return [system.hp, ...system.attributes];
}

export function statKeys() {
  return stats().map(stat => stat.key);
}

// The English abbreviation of a stat ('strength' -> 'STR'), or the key itself if the system has no such stat.
export function statAbbr(key) {
  return stats().find(stat => stat.key === key)?.abbr ?? key;
}

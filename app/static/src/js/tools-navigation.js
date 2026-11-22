import {generateResult} from './content_generators.js';
import {generateSettingArticle} from './setting_articles.js';
import {terrainSource} from './naming.js';

// A tool is one card with one Roll button. `browse` names a search panel opened by a second button;
// `option` names a select the page provides (the character's background); `options` are choices made
// before rolling (Weather's season, shown beside its quick roll).
const tool = (label, category, table = label, extra = {}) => ({label, category, table, ...extra});

// Five tabs, sorted by what the Warden is making. Labels are plain names: "Monster", not "Random monster".
export function toolSections() {
  return {
    world: [
      {label:'People', tools:[tool('People', 'Setting', 'people')]},
      {label:'Factions', tools:[tool('Faction', 'Worldbuilding'), tool('Faction Actions', 'Worldbuilding')]},
      // Dungeon site is the site alone (what it is and how it looks); the full dungeon is under Maps.
      {label:'Places of interest', tools:[...['Settlement','Waypoint','Curiosity','Lair'].map(label => tool(label, 'Setting', label.toLowerCase())),
        tool('Dungeon site', 'Setting', 'dungeon')]},
    ],
    // Everything that can be shown as a map.
    maps: [{label:'Maps', tools:[tool('Realm', 'Worldbuilding'), tool('Dungeon', 'Worldbuilding'), tool('Forest', 'Worldbuilding')]}],
    characters: [{label:'Characters', tools:[tool('Character', 'Character', 'Character', {option:'background'}),
      tool('NPC', 'Worldbuilding')]}],
    encounters: [{label:'Monsters', tools:[tool('Monster', 'Monsters', 'Random Monster', {browse:'Monster picker'}),
      tool('Custom monster', 'Monsters', 'Custom Monster')]}],
    treasure: [{label:'Treasure', tools:[tool('Relic', 'Items', 'Relics', {browse:'Relic picker'}),
      tool('Spellbook', 'Items', 'Spellbooks', {browse:'Spellbook picker'})]}],
  };
}

// Rolled mid-session, so they live only in the Quick rolls row above the tabs, on every tab.
export function quickRolls(data) {
  return [
    tool('Reaction Roll', 'Monsters'),
    tool('Weather', 'Weather', 'Weather', {options:Object.keys(data.Weather?.Types || {})}),
    tool('Dungeon Events', 'Events'),
    tool('Wilderness Events', 'Events'),
  ];
}

export const TAB_STORAGE_KEY = 'kw-tools-tab';
export const OPTION_STORAGE_KEY = 'kw-tools-options';

// The table a roll uses: a tool with options rolls the chosen one (Weather rolls a season).
export function rollTable(item, value) {
  return item.options ? (item.options.includes(value) ? value : item.options[0]) : item.table;
}

export function generateToolResult(data, category, table, random = Math.random) {
  return category === 'Setting'
    ? generateSettingArticle(data, table, random, {generateChildren:false, siteOnly:table === 'dungeon'})
    : generateResult(data, category, table, random);
}

// Sections with a single tool need no heading of their own: neighbours share one row.
export function launcherGroups(sections) {
  const groups = [];
  for (const section of sections) {
    const single = section.tools.length === 1 && sections.length > 1;
    const last = groups.at(-1);
    if (single && last && !last.label) last.tools.push(...section.tools);
    else groups.push({label:single || sections.length === 1 ? '' : section.label, tools:[...section.tools]});
  }
  return groups;
}

function storage(read) {
  try {return read(window.localStorage);} catch {return null;}
}

// One row of tabs; every tool below it is a card with the same layout:
//   name (and a map mark), what it makes, then [Roll] and, only when needed, a second control.
// `panels` maps a `browse` name to its search panel; `selects` maps an `option` name to a select the page
// provides (the character's background). `hints` explains a tool in one line (keyed category:table);
// `intros` explains each tab.
export function initToolsNavigation(data, t, {onRoll, panels = {}, selects = {}, hints = {}, intros = {}, mapTables = []}) {
  const mainTabs = [...document.querySelectorAll('.tools-nav [role=tab]')];
  const panel = document.getElementById('tab-content1');
  const launcher = document.getElementById('tools-launcher');
  const intro = document.getElementById('tools-intro');
  const quick = document.getElementById('tools-quick-rolls');
  const sections = toolSections();
  const open = new Set();
  const values = storage(store => JSON.parse(store.getItem(OPTION_STORAGE_KEY) || '{}')) || {};
  const remember = (name, value) => {
    values[name] = value;
    storage(store => store.setItem(OPTION_STORAGE_KEY, JSON.stringify(values)));
  };
  const valueFor = item => item.options ? values[item.table] : item.option ? selects[item.option]?.value : undefined;

  async function roll(item, key, button) {
    button.disabled = true;
    try {
      await onRoll({...item, table:rollTable(item, valueFor(item))}, key, button, valueFor(item));
    } finally {
      button.disabled = false;
    }
  }

  function makeButton(className, icon, text) {
    const control = document.createElement('button');
    control.type = 'button';
    control.className = className;
    control.innerHTML = `<i class="fa-solid ${icon}" aria-hidden="true"></i> `;
    control.append(text);
    return control;
  }

  function card(item, key, index) {
    const id = `tools-card-${key}-${index}`;
    const block = document.createElement('div');
    block.className = 'tools-card';
    block.setAttribute('role', 'group');
    block.setAttribute('aria-labelledby', `${id}-name`);
    block.dataset.table = item.table;
    const name = document.createElement('span');
    name.className = 'tools-card-name';
    name.id = `${id}-name`;
    name.textContent = t(item.label);
    block.append(name);
    // A map mark when the result can be shown as a map (#473).
    if (mapTables.includes(`${item.category}:${item.table}`)) {
      const mark = document.createElement('i');
      mark.className = 'fa-solid fa-map tools-card-map';
      mark.title = t('Show map');
      mark.setAttribute('aria-hidden', 'true');
      block.append(mark);
    }
    const hint = hints[`${item.category}:${item.table}`];
    if (hint) {
      const line = document.createElement('p');
      line.className = 'tools-card-hint';
      line.id = `${id}-hint`;
      line.textContent = hint;
      block.append(line);
    }
    const row = document.createElement('div');
    row.className = 'tools-card-actions';
    const rollButton = makeButton('tools-roll', 'fa-dice', t('Roll'));
    rollButton.setAttribute('aria-describedby', `${id}-name`);
    rollButton.addEventListener('click', () => roll(item, key, rollButton));
    row.append(rollButton);
    const target = panels[item.browse];
    if (target) {
      const browse = makeButton('tools-browse', 'fa-magnifying-glass', t('Browse'));
      browse.setAttribute('aria-describedby', `${id}-name`);
      browse.setAttribute('aria-controls', target.id);
      browse.setAttribute('aria-expanded', String(open.has(item.browse)));
      browse.addEventListener('click', () => {
        if (!open.delete(item.browse)) open.add(item.browse);
        target.hidden = !open.has(item.browse);
        browse.setAttribute('aria-expanded', String(!target.hidden));
        if (!target.hidden) target.querySelector('input, select')?.focus();
      });
      row.append(browse);
    }
    if (selects[item.option]) {
      const select = selects[item.option];
      select.classList.add('tools-option');
      row.append(select);
    }
    block.append(row);
    return block;
  }

  function selectMain(tab) {
    mainTabs.forEach(other => {
      other.setAttribute('aria-selected', String(other === tab));
      other.tabIndex = other === tab ? 0 : -1;
    });
    const key = tab.dataset.tool;
    storage(store => store.setItem(TAB_STORAGE_KEY, key));
    panel.setAttribute('aria-labelledby', tab.id);
    if (intro) intro.textContent = intros[key] || '';
    launcher.replaceChildren();
    const shown = new Set();
    let index = 0;
    for (const group of launcherGroups(sections[key])) {
      const block = document.createElement('div');
      block.className = 'tools-group';
      block.setAttribute('role', 'group');
      if (group.label) {
        const label = document.createElement('div');
        label.className = 'tools-group-label';
        label.id = `tools-${key}-group-${launcher.childElementCount}`;
        label.textContent = t(group.label);
        block.setAttribute('aria-labelledby', label.id);
        block.append(label);
      } else {
        block.setAttribute('aria-label', tab.textContent.trim());
      }
      const row = document.createElement('div');
      row.className = 'tools-group-choices';
      for (const item of group.tools) row.append(card(item, key, index++));
      block.append(row);
      launcher.append(block);
      // A search panel opens right under the cards that open it.
      for (const item of group.tools) if (panels[item.browse]) {
        shown.add(item.browse);
        launcher.append(panels[item.browse]);
      }
    }
    for (const [name, target] of Object.entries(panels)) target.hidden = !(shown.has(name) && open.has(name));
  }

  if (quick) {
    const label = document.createElement('span');
    label.className = 'tools-quick-label';
    label.id = 'tools-quick-label';
    label.textContent = t('Quick rolls');
    quick.setAttribute('role', 'group');
    quick.setAttribute('aria-labelledby', label.id);
    quick.append(label);
    for (const item of quickRolls(data)) {
      const control = makeButton('tools-quick-roll', 'fa-dice', t(item.label));
      const hint = hints[`${item.category}:${item.table}`];
      if (hint) control.title = hint;
      control.addEventListener('click', () => roll(item, 'quick', control));
      if (!item.options?.length) {
        quick.append(control);
        continue;
      }
      // Weather keeps its season beside it.
      const pair = document.createElement('span');
      pair.className = 'tools-quick-pair';
      const select = document.createElement('select');
      select.className = 'tools-quick-option';
      select.setAttribute('aria-label', `${t(item.label)}: ${t('Season')}`);
      for (const option of item.options) select.append(new Option(t(option), option));
      select.value = rollTable(item, values[item.table]);
      select.addEventListener('change', () => remember(item.table, select.value));
      pair.append(control, select);
      quick.append(pair);
    }
  }

  mainTabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectMain(tab));
    tab.addEventListener('keydown', event => {
      const next = {ArrowRight:(index+1)%mainTabs.length, ArrowLeft:(index+mainTabs.length-1)%mainTabs.length, Home:0, End:mainTabs.length-1}[event.key];
      if (next === undefined) return;
      event.preventDefault();
      selectMain(mainTabs[next]);
      mainTabs[next].focus();
    });
  });
  // The last tab used, or the first.
  const saved = storage(store => store.getItem(TAB_STORAGE_KEY));
  selectMain(mainTabs.find(tab => tab.dataset.tool === saved) || mainTabs[0]);
  return {open(key, table) {
    const tab = mainTabs.find(tab => tab.dataset.tool === key);
    if (!tab) return;
    selectMain(tab);
    const target = table && [...launcher.querySelectorAll('.tools-card')].find(node => node.dataset.table === table);
    (target?.querySelector('.tools-roll') || tab).focus();
  }};
}

// Keep the result intact; shortcuts only select a generator, never reroll it.
export function appendAreaNavigation(container, result, navigation, t, data = {}) {
  const kinds = new Set();
  if (result.mapKind === 'realm') {
    for (const kind of result.poiKinds || []) kinds.add(kind);
    if ((result.fields.Terrain || []).some(terrain => /forest|woodland|jungle|taiga|mangrove|thicket/i.test(terrainSource(data, terrain.split('. Difficulty:')[0])))) kinds.add('forest');
  } else if (result.category === 'dungeon' && !result.mapKind) {
    kinds.add('dungeon');
  }
  const actions = document.createElement('div');
  actions.className = 'campaign-actions';
  for (const [kind, table] of [['dungeon','Dungeon'], ['forest','Forest']]) {
    if (!kinds.has(kind)) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${t('Maps')}: ${t(table)} →`;
    button.addEventListener('click', () => navigation.open('maps', table));
    actions.append(button);
  }
  if (actions.childElementCount) container.prepend(actions);
}

import {generateResult} from './content_generators.js';
import {generateSettingArticle} from './setting_articles.js';
import {terrainSource} from './naming.js';

const choice = (label, category, table = label) => ({label, category, table});
export function toolSections(data) {
  return {
    realm: [
      {label:'Realm', choices:[choice('Realm', 'Worldbuilding')]},
      {label:'Factions', choices:[choice('Faction', 'Worldbuilding')]},
      {label:'POIs', choices:['Settlement','Waypoint','Curiosity','Lair','Dungeon'].map(label => choice(label, 'Setting', label.toLowerCase()))},
      {label:'People', choices:[choice('People', 'Setting', 'people'), choice('NPC', 'Worldbuilding')]},
    ],
    dungeons: [{label:'Dungeon', choices:[choice('Dungeon', 'Worldbuilding')]}],
    forests: [{label:'Forest', choices:[choice('Forest', 'Worldbuilding')]}],
    events: [
      {label:'Events', choices:[choice('Dungeon Events', 'Events'), choice('Wilderness Events', 'Events')]},
      {label:'Weather', choices:Object.keys(data.Weather.Types).map(label => choice(label, 'Weather'))},
      {label:'Reaction Roll', choices:[choice('Reaction Roll', 'Monsters')]},
      {label:'Faction Actions', choices:[choice('Faction Actions', 'Worldbuilding')]},
    ],
    monsters: [
      {label:'Generator', choices:[choice('Random Monster', 'Monsters'), choice('Custom Monster', 'Monsters'), choice('Monster picker', 'Monsters')]},
    ],
    items: [{label:'Items', choices:[choice('Relics', 'Items'), choice('Spellbooks', 'Items')]}],
  };
}

export function generateToolResult(data, category, table, random = Math.random) {
  return category === 'Setting'
    ? generateSettingArticle(data, table, random, {generateChildren:false, siteOnly:table === 'dungeon'})
    : generateResult(data, category, table, random);
}

// Sections with a single table need no heading of their own: neighbours share one row.
export function launcherGroups(sections) {
  const groups = [];
  for (const section of sections) {
    const single = section.choices.length === 1 && sections.length > 1;
    const last = groups.at(-1);
    if (single && last && !last.label) last.choices.push(...section.choices);
    else groups.push({label:single || sections.length === 1 ? '' : section.label, choices:[...section.choices]});
  }
  return groups;
}

// One row of area tabs; every table below it rolls with a single click.
// `panels` maps a table name to an element that the table shows instead of rolling.
export function initToolsNavigation(data, t, {onRoll, panels = {}}) {
  const mainTabs = [...document.querySelectorAll('.tools-nav [role=tab]')];
  const panel = document.getElementById('tab-content1');
  const pcPanel = document.getElementById('tab-content2');
  const launcher = document.getElementById('tools-launcher');
  const sections = toolSections(data);
  const open = new Set();

  function selectMain(tab) {
    mainTabs.forEach(other => {
      other.setAttribute('aria-selected', String(other === tab));
      other.tabIndex = other === tab ? 0 : -1;
    });
    const key = tab.dataset.tool;
    panel.hidden = !key;
    pcPanel.hidden = !!key;
    if (!key) return;
    panel.setAttribute('aria-labelledby', tab.id);
    launcher.replaceChildren();
    const shown = new Set();
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
      for (const item of group.choices) {
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'button tools-choice';
        control.textContent = t(item.label);
        const target = panels[item.table];
        if (target) {
          shown.add(item.table);
          control.classList.add('tools-choice-toggle');
          control.setAttribute('aria-controls', target.id);
          control.setAttribute('aria-expanded', String(open.has(item.table)));
          control.addEventListener('click', () => {
            if (!open.delete(item.table)) open.add(item.table);
            target.hidden = !open.has(item.table);
            control.setAttribute('aria-expanded', String(!target.hidden));
            if (!target.hidden) target.querySelector('input, select')?.focus();
          });
        } else {
          control.addEventListener('click', () => onRoll(item, key, control));
        }
        row.append(control);
      }
      block.append(row);
      launcher.append(block);
    }
    for (const [table, target] of Object.entries(panels)) target.hidden = !(shown.has(table) && open.has(table));
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
  selectMain(mainTabs[0]);
  return {open(key) {
    const tab = mainTabs.find(tab => tab.dataset.tool === key);
    if (tab) {selectMain(tab); tab.focus();}
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
  for (const [kind, key, label] of [['dungeon','dungeons','Dungeon'], ['forest','forests','Forest']]) {
    if (!kinds.has(kind)) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${t('POIs')}: ${t(label)} →`;
    button.addEventListener('click', () => navigation.open(key));
    actions.append(button);
  }
  if (actions.childElementCount) container.prepend(actions);
}

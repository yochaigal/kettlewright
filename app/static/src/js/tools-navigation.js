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

// Both Tools renderers share navigation while keeping their existing output/save behavior.
export function initToolsNavigation(data, t, onSelect) {
  const mainTabs = [...document.querySelectorAll('.tools-tabs > .tools-tab-list [role=tab]')];
  const panel = document.getElementById('tab-content1');
  const pcPanel = document.getElementById('tab-content2');
  const sectionTabs = document.getElementById('tools-section-tabs');
  const tablePanel = document.getElementById('tools-table-panel');
  const choices = document.getElementById('subcategory-buttons');
  const sections = toolSections(data);
  const remembered = new Map();

  function bindTabs(tabs, select) {
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', event => {
        const next = {ArrowRight:(index+1)%tabs.length, ArrowLeft:(index+tabs.length-1)%tabs.length, Home:0, End:tabs.length-1}[event.key];
        if (next === undefined) return;
        event.preventDefault();
        select(tabs[next]);
        tabs[next].focus();
      });
    });
  }
  function mark(tabs, selected) {
    tabs.forEach(tab => {
      tab.setAttribute('aria-selected', String(tab === selected));
      tab.tabIndex = tab === selected ? 0 : -1;
    });
  }
  function selectMain(tab) {
    mark(mainTabs, tab);
    const key = tab.dataset.tool;
    panel.hidden = !key;
    pcPanel.hidden = !!key;
    if (!key) return;
    panel.setAttribute('aria-labelledby', tab.id);
    sectionTabs.replaceChildren();
    sectionTabs.hidden = sections[key].length < 2;
    const tabs = sections[key].map((section, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.id = `tools-${key}-section-${index}`;
      button.textContent = t(section.label);
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-controls', 'tools-table-panel');
      sectionTabs.append(button);
      return button;
    });
    function selectSection(button) {
      mark(tabs, button);
      const index = tabs.indexOf(button), section = sections[key][index];
      remembered.set(key, index);
      tablePanel.hidden = false;
      tablePanel.setAttribute('aria-labelledby', sectionTabs.hidden ? tab.id : button.id);
      choices.replaceChildren();
      document.getElementById('tools-table-choices').hidden = section.choices.length < 2;
      onSelect('', '', key);
      const buttons = section.choices.map(item => {
        const control = document.createElement('button');
        control.type = 'button';
        control.className = 'button tools-choice';
        control.textContent = t(item.label);
        control.setAttribute('aria-pressed', 'false');
        control.addEventListener('click', () => {
          buttons.forEach(other => other.setAttribute('aria-pressed', String(other === control)));
          onSelect(item.category, item.table, key);
        });
        choices.append(control);
        return control;
      });
      if (buttons.length === 1) buttons[0].click();
    }
    bindTabs(tabs, selectSection);
    selectSection(tabs[remembered.get(key) ?? 0]);
  }
  bindTabs(mainTabs, selectMain);
  selectMain(mainTabs[0]);
  return {open(key) {
    const tab = mainTabs.find(tab => tab.dataset.tool === key);
    if (tab) {selectMain(tab); tab.focus();}
  }};
}

// Keep the realm result intact; shortcuts only select a generator, never reroll it.
export function appendRealmNavigation(container, result, navigation, t, data = {}) {
  if (result.mapKind !== 'realm') return;
  const kinds = new Set(result.poiKinds || []);
  if ((result.fields.Terrain || []).some(terrain => /forest|woodland|jungle|taiga|mangrove|thicket/i.test(terrainSource(data, terrain.split('. Difficulty:')[0])))) kinds.add('forest');
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

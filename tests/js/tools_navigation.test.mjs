import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {toolSections, launcherGroups, generateToolResult, appendAreaNavigation, rollTable, quickRolls} from '../../app/static/src/js/tools-navigation.js';
import {resultText} from '../../app/static/src/js/content_generators.js';
import {itemMarkdown} from '../../app/static/src/js/tools-items.js';

const data = {};
for (const name of ['dungeons','forests','realm','factions','npcs','names','faction-events','bestiary','custom-monster','reactions','weather','dungeon-events','wilderness-events','reliquary','spellbooks']) {
  Object.assign(data, JSON.parse(readFileSync(new URL(`../../system/cairn/content/generators/${name}.json`, import.meta.url))));
}

const tabTools = () => Object.values(toolSections()).flat().flatMap(section => section.tools);
const allTools = () => [...tabTools(), ...quickRolls(data)];

test('every tool rolls usable content', () => {
  for (const tool of allTools()) {
    // The bestiary and the character come from the page and the server, not the tables.
    if (tool.table === 'Random Monster' || tool.category === 'Character') continue;
    for (const table of tool.options || [tool.table]) {
      const result = generateToolResult(data, tool.category, table, () => 0.4);
      assert.ok(result.title, tool.label);
      const text = resultText(result);
      assert.ok(text.length > 0, tool.label);
      assert.ok(!text.includes('undefined'), tool.label);
      if (['Dungeon','Forest','Realm'].includes(table)) assert.ok(result.mapKind);
    }
  }
});

test('five tabs in the rulebooks\' order and the quick rolls keep every original table once', () => {
  const sections = toolSections();
  // The rulebooks' order: Setting Seeds, Dungeon and Forest Seeds, the Bestiary, Spellbooks and the Reliquary, characters.
  assert.deepEqual(Object.keys(sections), ['setting', 'seeds', 'bestiary', 'spellbooks', 'characters']);
  const tables = allTools().flatMap(tool => (tool.options || [tool.table]).map(table => `${tool.category}:${table}`));
  const original = {
    Worldbuilding:['Dungeon','Forest','Realm','Faction','Faction Actions','NPC'],
    Monsters:['Random Monster','Custom Monster','Reaction Roll'],
    Events:['Dungeon Events','Wilderness Events'], Weather:Object.keys(data.Weather.Types), Items:['Relics','Spellbooks'],
    Setting:['settlement','waypoint','curiosity','lair','dungeon','people'],
  };
  for (const [category, list] of Object.entries(original)) for (const table of list) {
    assert.equal(tables.filter(key => key === `${category}:${table}`).length, 1, table);
  }
  const labels = key => sections[key].map(section => [section.label, section.tools.map(tool => tool.label)]);
  assert.deepEqual(labels('setting'), [['Realm', ['Realm']], ['People', ['People']], ['Factions', ['Faction', 'Faction Actions']],
    ['Points of interest', ['Settlement','Waypoint','Curiosity','Lair','Dungeon site']]]);
  assert.deepEqual(labels('seeds'), [['Dungeons & Forests', ['Dungeon', 'Forest']]]);
  assert.deepEqual(labels('bestiary'), [['Bestiary', ['Monster', 'Custom monster']]]);
  assert.deepEqual(labels('spellbooks'), [['Spellbooks & Relics', ['Spellbook', 'Relic']]]);
  assert.deepEqual(labels('characters'), [['Characters', ['Character', 'NPC']]]);
});

test('every tool is one Roll button, with a second control only when it needs one', () => {
  const extra = Object.fromEntries(allTools().filter(tool => tool.browse || tool.option || tool.options)
    .map(tool => [tool.label, tool.browse || tool.option || 'options']));
  assert.deepEqual(extra, {Monster:'Monster picker', Spellbook:'Spellbook picker', Relic:'Relic picker',
    Character:'background', Weather:'options'});
  // Plain names: one Monster, one Relic, one Spellbook, not "Random X" next to "X picker".
  assert.ok(!allTools().some(tool => /^Random |picker$/.test(tool.label)));
});

test('Weather rolls the chosen season, or the first one', () => {
  const weather = allTools().find(tool => tool.label === 'Weather');
  assert.deepEqual(weather.options, Object.keys(data.Weather.Types));
  assert.equal(rollTable(weather, 'Winter'), 'Winter');
  assert.equal(rollTable(weather, 'Nonsense'), weather.options[0]);
  assert.equal(rollTable(weather, undefined), weather.options[0]);
  assert.equal(rollTable({table:'Realm'}, 'Winter'), 'Realm');
});

test('quick rolls are only quick rolls, never also a card on a tab', () => {
  assert.deepEqual(quickRolls(data).map(tool => tool.label), ['Reaction Roll', 'Weather', 'Dungeon Events', 'Wilderness Events']);
  const onTabs = tabTools().map(tool => `${tool.category}:${tool.table}`);
  for (const tool of quickRolls(data)) assert.ok(!onTabs.includes(`${tool.category}:${tool.table}`), tool.label);
  // The realm is a Setting Seed; the full dungeon and forest are their own seeds.
  assert.deepEqual(toolSections().setting[0].tools.map(tool => tool.table), ['Realm']);
  assert.deepEqual(toolSections().seeds[0].tools.map(tool => tool.table), ['Dungeon', 'Forest']);
});

test('Dungeon site rolls the dungeon site tables without generating a full dungeon', () => {
  const choice = toolSections().setting.flatMap(section => section.tools).find(tool => tool.label === 'Dungeon site');
  assert.ok(choice);
  const result = generateToolResult(data, choice.category, choice.table, () => 0);
  assert.deepEqual(result.fields, {Type:'Burial Ground', Feature:'Abandoned'});
  assert.equal(result.category, 'dungeon');
  assert.ok(!result.mapKind);
});

test('event text preserves the event description without a redundant field label', () => {
  for (const table of ['Dungeon Events', 'Wilderness Events']) {
    const result = generateToolResult(data, 'Events', table, () => 0);
    assert.equal(resultText(result, key => key), data[table][0].description);
    assert.ok(!resultText(result).includes('**Description:**'));
  }
});

test('area shortcuts open full generators without changing or rerolling the source result', () => {
  const originalDocument = globalThis.document;
  globalThis.document = {getElementById() {return null;}, createElement() {
    return {
      children:[], listeners:{},
      append(child) {this.children.push(child);},
      get childElementCount() {return this.children.length;},
      addEventListener(event, callback) {this.listeners[event] = callback;},
    };
  }};
  try {
    for (const [result, expected] of [
      [generateToolResult(data, 'Setting', 'dungeon', () => 0), [['seeds', 'Dungeon']]],
      [{mapKind:'realm', poiKinds:['dungeon'], fields:{Terrain:['Forest. Difficulty: Easy']}}, [['seeds', 'Dungeon'], ['seeds', 'Forest']]],
      [generateToolResult(data, 'Worldbuilding', 'Dungeon', () => 0), []],
      [generateToolResult(data, 'Setting', 'settlement', () => 0), []],
    ]) {
      const before = JSON.stringify(result), actions = [];
      const opened = [];
      appendAreaNavigation({prepend(child) {actions.push(child);}}, result, {open(key, table) {opened.push([key, table]);}}, key => key, data);
      for (const button of actions[0]?.children || []) button.listeners.click();
      assert.deepEqual(opened, expected);
      assert.equal(JSON.stringify(result), before);
    }
  } finally {
    globalThis.document = originalDocument;
  }
});

test('the launcher shows every tool once and only labels groups that need a heading', () => {
  const sections = toolSections();
  for (const [key, list] of Object.entries(sections)) {
    assert.deepEqual(launcherGroups(list).flatMap(group => group.tools), list.flatMap(section => section.tools), key);
  }
  const shape = key => launcherGroups(sections[key]).map(group => [group.label, group.tools.map(tool => tool.label)]);
  // Realm and People have one tool each, so they share a row without a heading.
  assert.deepEqual(shape('setting'), [
    ['', ['Realm', 'People']],
    ['Factions', ['Faction','Faction Actions']],
    ['Points of interest', ['Settlement','Waypoint','Curiosity','Lair','Dungeon site']],
  ]);
  for (const key of ['seeds','bestiary','spellbooks','characters']) assert.deepEqual(shape(key).map(([label]) => label), ['']);
});

test('the Relic and Spellbook pickers list every one, shown like a rolled one', async () => {
  const {itemCatalog} = await import('../../app/static/src/js/tools-items.js');
  const relics = itemCatalog(data, 'Relics'), spellbooks = itemCatalog(data, 'Spellbooks');
  assert.equal(Object.keys(relics).length, data.Relics.length);
  assert.equal(Object.keys(spellbooks).length, data.Spellbooks.length);
  // A pick is the same result a roll on that table gives.
  assert.deepEqual(relics['relic:A Blade Called Hope'], generateToolResult(data, 'Items', 'Relics', () => 0));
  assert.deepEqual(spellbooks['spellbook:Adhere'], generateToolResult(data, 'Items', 'Spellbooks', () => 0));
  // Relics read like spellbooks: no repeated name, tags then what it does.
  const text = resultText(relics['relic:A Blade Called Hope']);
  assert.ok(text.startsWith('_d6_ — A thin, curved sword'), text);
  assert.ok(!text.includes('Name:') && !text.includes('### Tags'));
});

test('a relic or spellbook saves as a module item (#476): its tags, uses and charges, then what it does', () => {
  const relic = fields => itemMarkdown({title: 'Thing', category: 'relic', fields: {description: 'Does it.', ...fields}});
  assert.equal(relic({tags: ['charge', 'petty'], charge: 1, max_charges: 1}), '### Thing [charges 1/1, petty]\nDoes it.\n');
  assert.equal(relic({tags: ['charges', 'd8'], charges: 2, max_charges: 2}), '### Thing [charges 2/2, d8]\nDoes it.\n');
  assert.equal(relic({tags: ['use'], uses: 1}), '### Thing [uses 1]\nDoes it.\n');
  assert.equal(relic({tags: ['+1 Armor', 'bulky']}), '### Thing [+1 Armor, bulky]\nDoes it.\n');
  assert.equal(relic({tags: []}), '### Thing\nDoes it.\n');
  assert.equal(itemMarkdown({title: 'Adhere', category: 'spellbook', fields: {tags: [], description: 'Sticky slime.',
    personality: 'Objects stick to it.'}}), '### Adhere\nSticky slime.\n\n_Objects stick to it._\n');
  // Every relic in the tables reads back as one item.
  for (const item of data.Relics) assert.match(itemMarkdown({title: item.name, category: 'relic', fields: item}), /^### /);
});

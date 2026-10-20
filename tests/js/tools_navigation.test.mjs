import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {toolSections, generateToolResult, appendAreaNavigation} from '../../app/static/src/js/tools-navigation.js';
import {resultText} from '../../app/static/src/js/content_generators.js';

const data = {};
for (const name of ['dungeons','forests','realm','factions','npcs','names','faction-events','bestiary','custom-monster','reactions','weather','dungeon-events','wilderness-events','reliquary','spellbooks']) {
  Object.assign(data, JSON.parse(readFileSync(new URL(`../../app/static/json/generators/${name}.json`, import.meta.url))));
}

test('every table in the campaign-aligned navigation produces usable content', () => {
  for (const sections of Object.values(toolSections(data))) for (const section of sections) for (const choice of section.choices) {
    if (choice.table === 'Monster picker') continue;
    const result = generateToolResult(data, choice.category, choice.table, () => 0.4);
    assert.ok(result.title, choice.label);
    const text = resultText(result);
    assert.ok(text.length > 0, choice.label);
    assert.ok(!text.includes('undefined'), choice.label);
    if (['Dungeon','Forest','Realm'].includes(choice.table)) assert.ok(result.mapKind);
  }
});

test('reorganization retains every original table with its original generator', () => {
  const choices = Object.values(toolSections(data)).flat().flatMap(section => section.choices);
  const original = {
    Worldbuilding:['Dungeon','Forest','Realm','Faction','Faction Actions','NPC'],
    Monsters:['Random Monster','Custom Monster','Reaction Roll'],
    Events:['Dungeon Events','Wilderness Events'], Weather:Object.keys(data.Weather.Types), Items:['Relics','Spellbooks'],
  };
  for (const [category, tables] of Object.entries(original)) for (const table of tables) {
    assert.equal(choices.filter(choice => choice.category === category && choice.table === table).length, 1, table);
  }
  assert.deepEqual(toolSections(data).realm.map(section => section.label), ['Realm','Factions','POIs','People']);
  assert.equal(toolSections(data).monsters.length, 1);
  assert.deepEqual(toolSections(data).monsters[0].choices.map(choice => choice.label), ['Random Monster','Custom Monster','Monster picker']);
});


test('Realm POIs roll the dungeon site tables without generating a full dungeon', () => {
  const choice = toolSections(data).realm.find(section => section.label === 'POIs').choices.find(choice => choice.table === 'dungeon');
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
      [generateToolResult(data, 'Setting', 'dungeon', () => 0), ['dungeons']],
      [{mapKind:'realm', poiKinds:['dungeon'], fields:{Terrain:['Forest. Difficulty: Easy']}}, ['dungeons','forests']],
      [generateToolResult(data, 'Worldbuilding', 'Dungeon', () => 0), []],
      [generateToolResult(data, 'Setting', 'settlement', () => 0), []],
    ]) {
      const before = JSON.stringify(result), actions = [];
      const opened = [];
      appendAreaNavigation({prepend(child) {actions.push(child);}}, result, {open(key) {opened.push(key);}}, key => key, data);
      for (const button of actions[0]?.children || []) button.listeners.click();
      assert.deepEqual(opened, expected);
      assert.equal(JSON.stringify(result), before);
    }
  } finally {
    globalThis.document = originalDocument;
  }
});

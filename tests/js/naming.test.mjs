import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {settingName} from '../../app/static/src/js/naming.js';

const data=JSON.parse(readFileSync(new URL('../../app/static/json/generators/names.json',import.meta.url)));
test('official naming tables retain dice sizes and source order',()=>{
  for(const table of [data.Names.Adjectives,data.Names.Nouns,data.Names.ForestNames.Adjectives,data.Names.ForestNames.Nouns])assert.equal(table.length,100);
  assert.equal(data.Names.Nouns[6],'Bastion');
  assert.equal(data.Names.Nouns[99],'Zephyr');
  assert.equal(data.Names.RulerTypes[1],'Barony');
  assert.equal(data.Names.GroupTypes.length,20);
  assert.equal(data.Names.RulerTypes.length,20);
});
test('all six place formulas use the concrete site instead of the category',()=>{
  const expected=['The Abyss Tower','The Aging Tower','Tower of the Abyss','Aging Tower of the Abyss',
    'The Abyss Aging Tower','Tower of the Aging Abyss'];
  expected.forEach((name,i)=>{
    const rolls=[(i+0.01)/6,0,0];
    assert.equal(settingName(data,'waypoint',{Waypoint:'Tower'},'',()=>rolls.shift() ?? 0),name);
  });
});
test('realm, faction, forest and terrain use their specific tables',()=>{
  assert.equal(settingName(data,'realm',{},'',()=>0),'The Abyss Alliance');
  assert.equal(settingName(data,'faction',{},'',()=>0),'The Abyss Assembly');
  assert.equal(settingName(data,'forest',{},'',()=>0),'Abandoned Arbors');
  assert.equal(settingName(data,'terrain',{Terrain:'Forests'},'',()=>0),'The Abyss Bush');
  assert.equal(settingName(data,'water',{Type:'River'},'',()=>0),'The Abyss River');
  assert.equal(settingName(data,'culture',{},'Stoic · Division',()=>0),'Stoic · Division');
  assert.equal(settingName({},'realm',{},'Existing title',()=>0),'Existing title');
});

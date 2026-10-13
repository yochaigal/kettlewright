import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {settingName} from '../../app/static/src/js/naming.js';
import pointcrawl from '../../app/static/src/js/alpine/components/pointcrawl.js';

const data=JSON.parse(readFileSync(new URL('../../app/static/json/generators/names.json',import.meta.url)));

test('manually connected paths use naming dictionaries and reject duplicate clicks',async()=>{
  const component=pointcrawl();
  component.graph={nodes:[{id:7,number:7},{id:9,number:9}],edges:[]};
  component.edgeSource='7';component.edgeTarget='9';component.labels={duplicate:'Duplicate',error:'Failed'};
  let resolveTables;
  component.loadTables=()=>new Promise(resolve=>{resolveTables=resolve;});
  const pending=component.addEdge();
  await component.addEdge();
  assert.equal(component.graph.edges.length,0);
  resolveTables(data);await pending;
  assert.equal(component.graph.edges.length,1);
  const edge=component.graph.edges[0];
  assert.match(edge.title,/Path/);
  assert.notEqual(edge.title,'7 – 9');
  assert.equal(edge.source,'7');assert.equal(edge.target,'9');
  assert.equal(edge.path_type,'standard');assert.equal(edge.body,'');
  component.edgeSource='9';component.edgeTarget='7';
  await component.addEdge();
  assert.equal(component.graph.edges.length,1);
  assert.equal(component.graph.edges[0].title,edge.title);
});

test('failed naming-table load leaves the drawing unchanged and allows retry',async()=>{
  const component=pointcrawl();
  component.graph={nodes:[{id:1},{id:2}],edges:[]};
  component.edgeSource='1';component.edgeTarget='2';component.labels={error:'Failed'};
  component.loadTables=async()=>{throw new Error('Offline');};
  await component.addEdge();
  assert.equal(component.graph.edges.length,0);
  assert.equal(component.status,'Failed');assert.equal(component.generating,false);
  component.loadTables=async()=>data;
  await component.addEdge();
  assert.equal(component.graph.edges.length,1);
});
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

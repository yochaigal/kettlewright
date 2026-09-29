import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {generateResult, graphFromResult, resultText} from '../../app/static/src/js/content_generators.js';

const data={};
for (const name of ['dungeons','forests','realm','factions','npcs','faction-events','bestiary','custom-monster','reactions','weather','dungeon-events','wilderness-events','reliquary','spellbooks']) {
  Object.assign(data,JSON.parse(readFileSync(new URL(`../../app/static/json/generators/${name}.json`,import.meta.url))));
}
function rng(seed) {return () => {seed=(seed*1664525+1013904223)>>>0; return seed/4294967296;};}
for (const type of ['Dungeon','Forest','Realm']) test(`${type}: deterministic tables, connected graph and preserved results`,()=>{
  for (let seed=1;seed<=20;seed++) {
    const result=generateResult(data,'Worldbuilding',type,rng(seed));
    assert.deepEqual(result,generateResult(data,'Worldbuilding',type,rng(seed)));
    const graph=graphFromResult(result,rng(seed));
    assert.equal(graph.nodes.length,result.fields.POIs.length);
    assert.deepEqual(graph.nodes.map(n=>n.body),result.fields.POIs);
    assert.equal(graph.body,resultText(result));
    assert(!graph.body.includes('undefined'));
    const visited=new Set([graph.nodes[0].id]);
    for (let i=0;i<graph.nodes.length;i++) for (const edge of graph.edges) {
      if (visited.has(edge.source)) visited.add(edge.target);
      if (visited.has(edge.target)) visited.add(edge.source);
    }
    assert.equal(visited.size,graph.nodes.length);
    assert(graph.edges.length>=graph.nodes.length); // At least one loop.
    assert.equal(new Set(graph.edges.map(e=>[e.source,e.target].sort().join(':'))).size,graph.edges.length);
    if (type==='Forest') assert(graph.edges.every(e=>result.fields.trails.includes(e.body)));
  }
});
test('all existing Tools categories still produce structured content',()=>{
  const categories={Worldbuilding:['NPC','Faction','Faction Actions'],Monsters:['Random Monster','Custom Monster','Reaction Roll'],
    Events:['Dungeon Events','Wilderness Events'],Weather:Object.keys(data.Weather.Types),Items:['Relics','Spellbooks']};
  for (const [category,types] of Object.entries(categories)) for (const type of types) {
    const result=generateResult(data,category,type,rng(12));
    assert.equal(typeof result.title,'string');
    assert(resultText(result).length>0);
    assert(!resultText(result).includes('undefined'),`${category} ${type}`);
  }
});

test('region drafts generate real dungeon and forest maps without rerolling the region',()=>{
  const tables=structuredClone(data);
  tables.Realm.PointsOfInterest.POI=['Dungeon','Forest'];
  const kinds=new Set();
  for (let seed=1;seed<=12;seed++) {
    const result=generateResult(tables,'Worldbuilding','Realm',rng(seed));
    const before=JSON.stringify(result);
    const graph=graphFromResult(result,rng(seed),tables);
    assert.equal(JSON.stringify(result),before);
    assert.deepEqual(graph,graphFromResult(result,rng(seed),tables));
    for (const node of graph.nodes) {
      const nested=node.nested_draft;
      kinds.add(nested.kind);
      assert.equal(nested.kind,node.poi_kind);
      assert.equal(nested.title,node.title);
      assert(nested.nodes.length>0);
      assert(nested.edges.length>=nested.nodes.length);
      assert(nested.nodes.every(child=>!child.nested_draft));
    }
  }
  assert.deepEqual(kinds,new Set(['dungeon','forest']));
});

test('dungeon and region paths roll all three types reproducibly',()=>{
  for (const type of ['Dungeon','Realm']) {
    const kinds=new Set();
    for (let seed=1;seed<=20;seed++) {
      const result=generateResult(data,'Worldbuilding',type,rng(seed));
      const graph=graphFromResult(result,rng(seed));
      assert.deepEqual(graph,graphFromResult(result,rng(seed)));
      for (const edge of graph.edges) kinds.add(edge.path_type);
    }
    assert.deepEqual([...kinds].sort(),['conditional','hidden','standard']);
  }
});

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

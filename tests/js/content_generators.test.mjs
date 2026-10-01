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
      if (node.number===1) {assert.equal(node.poi_kind,'settlement');assert(!nested);continue;}
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

test('map dice counts are respected and Realm starts with its Heart',()=>{
  for(const type of ['Dungeon','Forest','Realm']) for(const count of [3,6,8,12,20]) {
    const result=generateResult(data,'Worldbuilding',type,rng(4),{poiCount:count});
    assert.equal(result.fields.POIs.length,count);
    if(type==='Realm') {
      assert.equal(result.poiKinds[0],'settlement');
      assert.match(result.fields.POIs[0],/^Heart · Settlement:/);
    }
  }
});

test('spellbooks and equipment use compact Cairn descriptions',()=>{
  assert.equal(resultText({category:'spellbook',fields:{name:'Illusion',description:'A sound appears.',personality:'Whispers at night.'}}),
    'A sound appears. _Whispers at night._');
  assert.equal(resultText({category:'item',title:'Shield',fields:{tags:['1 Armor','bonus defense'],cost:10}}),'Shield (+1 Armor). 10gp.');
  assert.equal(resultText({category:'item',title:'Rations',fields:{tags:['uses'],uses:3,cost:10}}),'Rations (3 uses). 10gp.');
  assert.equal(resultText({category:'item',title:'Sword',fields:{tags:['d8','bulky'],cost:20}}),'Sword (d8, bulky). 20gp.');
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

test('every Article category has a complete editable draft from shared rules tables', async()=>{
  const {generateArticle}=await import('../../app/static/src/js/content_generators.js');
  data.Equipment=JSON.parse(readFileSync(new URL('../../app/static/json/marketplace.json',import.meta.url)));
  for(const category of ['overview','npc','location','lore','faction','relic','note','bestiary','item','spellbook','culture','map']) {
    const draft=generateArticle(data,category,'',rng(9));
    assert.equal(draft.category,category);
    assert(draft.title.length>0 && draft.title.length<=200);
    assert(draft.body.length>0 && !draft.body.includes('undefined'),category);
  }
  assert.equal(generateArticle(data,'custom'),null);
});
test('generated map labels retain their rolled descriptions without invented names',()=>{
  for(const kind of ['Dungeon','Forest','Realm']){
    const result=generateResult(data,'Worldbuilding',kind,rng(16));
    assert(result.title.startsWith(kind+':'));
    const graph=graphFromResult(result,rng(1));
    for(const node of graph.nodes)assert.equal(node.title,node.body.replace(/\s+/g,' ').trim().slice(0,200));
  }
});

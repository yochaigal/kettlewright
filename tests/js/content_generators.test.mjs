import test from 'node:test';
import {article} from '../../app/static/src/js/setting_articles.js';
import assert from 'node:assert/strict';

test('setting headings use rolled values and preserve custom names',()=>{
  for(const [category,placeholder,fields,expected] of [
    ['culture','Culture',{Character:'Struggling',Ambition:'Conversion'},'Struggling · Conversion'],
    ['resources','Resources',{Abundance:'Gemstones',Scarcity:'Land'},'Abundance: Gemstones · Scarcity: Land'],
    ['faction_type','Faction types',{Type:'Commoners',Agent:'Gravedigger'},'Commoners · Gravedigger'],
    ['faction_trait','Faction traits',{'Trait 1':'Connected','Trait 2':'Selfish'},'Connected · Selfish'],
    ['advantage','Advantages',{Advantages:['Apparatus','Information']},'Apparatus, Information'],
    ['agenda','Agendas',{Agenda:'Explore Uncharted Lands',Obstacle:'A powerful foe'},'Explore Uncharted Lands'],
  ]) {
    const generated=article(category,placeholder,fields);
    assert.equal(generated.title,expected);
    assert.deepEqual(generated.fields,fields);
    assert.equal(article(category,'My own name',fields).title,'My own name');
  }
});
import {readFileSync} from 'node:fs';
import {generateResult, graphFromResult, localizeText, resultText} from '../../app/static/src/js/content_generators.js';

const data={};
for (const name of ['dungeons','forests','realm','factions','npcs','names','faction-events','bestiary','custom-monster','reactions','weather','dungeon-events','wilderness-events','reliquary','spellbooks']) {
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

test('Tools display translation leaves the generated result machine-readable',()=>{
  const terms={Difficulty:'Сложность',Landmark:'Ориентир',Easy:'Простой',Tough:'Трудный',Perilous:'Опасный',Heart:'Сердце',
    Settlement:'Поселение',Monster:'Монстр',Hidden:'Скрытая',Terrain:'Местность',POIs:'Места интереса',Weather:'Погода'};
  const t=key=>terms[key] ?? key;
  for (const type of ['Dungeon','Forest','Realm']) for (let seed=1;seed<=10;seed++) {
    const result=generateResult(data,'Worldbuilding',type,rng(seed));
    const before=structuredClone(result);
    const shown=resultText(result,t);
    assert.deepEqual(result,before);
    assert.equal(resultText(result,key=>key),resultText(result));
    assert(!/Difficulty: |Landmark: |Heart · |\bMonster: /.test(shown),shown);
    graphFromResult(result,rng(seed),data);
  }
  assert.equal(localizeText('Heart · Settlement: Hamlet, walls',t),'Сердце · Поселение: Hamlet, walls');
  assert.equal(localizeText('Bogs. Difficulty: Tough. Landmark: Bones.',t),'Bogs. Сложность: Трудный. Ориентир: Bones.');
  assert.equal(localizeText('Hidden, Deer Crossing, cairn',t),'Скрытая, Deer Crossing, cairn');
  assert.equal(localizeText('Weather',t),'Погода');
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
test('generated names preserve rolled descriptions and survive graph conversion',()=>{
  for(const kind of ['Dungeon','Forest','Realm']){
    const result=generateResult(data,'Worldbuilding',kind,rng(16));
    assert(!result.title.startsWith(kind+':'));
    const graph=graphFromResult(result,rng(1));
    assert.deepEqual(graph.nodes.map(n=>n.body),result.fields.POIs);
    if(kind==='Realm')assert.deepEqual(graph.nodes.map(n=>n.title),result.poiNames);
  }
});

const {generateArticle}=await import('../../app/static/src/js/content_generators.js');
const {settingTypes,parentTypes,draftPreview}=await import('../../app/static/src/js/setting_articles.js');
const flatten=draft=>[draft,...(draft.children||[]).flatMap(flatten)];
test('setting entities form deterministic typed trees, with an explicit opt-out',()=>{
  for(const category of settingTypes) {
    const draft=generateArticle(data,category,'',rng(5));
    assert.deepEqual(draft,generateArticle(data,category,'',rng(5)),category);
    for(const child of flatten(draft)) {
      assert(child.title && child.title.length<=200,category);
      assert(!/undefined|\[object Object\]/.test(child.body),`${category}: ${child.body}`);
      assert.notEqual(child.category,'location');
    }
    if(parentTypes.has(category)) assert.equal(generateArticle(data,category,'',rng(5),{generateChildren:false}).children.length,0);
  }
  const realm=generateArticle(data,'realm','',rng(5));
  assert.deepEqual(realm.children.map(x=>x.category),['people','faction','topography','pois','paths']);
  assert.deepEqual(realm.children[0].children,[]);
  assert(!('Character' in realm.fields));
  assert(!realm.body.startsWith('**Character:**'));
  assert(realm.children[0].body.includes(`**Character:** ${realm.children[0].fields.Culture.Character}`));
  const pois=realm.children.find(x=>x.category==='pois').children;
  assert.equal(pois.filter(x=>x.is_heart).length,1);
  assert.equal(pois[0].category,'settlement');
  assert(draftPreview(realm).includes(realm.children[0].fields.Culture.Character));
});
test('forest and dungeon chance boundaries and terrain difficulty use the selected options',()=>{
  for(const forestChance of [0,100]) {
    const draft=generateArticle(data,'terrain','',rng(1),{terrainDifficulty:'Tough',forestTerrain:true,forestChance,dungeonChance:100});
    assert.equal(draft.fields.Difficulty,'Tough');
    const forest=draft.children.find(x=>x.category==='forest');
    assert.equal(!!forest,forestChance===100);
    if(forest) assert(forest.children.some(x=>x.category==='dungeon'));
  }
  assert(!generateArticle(data,'forest','',rng(1),{dungeonChance:0}).children.some(x=>x.category==='dungeon'));
  const advantages=generateArticle(data,'advantage','',()=>0.99).fields.Advantages;
  assert.equal(advantages.length,4);
  assert.equal(new Set(advantages).size,4);
});
test('map hierarchy preserves the rolled realm and disabled children produce an empty graph',()=>{
  const result=generateResult(data,'Worldbuilding','Realm',rng(12));
  const graph=graphFromResult(result,rng(12),data);
  assert.deepEqual(graph.children[0].fields.Culture,result.fields.Culture);
  assert.deepEqual(graph.children[0].fields.Resources,result.fields.Resources);
  assert.equal(graph.children[0].children.length,0);
  assert.equal(graph.children[1].title,'Factions');
  assert.deepEqual(graph.children[1].children[0].fields,result.fields.Factions);
  assert.equal(graph.children[1].children[0].children.length,0);
  assert.equal(graph.children[2].children.filter(x=>x.category==='terrain').length,result.fields.Terrain.length);
  for(const terrain of graph.children[2].children.filter(x=>x.category==='terrain')) {
    assert(terrain.fields.Landmark);
    assert.deepEqual(terrain.fields.Weather,result.fields.Weather);
  }
  assert(graph.nodes.every(x=>['settlement','waypoint','curiosity','lair','dungeon'].includes(x.category)));
  assert(graph.edges.every(x=>x.body.includes('Feature:') && x.body.includes('Condition:')));
  const empty=graphFromResult(result,rng(1),data,{generateChildren:false});
  assert.deepEqual([empty.nodes,empty.edges,empty.children],[[],[],[]]);
});

test('realm terrain follows the d6 count and difficulty weights with a landmark for every seed',()=>{
  for(const [random,count] of [[()=>0,1],[()=>0.999,6]]) {
    const realm=generateArticle(data,'realm','',random);
    const terrain=realm.children.find(x=>x.category==='topography').children;
    assert.equal(terrain.length,count);
    for(const region of terrain) {
      assert.equal(region.children.filter(x=>x.category==='landmark').length,0);
      assert(region.fields.Landmark);
      assert(region.body.includes(region.fields.Landmark));
    }
    const tools=generateResult(data,'Worldbuilding','Realm',random);
    assert.equal(tools.fields.Terrain.length,count);
  }
  for(let die=1;die<=6;die++) {
    const region=generateArticle(data,'terrain','',()=>(die-.5)/6,{generateChildren:false});
    assert.equal(region.fields.Difficulty,die<=3?'Easy':die<=5?'Tough':'Perilous');
    assert(region.fields.Landmark);
  }
});

test('using a path draft preserves its rolled path type in the form',async()=>{
  const {contentDraft}=await import('../../app/static/src/js/alpine/components/content-draft.js');
  const component=contentDraft();
  component.formElement={elements:{title:{},body:{dispatchEvent(){}},path_type:{value:'standard'}}};
  component.generated=generateArticle(data,'path','',rng(1),{pathType:'hidden'});
  component.useGenerated();
  assert.equal(component.formElement.elements.path_type.value,'hidden');
  assert.equal(component.generated,null);
});

test('category picker restores existing leaves and clears stale drafts when changing groups',async()=>{
  const {contentDraft}=await import('../../app/static/src/js/alpine/components/content-draft.js');
  const component=contentDraft();
  component.categoryGroups=[{value:'People',choices:[{value:'people'},{value:'npc'}]},
    {value:'POIs',choices:[{value:'pois'},{value:'settlement'}]}];
  component.category='npc';
  component.syncTopCategory();
  assert.equal(component.topCategory,'People');
  assert.deepEqual(component.subCategories.map(x=>x.value),['people','npc']);
  component.generated={title:'Old draft'};component.children=[{category:'npc'}];component.variant='Old';
  component.topCategory='POIs';
  component.changeTopCategory();
  assert.equal(component.category,'pois');
  assert.equal(component.generated,null);
  assert.deepEqual(component.children,[]);
  assert.equal(component.variant,'');
  component.category='settlement';component.syncTopCategory();
  assert.equal(component.topCategory,'POIs');
});

test('realm groups named factions under Factions',()=>{
  const realm=generateArticle(data,'realm','',rng(5));
  const factions=realm.children.find(child=>child.category==='faction');
  assert.equal(factions.title,'Factions');
  assert.equal(factions.children[0].category,'faction');
  assert.notEqual(factions.children[0].title,'Factions');
  assert.equal(factions.children[0].children.length,0);
  assert(factions.children[0].fields.Agenda);
  assert.equal(generateArticle(data,'water','',rng(1)).category,'water');
});


test('each generated Realm describes exactly one water source on a terrain',()=>{
  const waters=draft=>flatten(draft).filter(child=>child.fields?.Water);
  for(let seed=1;seed<=40;seed++) {
    const realm=generateArticle(data,'realm','',rng(seed));
    const graph=graphFromResult(generateResult(data,'Worldbuilding','Realm',rng(seed)),rng(seed),data);
    for(const draft of [realm,graph]) {
      assert.equal(waters(draft).length,1);
      const terrains=draft.children.find(child=>child.category==='topography').children.filter(child=>child.category==='terrain');
      assert.equal(terrains.filter(terrain=>waters(terrain).length===1).length,1);
    }
  }
  assert.equal(waters(generateArticle(data,'realm','',rng(1),{generateChildren:false})).length,0);
});

test('compound descriptions retain descendant text and unambiguous draft links without duplicate previews',()=>{
  for(const category of ['realm','topography','pois','paths','dungeon','forest']) {
    const draft=generateArticle(data,category,'',rng(5));
    const descendants=flatten(draft).slice(1);
    assert(descendants.length>0,category);
    assert.equal(new Set(descendants.map(child=>child.draft_key)).size,descendants.length);
    for(const child of descendants) {
      assert(draft.body.includes(`](kw-generated/${child.draft_key})`),`${category}: ${child.title}`);
      assert(draft.body.includes(child.body),`${category}: ${child.title}`);
    }
    assert.equal(draftPreview(draft),draft.body);
  }
});

test('Dungeon and Forest retain the Tools POIs and trails even without child articles',()=>{
  for(const kind of ['Dungeon','Forest']) {
    const options={generateChildren:false};
    const tools=generateResult(data,'Worldbuilding',kind,rng(17),options);
    const draft=generateArticle(data,kind.toLowerCase(),'',rng(17),options);
    assert.equal(draft.children.length,0);
    for(const text of [...tools.fields.POIs,...(tools.fields.trails || [])]) assert(draft.body.includes(text));
  }
});

test('Tools map drafts retain the original description and link their generated article sections',()=>{
  const result=generateResult(data,'Worldbuilding','Realm',rng(5));
  const graph=graphFromResult(result,rng(5),data);
  assert(graph.body.startsWith(resultText(result)));
  for(const child of graph.children) {
    assert(graph.body.includes(`](kw-generated/${child.draft_key})`));
    for(const descendant of flatten(child).slice(1)) assert(child.body.includes(descendant.body));
  }
});

test('Realm detail rolls stay in parent descriptions without child articles',()=>{
  const removed=new Set(['culture','resources','npc','faction_type','faction_trait','advantage','agenda','landmark','weather','water']);
  for(let seed=1;seed<=20;seed++) {
    for(const draft of [generateArticle(data,'realm','',rng(seed)),
      graphFromResult(generateResult(data,'Worldbuilding','Realm',rng(seed)),rng(seed),data)]) {
      assert(!flatten(draft).some(child=>removed.has(child.category)));
      const people=draft.children.find(child=>child.category==='people');
      assert.deepEqual(Object.keys(people.fields),['Culture','Resources']);
      for(const section of ['Culture','Resources']) {
        assert(people.fields[section]);
        assert(people.body.includes(`### ${section}`));
      }
      const faction=draft.children.find(child=>child.category==='faction').children[0];
      for(const field of ['Type','Agent','Trait 1','Trait 2','Advantages','Agenda','Obstacle']) {
        const key=field in faction.fields?field:field.replace(' ','');
        assert(faction.fields[key],field);
        assert(faction.body.includes(`**${key}:**`));
      }
      const terrains=draft.children.find(child=>child.category==='topography').children;
      for(const terrain of terrains) {
        assert(terrain.body.includes('**Landmark:**'));
        assert(terrain.body.includes('### Weather'));
        if(terrain.fields.Water) assert(terrain.body.includes('### Water'));
      }
    }
  }
  for(const category of ['people','faction','terrain']) {
    const draft=generateArticle(data,category,'',rng(1),{generateChildren:false});
    assert(draft.body.length>0);
    assert.equal(draft.children.length,0);
    if(category==='people') assert(!draft.fields.NPC && draft.fields.Resources && draft.fields.Culture);
    if(category==='faction') assert(draft.fields.Agenda && draft.fields.Advantages);
    if(category==='terrain') assert(draft.fields.Weather && draft.fields.Landmark);
  }
  const realm=generateArticle(data,'realm','',rng(1),{generateChildren:false});
  assert.deepEqual(realm.fields,{});
  assert.equal(realm.body,'');
});

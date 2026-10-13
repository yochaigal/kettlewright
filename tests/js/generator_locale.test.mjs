import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {localizeDraft, localizeGraph, localizeBody} from '../../app/static/src/js/generator-locale.js';
import {generateSettingArticle} from '../../app/static/src/js/setting_articles.js';
import {interfaceText} from '../../app/static/src/js/locale.js';
import {resultText} from '../../app/static/src/js/content_generators.js';

const terms={Realm:'Регион',Terrain:'Ландшафт',Water:'Вода',Path:'Путь',Articles:'Статьи',
  Heart:'Сердце',Settlement:'Поселение',Type:'Тип',River:'Река',Hidden:'Скрытая',
  standard:'Обычная', '1 Armor':'Броня 1',gp:'зм','equipment:Shield':'Щит'};
const t=key=>terms[key] ?? key;

test('fresh graph localization keeps internal keys and exact child link targets',()=>{
  const graph={kind:'realm',title:'Realm',body:'## Articles\n\n## [Heart · Settlement: Дом](kw-generated/root/0)',
    children:[{draft_key:'root/0',category:'settlement',title:'Дом',body:'**Type:** River'}],
    nodes:[{id:'poi-1',poi_kind:'dungeon',category:'dungeon',title:'Terrain: Леса',body:'**Water:** River'}],
    edges:[{source:'poi-1',target:'poi-2',path_type:'hidden',body:'Hidden, мост, лес'}]};
  localizeGraph(graph,t);
  assert.equal(graph.title,'Регион');
  assert.match(graph.body,/\[Сердце · Поселение: Дом\]\(kw-generated\/root\/0\)/);
  assert.equal(graph.children[0].body,'**Тип:** Река');
  assert.equal(graph.children[0].draft_key,'root/0');
  assert.equal(graph.nodes[0].poi_kind,'dungeon');
  assert.equal(graph.edges[0].path_type,'hidden');
  assert.equal(graph.edges[0].body,'Скрытая, мост, лес');
  assert.equal(localizeBody('**Type:** standard',t),'**Тип:** Обычная');
  assert.equal(localizeDraft({title:'Path: standard',body:''},t).title,'Путь: Обычная');
});

test('localized forest terrain still generates a nested forest',()=>{
  const data={};
  for(const file of ['realm','forests','dungeons'])
    Object.assign(data,JSON.parse(readFileSync(new URL(`../../app/static/json/generators/${file}.json`,import.meta.url))));
  data.Realm.Topography.TerrainKeys={'Леса':'Forests'};
  data.Realm.Topography.Terrain.Tough.Terrain=['Леса'];
  const draft=generateSettingArticle(data,'terrain',()=>0,{terrainDifficulty:'Tough',forestChance:100,dungeonChance:0});
  assert.equal(draft.children.length,1);
  assert.equal(draft.children[0].category,'forest');
});

test('Babel messages substitute runtime limits and localize equipment bonuses',()=>{
  const original=globalThis.document;
  globalThis.document={getElementById:id=>({textContent:JSON.stringify(id==='interface-labels'
    ? {'Uses must be less than %(maximum)s':'Использований должно быть меньше %(maximum)s'} : terms)})};
  try {
    assert.equal(interfaceText('Uses must be less than %(maximum)s',{maximum:100}),'Использований должно быть меньше 100');
    assert.equal(resultText({category:'item',title:'Shield',fields:{tags:['1 Armor','bonus defense'],cost:10}}),
      'Щит (+Броня 1). 10 зм.');
  } finally {globalThis.document=original;}
});

import {generateWorldbuilding} from './worldbuilding.js';
import {settingName} from './naming.js';

export const settingTypes = new Set(['realm','people','culture','resources','faction','faction_type',
  'faction_trait','advantage','agenda','topography','terrain','landmark','water','weather','pois','settlement',
  'waypoint','curiosity','lair','dungeon','forest','paths','path','room','monster','ruins','shelter','hazard','trap','special']);
export const parentTypes = new Set(['realm','people','faction','topography','terrain','pois','dungeon','forest','paths']);
const labels = {faction_type:'Faction types',faction_trait:'Faction traits',advantage:'Advantages',agenda:'Agendas',pois:'POIs'};
export function fieldText(fields, level=3) {
  return Object.entries(fields).map(([key,value])=>value && typeof value==='object' && !Array.isArray(value)
    ? `${'#'.repeat(Math.min(level,6))} ${key}\n\n${fieldText(value,level+1)}`
    : `**${key}:** ${Array.isArray(value)?value.join(', '):value}`).join('\n\n');
}
export function article(category, title, fields={}, children=[]) {
  const generic={culture:'Culture',resources:'Resources',faction_type:'Faction types',faction_trait:'Faction traits',advantage:'Advantages',agenda:'Agendas'};
  if(title===generic[category]) {
    const values=category==='resources'
      ? [fields.Abundance,fields.Scarcity && `Scarce: ${fields.Scarcity}`]
      : ({culture:[fields.Character,fields.Ambition],faction_type:[fields.Type,fields.Agent],
          faction_trait:[fields['Trait 1'],fields['Trait 2']],advantage:[fields.Advantages],agenda:[fields.Agenda]})[category];
    title=values?.filter(Boolean).map(value=>Array.isArray(value)?value.join(', '):value).join(' · ') || title;
  }
  return {category,title:title.slice(0,200),fields,body:fieldText(fields),children};
}
export function draftPreview(draft, level=2) {
  return [draft.body,...(draft.children || []).map(child=>`${'#'.repeat(Math.min(level,6))} ${child.is_heart?'Heart · ':''}${child.title}\n\n${draftPreview(child,level+1)}`)].filter(Boolean).join('\n\n');
}

// Setting Seeds tables are shared with Tools. Water choice and forest chance
// are application options: the rules prescribe neither of those probabilities.
export function generateSettingArticle(data, category, random=Math.random, options={}) {
  const draft=rollSettingArticle(data,category,random,options);
  draft.title=settingName(data,category,draft.fields,draft.title,random);
  return draft;
}

function rollSettingArticle(data, category, random=Math.random, options={}) {
  const pick=items=>items[Math.floor(random()*items.length)];
  const roll=sides=>Math.floor(random()*sides)+1;
  const realm=data.Realm, people=realm.Theme.People, factions=realm.Theme.Factions;
  const all=options.generateChildren !== false;
  const count=['realm','pois','paths'].includes(category) ? (options.poiCount ? Math.max(3,Math.min(20,Number(options.poiCount))) : roll(6)+2) : 0;
  const sub=(kind,extra={})=>generateSettingArticle(data,kind,random,{...options,...extra});
  const fieldsFrom=table=>Object.fromEntries(Object.entries(table).map(([key,values])=>[key,pick(values)]));
  const simple=(kind,table)=>article(kind,labels[kind] || kind[0].toUpperCase()+kind.slice(1),fieldsFrom(table));
  if(category==='culture') return simple(category,people.Culture);
  if(category==='resources') return simple(category,people.Resources);
  if(category==='people') {
    const children=all?[sub('culture'),sub('resources')]:[];
    if(all) {
      const npc=generateWorldbuilding({NPC:data.NPCGenerator},'NPC',random);
      children.push(article('npc',npc.title,npc.fields));
    }
    return article(category,'People',{},children);
  }
  if(category==='faction_type') return simple(category,factions.FactionTypes);
  if(category==='faction_trait') return simple(category,factions.FactionTraits);
  if(category==='agenda') return simple(category,factions.FactionAgendas);
  if(category==='advantage') {
    const available=[...factions.FactionAdvantages.Advantage], values=[];
    const total=pick(factions.FactionAdvantages.NumberOfAdvantages);
    for(let i=0;i<total;i++) values.push(available.splice(Math.floor(random()*available.length),1)[0]);
    return article(category,'Advantages',{Advantages:values});
  }
  if(category==='faction') {
    const type=sub('faction_type');
    return article(category,`Faction: ${type.fields.Type}`,type.fields,
      all?[type,sub('faction_trait'),sub('advantage'),sub('agenda')]:[]);
  }
  if(category==='weather') return simple(category,realm.Weather.SeasonalWeather);
  if(category==='water') {
    const type=pick(['River','Lake','Sea']);
    return article(category,type,{Type:type,
      Course:'Connect higher ground to lower ground; the water may end in a lake, sea, or beyond the map.'});
  }
  if(category==='landmark') {
    const difficulty=options.terrainDifficulty || pick(realm.Topography.Difficulty);
    const landmark=pick(realm.Topography.Terrain[difficulty].Landmark);
    return article(category,`Landmark: ${landmark}`,{Landmark:landmark});
  }
  if(category==='terrain') {
    const difficulty=options.terrainDifficulty || pick(realm.Topography.Difficulty);
    const fields=options.terrainFields || fieldsFrom(realm.Topography.Terrain[difficulty]);
    if(options.forestTerrain) fields.Terrain='Forests';
    const landmark=article('landmark',fields.Landmark,{Landmark:fields.Landmark});
    landmark.title=settingName(data,'landmark',landmark.fields,landmark.title,random);
    const children=all?[landmark]:[];
    if(all && random()<0.25) children.push(sub('water'));
    if(all) children.push(sub('weather'));
    if(all && /forest|woodland|jungle|taiga|mangrove|thicket/i.test(fields.Terrain)
      && random()*100<Number(options.forestChance ?? 50)) children.push(sub('forest'));
    return article(category,`Terrain: ${fields.Terrain}`,{Difficulty:difficulty,...fields},children);
  }
  if(category==='topography') return article(category,'Topography',{},all?Array.from({length:roll(6)},()=>sub('terrain')):[]);
  if(category==='path') {
    const path_type=options.pathType || pick(['standard','standard','standard','standard','hidden','conditional']);
    return {...article(category,`Path: ${path_type}`,{Type:path_type,...fieldsFrom(realm.Paths.PathFeatures)}),path_type};
  }
  if(category==='paths') return article(category,'Paths',{},all?Array.from({length:count-1},()=>sub('path')):[]);
  if(category==='pois') {
    const children=[];
    if(all) for(let i=0;i<count;i++) {
      // d6: 1 settlement/waypoint, 2–3 curiosity, 4 lair, 5–6 dungeon.
      const kind=i===0?'settlement':pick(realm.PointsOfInterest.POI).toLowerCase();
      children.push({...sub(kind),is_heart:i===0});
    }
    return article(category,'POIs',{},children);
  }
  if(category==='realm') {
    const children=all?[sub('people'),article('faction','Factions',{},[sub('faction')]),sub('topography'),sub('pois',{poiCount:count}),sub('paths',{poiCount:count})]:[];
    const character=children[0]?.children[0]?.fields.Character || pick(people.Culture.Character);
    return article(category,`Realm: ${character}`,{Character:character},children);
  }
  const poiTables={settlement:'Settlements',waypoint:'Waypoints',curiosity:'Curiosities',lair:'Lairs'};
  if(poiTables[category]) {
    const fields=fieldsFrom(realm.PointsOfInterest[poiTables[category]]);
    return {...article(category,`${category[0].toUpperCase()+category.slice(1)}: ${fields[category[0].toUpperCase()+category.slice(1)]}, ${fields.Feature}`,fields),is_heart:category==='settlement' && !!options.isHeart};
  }
  if(category==='dungeon' || category==='forest') {
    const result=generateWorldbuilding({Dungeon:data.Dungeon,Forest:data.Forest},category==='dungeon'?'Dungeon':'Forest',random,options);
    const {POIs,trails,...fields}=result.fields;
    const own=fields;
    const site=category==='dungeon'?fieldsFrom(realm.PointsOfInterest.Dungeons):null;
    if(site) own.Site=site;
    const children=all?POIs.map(body=>{
      const kind=body.split(':')[0].toLowerCase();
      return article(settingTypes.has(kind)||kind==='lore'?kind:'room',body.replace(/\s+/g,' ').trim(),{Description:body});
    }):[];
    if(all && category==='forest' && random()*100<Number(options.dungeonChance ?? 25)) children.push(sub('dungeon'));
    if(all && trails) children.push(article('paths','Paths',{},trails.map(body=>({...article('path',body,{Description:body}),
      path_type:/^(hidden|conditional)/i.exec(body)?.[1].toLowerCase() || 'standard'}))));
    return article(category,site?`Dungeon: ${site.Type}, ${site.Feature}`:result.title,own,children);
  }
  const forestTypes={monster:'Monster',ruins:'Ruins',shelter:'Shelter',hazard:'Hazard'};
  const dungeonTypes={room:'Lore',trap:'Trap',special:'Special'};
  if(forestTypes[category]) return simple(category,data.Forest.ForestPOIs[forestTypes[category]]);
  if(dungeonTypes[category]) return simple(category,data.Dungeon.POIs[dungeonTypes[category]]);
  throw new Error('Unknown setting article type');
}

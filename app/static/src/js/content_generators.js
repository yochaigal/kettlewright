import {generateSettingArticle, settingTypes, article} from './setting_articles.js';
import {generateWorldbuilding} from './worldbuilding.js';
import {settingName} from './naming.js';

// All consumers retain this result object; saving never rolls the tables again.
export function generateResult(data, category, subcategory, random = Math.random, options = {}) {
  const pick = values => values[Math.floor(random() * values.length)];
  if (category === 'Worldbuilding') {
    return generateWorldbuilding({Names:data.Names,Dungeon:data.Dungeon, Forest:data.Forest, Realm:data.Realm,
      Faction:data.FactionGenerator, 'Faction Actions':data.FactionActions, NPC:data.NPCGenerator}, subcategory, random, options);
  }
  if (category === 'Items') {
    const item = pick(data[subcategory]);
    return {title:item.name, category:subcategory === 'Relics' ? 'relic' : 'spellbook', fields:{...item}};
  }
  if (category === 'Weather') {
    const type = pick(data.Weather.Types[subcategory]);
    return {title:'Weather', category:'weather', fields:{Season:subcategory, Type:type, ...data.Weather.Difficulty[type]}};
  }
  if (category === 'Events') {
    return {title:subcategory, category:'note', fields:pick(data[subcategory])};
  }
  if (subcategory === 'Reaction Roll') {
    const total = Math.floor(random()*6) + Math.floor(random()*6);
    return {title:'Reaction Roll', category:'note', fields:{Reaction:data[subcategory][total]}};
  }
  if (subcategory === 'Random Monster') {
    const monster = pick(data[subcategory]);
    return {title:monster.Name, category:'bestiary', fields:monster};
  }
  const monster = data['Custom Monster'];
  return {title:'Custom Monster', category:'bestiary', fields:{
    Physique:pick(monster.MonsterAppearance.Physique), Feature:pick(monster.MonsterAppearance.Feature),
    Quirks:pick(monster.MonsterTraits.Quirks), Weakness:pick(monster.MonsterTraits.Weakness),
    Attack:pick(monster.MonsterAttacks.Type), 'Critical Damage':pick(monster.MonsterAttacks.CriticalDamage),
    Ability:pick(monster.MonsterAbilities.Ability), Target:pick(monster.MonsterAbilities.Target)}};
}

export function resultText(result) {
  if (result.category === 'spellbook') {
    return [result.fields.description, result.fields.personality ? `_${result.fields.personality}_` : ''].filter(Boolean).join(' ');
  }
  if (result.category === 'item') {
    const fields=result.fields, tags=fields.tags || [];
    const traits=tags.filter(tag=>!['uses','bonus defense'].includes(tag)).map(tag=>
      tags.includes('bonus defense') && /Armor/i.test(tag) ? `+${tag}` : tag);
    if (fields.uses) traits.push(`${fields.uses} uses`);
    return `${result.title}${traits.length ? ` (${traits.join(', ')})` : ''}. ${fields.cost}gp.`;
  }
  function render(value, level=3) {
    if(Array.isArray(value)) return value.map(item=>`- ${typeof item==='object' ? render(item,level) : item}`).join('\n');
    if(value && typeof value==='object') return Object.entries(value).filter(([,item])=>!Array.isArray(item) || item.length).map(([key,item])=>
      item && typeof item==='object' ? `${'#'.repeat(Math.min(level,6))} ${key.charAt(0).toUpperCase()+key.slice(1)}\n\n${render(item,level+1)}`
        : `**${key.charAt(0).toUpperCase()+key.slice(1)}:** ${item ?? ''}`).join('\n\n');
    return String(value ?? '');
  }
  return render(result.fields);
}

export function graphFromResult(result, random = Math.random, tables = null, options = {}) {
  if (!result.mapKind || !Array.isArray(result.fields.POIs)) throw new Error('This result has no locations.');
  const pois = options.generateChildren === false ? [] : result.fields.POIs;
  const columns = Math.ceil(Math.sqrt(pois.length));
  const nodes = pois.map((body, i) => ({id:`new-node-${i}`, number:i+1,
    title:result.poiNames?.[i] || body.replace(/\s+/g,' ').trim().slice(0,200), body,
    poi_kind:result.poiKinds?.[i] || null,
    category:result.poiKinds?.[i] || (body.startsWith('Heart')?'settlement':body.split(':')[0].trim().toLowerCase()),
    is_heart:result.mapKind==='realm' && i===0,
    x:100+(i%columns)*210+Math.round(random()*60),
    y:100+Math.floor(i/columns)*180+Math.round(random()*60), nested_map_id:null}));
  const edges = [], connected = new Set(nodes.length ? [0] : []), pairs = new Set();
  const distance = (a,b) => (nodes[a].x-nodes[b].x)**2+(nodes[a].y-nodes[b].y)**2;
  function add(a,b) {
    let trail = result.fields.trails?.[edges.length % result.fields.trails.length] || '';
    if(!trail && tables?.Realm && result.mapKind==='realm') {
      const fields=tables.Realm.Paths.PathFeatures;
      trail=Object.entries(fields).map(([key,values])=>`${key}: ${values[Math.floor(random()*values.length)]}`).join('. ');
    }
    // Fallback weights are generator choices, not a rules-table probability.
    const type = result.fields.trails?.length ? trail.split(',')[0].trim().toLowerCase()
      : ['standard','standard','standard','standard','hidden','conditional'][Math.floor(random()*6)];
    edges.push({id:`new-edge-${edges.length}`, source:nodes[a].id, target:nodes[b].id,
      title:`${a+1} – ${b+1}`, body:trail,
      path_type:['hidden','conditional'].includes(type) ? type : 'standard'});
    pairs.add([a,b].sort((x,y)=>x-y).join(':'));
  }
  // A nearest-neighbour spanning tree keeps every location reachable.
  while (connected.size < nodes.length) {
    let best = null;
    for (const a of connected) for (let b=0;b<nodes.length;b++) {
      if (!connected.has(b) && (!best || distance(a,b)<best.distance)) best={a,b,distance:distance(a,b)};
    }
    add(best.a,best.b); connected.add(best.b);
  }
  // Short extra connections create loops while preserving branches and dead ends.
  const candidates = [];
  for (let a=0;a<nodes.length;a++) for (let b=a+1;b<nodes.length;b++) {
    if (!pairs.has(`${a}:${b}`)) candidates.push({a,b,distance:distance(a,b)});
  }
  candidates.sort((a,b)=>a.distance-b.distance);
  candidates.slice(0, Math.max(1, Math.floor(nodes.length/6))).forEach(({a,b})=>add(a,b));
  if (options.generateChildren !== false && tables && result.mapKind === 'realm') for (const node of nodes) {
    const kind = node.poi_kind || suggestedMapKind(node);
    if (['dungeon','forest'].includes(kind)) node.nested_draft = nestedMapDraft(node, kind, tables, random);
  }
  const children=[];
  if(tables?.NPCGenerator && result.mapKind==='realm' && options.generateChildren !== false) {
    const rolled=result.fields;
    children.push({category:'people',title:'People',body:'',children:[
      article('culture','Culture',rolled.Culture),
      article('resources','Resources',rolled.Resources),
      generateArticle(tables,'npc','',random)]});
    const faction=rolled.Factions;
    children.push(article('faction',settingName(tables,'faction',faction,`Faction: ${faction.Type}`,random),{},[
      article('faction_type','Faction types',{Type:faction.Type,Agent:faction.Agent}),
      article('faction_trait','Faction traits',{'Trait 1':faction['Trait 1'],'Trait 2':faction['Trait 2']}),
      article('advantage','Advantages',{Advantages:faction.Advantages}),
      article('agenda','Agendas',{Agenda:faction.Agenda,Obstacle:faction.Obstacle})]));
    const terrains=rolled.Terrain.map(description=>{
      const match=/^(.*?)\. Difficulty: (.*?)\. Landmark: (.*?)\./.exec(description);
      return generateSettingArticle(tables,'terrain',random,{...options,
        terrainDifficulty:match[2],terrainFields:{Terrain:match[1],Landmark:match[3]}});
    });
    // The already rolled climate is shared by this region, not rolled again.
    for(const terrain of terrains) terrain.children=terrain.children.filter(child=>child.category!=='weather');
    children.push(article('topography','Topography',{},[...terrains,article('weather','Weather',rolled.Weather)]),
      article('pois','POIs'),article('paths','Paths'));
  }
  if(tables && result.mapKind==='forest' && options.generateChildren !== false
    && random()*100<Number(options.dungeonChance ?? 25)) children.push(generateSettingArticle(tables,'dungeon',random,options));
  return {title:result.title, body:resultText(result), kind:result.mapKind, nodes, edges, children};
}

// Older Tools results have no POI metadata; generated names include their type.
export function suggestedMapKind(node) {
  return node.poi_kind || (['forest','dungeon'].includes(node.category)?node.category:null) || (/\bforest\b/i.test(node.title) ? 'forest'
    : /\bdungeon\b/i.test(node.title) ? 'dungeon' : null);
}

export function nestedMapDraft(node, kind, tables, random = Math.random) {
  if (!['dungeon','forest'].includes(kind)) throw new Error('Unsupported nested map type.');
  const result = generateResult(tables, 'Worldbuilding', kind === 'dungeon' ? 'Dungeon' : 'Forest', random);
  return {...graphFromResult(result, random), title:node.title};
}

// Article categories reuse the same rules tables as Tools. No campaign is needed.
export function generateArticle(data, category, variant='', random=Math.random, options={}) {
  if(settingTypes.has(category)) return generateSettingArticle(data,category,random,options);
  const pick=items=>items[Math.floor(random()*items.length)];
  let result;
  if(category==='npc') result=generateResult(data,'Worldbuilding','NPC',random);
  else if(category==='bestiary') result=generateResult(data,'Monsters',variant || 'Random Monster',random);
  else if(category==='relic' || category==='spellbook') result=generateResult(data,'Items',category==='relic'?'Relics':'Spellbooks',random);
  else if(category==='item') {
    const group=variant || 'Gear', [name,fields]=pick(Object.entries(data.Equipment[group]));
    result={title:name,category:'item',fields:{Type:group,...fields}};
  } else if(category==='lore') {
    const lore=data.Dungeon.POIs.Lore;
    result={title:'Lore',fields:{'Found in':pick(lore.RoomType),Clue:pick(lore.Clue)}};
  } else if(category==='location') {
    const realm=generateResult(data,'Worldbuilding','Realm',random);
    const poi=pick(realm.fields.POIs).replace(/\s+/g,' ').trim();
    result={title:poi.slice(0,200),fields:{Description:poi}};
  } else if(category==='overview') {
    result=generateResult(data,'Worldbuilding','Realm',random);
    result={title:result.title,fields:result.fields};
  } else if(category==='note') result=generateResult(data,'Events',variant || 'Wilderness Events',random);
  else if(category==='map') result=generateResult(data,'Worldbuilding',variant || 'Realm',random);
  else if(category==='custom') return null;
  else throw new Error('Unknown article category');
  return {...result,category,body:resultText(result)};
}

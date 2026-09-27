import {generateWorldbuilding} from './worldbuilding.js';

// All consumers retain this result object; saving never rolls the tables again.
export function generateResult(data, category, subcategory, random = Math.random) {
  const pick = values => values[Math.floor(random() * values.length)];
  if (category === 'Worldbuilding') {
    return generateWorldbuilding({Dungeon:data.Dungeon, Forest:data.Forest, Realm:data.Realm,
      Faction:data.FactionGenerator, 'Faction Actions':data.FactionActions, NPC:data.NPCGenerator}, subcategory, random);
  }
  if (category === 'Items') {
    const item = pick(data[subcategory]);
    return {title:item.name, category:subcategory === 'Relics' ? 'relic' : 'note', fields:{...item}};
  }
  if (category === 'Weather') {
    const type = pick(data.Weather.Types[subcategory]);
    return {title:'Weather', category:'note', fields:{Season:subcategory, Type:type, ...data.Weather.Difficulty[type]}};
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
    return {title:monster.Name, category:'npc', fields:monster};
  }
  const monster = data['Custom Monster'];
  return {title:'Custom Monster', category:'npc', fields:{
    Physique:pick(monster.MonsterAppearance.Physique), Feature:pick(monster.MonsterAppearance.Feature),
    Quirks:pick(monster.MonsterTraits.Quirks), Weakness:pick(monster.MonsterTraits.Weakness),
    Attack:pick(monster.MonsterAttacks.Type), 'Critical Damage':pick(monster.MonsterAttacks.CriticalDamage),
    Ability:pick(monster.MonsterAbilities.Ability), Target:pick(monster.MonsterAbilities.Target)}};
}

export function resultText(result) {
  function lines(value, indent = '') {
    if (Array.isArray(value)) return value.map((item, i) => `${indent}${i+1}. ${typeof item === 'object' ? lines(item, indent+'  ') : item}`).join('\n');
    if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) =>
      item && typeof item === 'object' ? `${indent}${key}:\n${lines(item, indent+'  ')}` : `${indent}${key}: ${item ?? ''}`).join('\n');
    return `${indent}${value ?? ''}`;
  }
  return lines(result.fields);
}

export function graphFromResult(result, random = Math.random) {
  if (!result.mapKind || !Array.isArray(result.fields.POIs)) throw new Error('This result has no locations.');
  const pois = result.fields.POIs;
  const columns = Math.ceil(Math.sqrt(pois.length));
  const nodes = pois.map((body, i) => ({id:`new-node-${i}`, number:i+1,
    title:body.split(':')[0], body,
    x:100+(i%columns)*210+Math.round(random()*60),
    y:100+Math.floor(i/columns)*180+Math.round(random()*60), nested_map_id:null}));
  const edges = [], connected = new Set(nodes.length ? [0] : []), pairs = new Set();
  const distance = (a,b) => (nodes[a].x-nodes[b].x)**2+(nodes[a].y-nodes[b].y)**2;
  function add(a,b) {
    const trail = result.fields.trails?.[edges.length % result.fields.trails.length] || '';
    const type = trail.split(',')[0].trim().toLowerCase();
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
  return {title:result.title, body:resultText(result), kind:result.mapKind, nodes, edges};
}

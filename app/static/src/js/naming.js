// Cairn 2e, Naming Procedures. Tables and source attribution: generators/names.json.
export function settingName(data, category, fields={}, fallback='', random=Math.random) {
  const names=data.Names;
  if(!names)return fallback;
  const pick=values=>values[Math.floor(random()*values.length)];
  if(category==='forest')return `${pick(names.ForestNames.Adjectives)} ${pick(names.ForestNames.Nouns)}`;
  let group='POI', base;
  if(category==='realm') {group='Realm';base=pick(names.RulerTypes);}
  else if(category==='faction') {group='Faction';base=pick(names.GroupTypes);}
  else if(category==='terrain') {
    base=fields.Terrain || fallback.replace(/^Terrain:\s*/,'');
    const singular=value=>value.toLowerCase().replace(/s$/,'');
    const key=Object.keys(names.TerrainSynonyms).find(key=>singular(key)===singular(base));
    if(key)base=pick(names.TerrainSynonyms[key]);
    base=base.replace(/\b\w/g,c=>c.toUpperCase());
  } else if(category==='water')base=fields.Type || fallback;
  else if(category==='landmark')base=fields.Landmark || fallback.replace(/^Landmark:\s*/,'');
  else if(category==='dungeon')base=fields.Site?.Type || fields.Purpose?.['Original Use'] || 'Dungeon';
  else if(['settlement','waypoint','curiosity','lair'].includes(category)) {
    const label=category[0].toUpperCase()+category.slice(1);
    base=fields[label] || fallback.replace(/^(?:Heart · )?[^:]+:\s*/,'').split(',')[0] || label;
  } else if(category==='path')base='Path';
  else return fallback;
  const formula=pick(names.NameFormulas[group]);
  const values={POI:base,Group:base,Rulers:base};
  return formula.replace(/\((The|the)\)/g,'$1').replace(/\[(\w+)\]/g,(_,key)=>{
    if(!(key in values))values[key]=pick(names[key==='Noun'?'Nouns':'Adjectives']);
    return values[key];
  }).slice(0,200);
}

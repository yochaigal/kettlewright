// Partition the map around die-drop/landmark seeds. Each clipped cell contains
// its own seed and shares its borders with neighbouring terrain, without gaps.
export function terrainRegions(graph) {
  if (graph.kind !== 'realm') return new Map();
  const seeds=graph.nodes.filter(node=>node.category==='terrain').map(node=>{
    const landmark=graph.nodes.find(point=>point.category==='landmark' && String(point.terrain_id)===String(node.id));
    return {id:String(node.id),x:landmark?.x ?? node.x,y:landmark?.y ?? node.y};
  });
  const bounds=graph.nodes.concat(seeds);
  if (!seeds.length) return new Map();
  const left=Math.min(...bounds.map(p=>p.x))-320, right=Math.max(...bounds.map(p=>p.x))+320;
  const top=Math.min(...bounds.map(p=>p.y))-350, bottom=Math.max(...bounds.map(p=>p.y))+350;
  // Separate coincident legacy seeds deterministically, without changing data.
  seeds.forEach((seed,i)=>{if(seeds.slice(0,i).some(p=>p.x===seed.x && p.y===seed.y))seed.x+=i*.01;});
  return new Map(seeds.map(seed=>{
    let polygon=[[left,top],[right,top],[right,bottom],[left,bottom]];
    for(const other of seeds) {
      if(other===seed)continue;
      const dx=other.x-seed.x,dy=other.y-seed.y;
      const midpoint=[(other.x+seed.x)/2,(other.y+seed.y)/2];
      const distance=p=>(p[0]-midpoint[0])*dx+(p[1]-midpoint[1])*dy;
      const clipped=[];
      polygon.forEach((a,i)=>{
        const b=polygon[(i+1)%polygon.length],da=distance(a),db=distance(b);
        if(da<=0)clipped.push(a);
        if((da<=0)!==(db<=0)) {
          const t=da/(da-db);
          clipped.push([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]);
        }
      });
      polygon=clipped;
    }
    return [seed.id,{...seed,polygon}];
  }));
}

export function insideRegion(polygon,x,y) {
  let inside=false;
  for(let i=0,j=polygon.length-1;i<polygon.length;j=i++) {
    const a=polygon[i],b=polygon[j];
    if((a[1]>y)!==(b[1]>y) && x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}

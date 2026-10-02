import {terrainRegions, insideRegion} from './terrain.js';
export const emptyDrawing = () => ({elements: [], files: {}});
export const isManaged = element => element.id.startsWith('kw-') || Boolean(element.customData?.kwType);
export const editableGeography = node => ['terrain','water'].includes(node?.category);
export function shapeGeometry(element) {
  return Object.fromEntries(['type','x','y','width','height','angle','points','strokeWidth']
    .filter(key=>element[key]!==undefined).map(key=>[key,element[key]]));
}
function sameGeometry(a,b) {
  if(typeof a==='number' && typeof b==='number')return Math.abs(a-b)<0.001;
  if(Array.isArray(a) && Array.isArray(b))return a.length===b.length && a.every((v,i)=>sameGeometry(v,b[i]));
  if(a && b && typeof a==='object' && typeof b==='object')return Object.keys(a).length===Object.keys(b).length && Object.keys(a).every(k=>sameGeometry(a[k],b[k]));
  return a===b;
}

// Only free drawing belongs in the snapshot. Cards are always projected by Flask.
export function drawingFromScene(elements, files) {
  const drawing = elements.filter(element => !element.isDeleted && !isManaged(element));
  const fileIds = new Set(drawing.filter(element => element.type === 'image').map(element => element.fileId));
  return {elements: drawing, files: Object.fromEntries(Object.entries(files).filter(([id]) => fileIds.has(id)))};
}

// Shape, colour and text all identify a type; colour is never the only cue.
export function nodeAppearance(node, kind) {
  const types = {
    terrain: {type:'rectangle', width:640, height:700, stroke:'#5c713b', fill:'#e9efcf', label:'Terrain', background:true},
    landmark: {type:'line', width:54, height:48, stroke:'#765329', fill:'#ffe8a3', label:'Landmark'},
    water: {type:'ellipse', width:170, height:80, stroke:'#1971c2', fill:'#d0ebff', label:'Water'},
    waypoint: {type:'diamond', width:64, height:64, stroke:'#9c5b00', fill:'#ffec99', label:'Waypoint'},
    settlement: {type:'rectangle', width:64, height:54, stroke:'#9c4221', fill:'#ffe8cc', label:'Settlement'},
    forest: {type:'diamond', width:72, height:72, stroke:'#2b6d3d', fill:'#d3f9d8', label:'Forest'},
    dungeon: {type:'rectangle', width:60, height:60, stroke:'#6741a5', fill:'#e5dbff', label:'Dungeon'},
    lair: {type:'diamond', width:60, height:60, stroke:'#c92a2a', fill:'#ffe3e3', label:'Lair'},
    curiosity: {type:'ellipse', width:60, height:60, stroke:'#087f8c', fill:'#c5f6fa', label:'Curiosity'},
  };
  const style = types[node.category];
  if (!style) return {type:'ellipse', width:60, height:60, stroke:'#1b1b1f', fill:'#ffffff', label:''};
  if (node.category==='terrain' && kind!=='realm')return {...style,width:100,height:70,background:false};
  return style;
}

export function graphShapes(graph, selected='', selectedEdge='') {
  const nodes = new Map(graph.nodes.map(node => [String(node.id), node]));
  const regions=terrainRegions(graph);
  const backgrounds=[], foregrounds=[], paths=[];
  for (const node of graph.nodes) {
    const style=nodeAppearance(node,graph.kind), active=String(node.id)===selected;
    const shapes=style.background?backgrounds:foregrounds;
    const region=regions.get(String(node.id));
    const shape={id:`kw-node-${node.id}`,type:style.type,x:node.x-style.width/2,y:node.y-style.height/2,
      width:style.width,height:style.height,strokeColor:active?'#e67700':style.stroke,
      strokeWidth:active && !editableGeography(node)?4:2,backgroundColor:style.fill,fillStyle:style.background?'hachure':'solid',roughness:0,
      opacity:style.background?55:100,
      customData:{kwType:'location',nodeId:String(node.id)}};
    if(region) {
      const polygon=region.polygon, [originX,originY]=polygon[0];
      Object.assign(shape,{type:'line',x:originX,y:originY,locked:false,
        width:Math.max(...polygon.map(p=>p[0]))-Math.min(...polygon.map(p=>p[0])),
        height:Math.max(...polygon.map(p=>p[1]))-Math.min(...polygon.map(p=>p[1])),
        points:[...polygon,polygon[0]].map(p=>[p[0]-originX,p[1]-originY]),
        customData:{kwType:'location',nodeId:String(node.id)}});
    } else if(node.category==='landmark') {
      shape.y=node.y+style.height/2;
      shape.points=[[0,0],[style.width/2,-style.height],[style.width,0],[0,0]];
    }
    if(node.geometry && editableGeography(node)) {
      Object.assign(shape,node.geometry,{locked:false});
      if(shape.type==='freedraw')Object.assign(shape,{pressures:[],simulatePressure:true,backgroundColor:'transparent'});
      if(node.category==='water' && shape.type==='line')shape.backgroundColor='transparent';
    }
    shapes.push(shape);
    const typeLabel=node.is_heart?'Heart · Settlement':style.label;
    const shortTitle=style.label ? node.title.replace(new RegExp('^'+style.label+':\\s*','i'),'').split(',')[0] : node.title;
    const label=`${node.number}. ${typeLabel ? typeLabel+' · ' : ''}${shortTitle}`;
    shapes.push({id:`kw-label-${node.id}`,type:'text',
      x:node.geometry?shape.x:region?region.x-85:node.x-(style.background?style.width/2-16:85),
      y:node.geometry?shape.y-45:region?region.y-100:style.background?node.y-style.height/2+12:node.y+style.height/2+10,
      text:label.replace(/(.{1,20})(?:\s+|$)/g,'$1\n').trim(),fontSize:16,fontFamily:2,locked:true,
      strokeColor:style.stroke,customData:{kwType:'label'}});
  }
  for (const edge of graph.edges) {
    const a = nodes.get(String(edge.source)), b = nodes.get(String(edge.target));
    if (!a || !b) continue;
    paths.push({id: `kw-edge-${edge.id}`, type: 'line', x: a.x, y: a.y,
      points: [[0, 0], [b.x - a.x, b.y - a.y]], locked: true,
      strokeStyle: edge.path_type === 'hidden' ? 'dashed' : edge.path_type === 'conditional' ? 'dotted' : 'solid',
      strokeColor:String(edge.id)===selectedEdge ? '#e67700' : '#1b1b1f',
      strokeWidth:String(edge.id)===selectedEdge ? 5 : 2, roughness: 0, customData: {kwType: 'path', edgeId:String(edge.id)}});
  }
  return [...backgrounds,...paths,...foregrounds];
}

export function movedLocations(elements, graph) {
  const nodes = new Map(graph.nodes.map(node => [String(node.id), node]));
  const originals=new Map(graphShapes(graph).filter(shape=>shape.customData?.kwType==='location').map(shape=>[shape.id,shape]));
  return elements.flatMap(element => {
    const id = element.customData?.nodeId;
    const node = nodes.get(id);
    const original=originals.get(element.id);
    if (!node || !original || element.isDeleted) return [];
    if(editableGeography(node)) {
      const geometry=shapeGeometry(element), initial=shapeGeometry(original);
      // Excalidraw supplies angle=0 even when the generated skeleton omits it.
      geometry.angle ??= 0; initial.angle ??= 0;
      if(sameGeometry(geometry,initial))return [];
      return [{id,x:node.x+element.x-original.x,y:node.y+element.y-original.y,geometry}];
    }
    const x = Math.round(node.x+element.x-original.x), y = Math.round(node.y+element.y-original.y);
    return x === node.x && y === node.y ? [] : [{id, x, y}];
  });
}

// Hit testing also works for locked paths and the read-only party canvas.
export function graphHit(graph, x, y, tolerance=10) {
  const regions=terrainRegions(graph);
  const hitNode = node => {
    if(node.geometry) {
      const g=node.geometry, angle=-(g.angle || 0),cx=g.x+g.width/2,cy=g.y+g.height/2;
      const px=Math.cos(angle)*(x-cx)-Math.sin(angle)*(y-cy)+g.width/2;
      const py=Math.sin(angle)*(x-cx)+Math.cos(angle)*(y-cy)+g.height/2;
      if(g.points) {
        if(node.category==='terrain')return insideRegion(g.points,px,py);
        return g.points.slice(1).some((b,i)=>{
          const a=g.points[i],dx=b[0]-a[0],dy=b[1]-a[1],length=dx*dx+dy*dy;
          const t=length?Math.max(0,Math.min(1,((px-a[0])*dx+(py-a[1])*dy)/length)):0;
          return Math.hypot(px-a[0]-t*dx,py-a[1]-t*dy)<=tolerance+(g.strokeWidth || 2)*2;
        });
      }
      return px>=-tolerance && px<=g.width+tolerance && py>=-tolerance && py<=g.height+tolerance;
    }
    const style=nodeAppearance(node,graph.kind), dx=Math.abs(x-node.x), dy=Math.abs(y-node.y);
    const w=style.width/2+tolerance,h=style.height/2+tolerance;
    if(regions.has(String(node.id)))return insideRegion(regions.get(String(node.id)).polygon,x,y);
    return style.type==='diamond'?dx/w+dy/h<=1:style.type==='ellipse'?(dx/w)**2+(dy/h)**2<=1:dx<=w && dy<=h;
  };
  const foreground=graph.nodes.filter(node=>!nodeAppearance(node,graph.kind).background).reverse();
  for(const node of foreground)if(hitNode(node))return {id:String(node.id),kind:'location'};
  const nodes=new Map(graph.nodes.map(node=>[String(node.id),node]));
  let closest=null, distance=tolerance;
  for(const edge of graph.edges){
    const a=nodes.get(String(edge.source)), b=nodes.get(String(edge.target));if(!a || !b)continue;
    const dx=b.x-a.x,dy=b.y-a.y,length=dx*dx+dy*dy;
    const t=length?Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/length)):0;
    const d=Math.hypot(x-a.x-t*dx,y-a.y-t*dy);
    if(d<distance){closest={id:String(edge.id),kind:'path'};distance=d;}
  }
  if(closest)return closest;
  for(const node of [...graph.nodes].reverse())if(nodeAppearance(node,graph.kind).background && hitNode(node))return {id:String(node.id),kind:'location'};
  return null;
}

export const emptyDrawing = () => ({elements: [], files: {}});
export const isManaged = element => element.id.startsWith('kw-') || Boolean(element.customData?.kwType);

// Only free drawing belongs in the snapshot. Cards are always projected by Flask.
export function drawingFromScene(elements, files) {
  const drawing = elements.filter(element => !element.isDeleted && !isManaged(element));
  const fileIds = new Set(drawing.filter(element => element.type === 'image').map(element => element.fileId));
  return {elements: drawing, files: Object.fromEntries(Object.entries(files).filter(([id]) => fileIds.has(id)))};
}

export function graphShapes(graph, selected='', selectedEdge='') {
  const nodes = new Map(graph.nodes.map(node => [String(node.id), node]));
  const shapes = [];
  for (const edge of graph.edges) {
    const a = nodes.get(String(edge.source)), b = nodes.get(String(edge.target));
    if (!a || !b) continue;
    shapes.push({id: `kw-edge-${edge.id}`, type: 'line', x: a.x, y: a.y,
      points: [[0, 0], [b.x - a.x, b.y - a.y]], locked: true,
      strokeStyle: edge.path_type === 'hidden' ? 'dashed' : edge.path_type === 'conditional' ? 'dotted' : 'solid',
      strokeColor:String(edge.id)===selectedEdge ? '#e67700' : '#1b1b1f',
      strokeWidth:String(edge.id)===selectedEdge ? 5 : 2, roughness: 0, customData: {kwType: 'path', edgeId:String(edge.id)}});
  }
  for (const node of graph.nodes) {
    shapes.push({id: `kw-node-${node.id}`, type: 'ellipse', x: node.x - 30, y: node.y - 30,
      width: 60, height: 60, strokeColor:String(node.id)===selected ? '#e67700' : '#1b1b1f', backgroundColor: '#ffffff', fillStyle: 'solid', roughness: 0,
      customData: {kwType: 'location', nodeId: String(node.id)}});
    shapes.push({id: `kw-label-${node.id}`, type: 'text', x: node.x - 55, y: node.y + 36,
      text: `${node.number}. ${node.title}`.replace(/(.{1,24})(?:\s+|$)/g,'$1\n').trim(), fontSize: 16, fontFamily: 2, locked: true,
      customData: {kwType: 'label'}});
  }
  return shapes;
}

export function movedLocations(elements, graph) {
  const nodes = new Map(graph.nodes.map(node => [String(node.id), node]));
  return elements.flatMap(element => {
    const id = element.customData?.nodeId;
    const node = nodes.get(id);
    if (!node || element.id !== `kw-node-${id}` || element.isDeleted) return [];
    const x = Math.round(element.x + 30), y = Math.round(element.y + 30);
    return x === node.x && y === node.y ? [] : [{id, x, y}];
  });
}

// Hit testing also works for locked paths and the read-only party canvas.
export function graphHit(graph, x, y, tolerance=10) {
  for(const node of graph.nodes)if(Math.hypot(x-node.x,y-node.y)<=30+tolerance)return {id:String(node.id),kind:'location'};
  const nodes=new Map(graph.nodes.map(node=>[String(node.id),node]));
  let closest=null, distance=tolerance;
  for(const edge of graph.edges){
    const a=nodes.get(String(edge.source)), b=nodes.get(String(edge.target));if(!a || !b)continue;
    const dx=b.x-a.x,dy=b.y-a.y,length=dx*dx+dy*dy;
    const t=length?Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/length)):0;
    const d=Math.hypot(x-a.x-t*dx,y-a.y-t*dy);
    if(d<distance){closest={id:String(edge.id),kind:'path'};distance=d;}
  }
  return closest;
}

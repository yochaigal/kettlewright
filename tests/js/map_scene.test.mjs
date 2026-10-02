import test from 'node:test';
import assert from 'node:assert/strict';
import {drawingFromScene, graphShapes, movedLocations} from '../../app/static/src/js/maps/scene.js';

test('geography is separate from POIs and the water brush requires a Water article',async()=>{
  const {default:pointcrawl}=await import('../../app/static/src/js/alpine/components/pointcrawl.js');
  const component=pointcrawl();
  component.graph.nodes=['terrain','landmark','water','forest','settlement','waypoint','curiosity','lair','dungeon','room']
    .map((category,id)=>({id:String(id),category}));
  assert.deepEqual(component.nodesForGroup('topography').map(n=>n.category),['terrain','landmark','water','forest']);
  assert.deepEqual(component.nodesForGroup('pois').map(n=>n.category),['settlement','waypoint','curiosity','lair','dungeon']);
  assert.deepEqual(component.nodesForGroup('other').map(n=>n.category),['room']);
  const messages=[];
  component.canvasReady=true;
  component.sendCanvas=(...args)=>messages.push(args);
  component.$refs={canvas:{scrollIntoView(){},focus(){}}};
  component.waterBrush();
  component.selected='0';component.waterBrush();
  assert.equal(messages.length,0);
  component.selected='2';component.waterBrush();
  assert.deepEqual(messages,[['water-brush',{width:4,nodeId:'2'}]]);
});

test('drawing snapshots exclude graph labels, deleted content and unused images', () => {
  const elements = [
    {id: 'kw-label-1', type: 'text', text: 'Private room'},
    {id: 'duplicated', customData: {kwType: 'location'}},
    {id: 'deleted', isDeleted: true},
    {id: 'token', type: 'image', fileId: 'image1'},
  ];
  assert.deepEqual(drawingFromScene(elements, {image1: {id: 'image1'}, private: {id: 'private'}}),
    {elements: [elements[3]], files: {image1: {id: 'image1'}}});
});

test('graph conversion preserves IDs and skips paths with hidden endpoints', () => {
  const graph = {nodes: [{id: 1, x: 50, y: 70, number: 1, title: 'Known room'}],
    edges: [{id: 2, source: 1, target: 3}]};
  const shapes = graphShapes(graph);
  assert.deepEqual(shapes.map(shape => shape.id), ['kw-node-1', 'kw-label-1']);
  assert.equal(shapes[0].x, 20);
  assert.equal(shapes[1].text, '1. Known room');
  assert.deepEqual(movedLocations([{...shapes[0], x: 25, y: 45}], graph), [{id: '1', x: 55, y: 75}]);
  assert.deepEqual(movedLocations([{...shapes[0], id: 'copy', x: 25}], graph), []);
});

test('locked paths and nodes are clickable without selecting hidden endpoints', async()=>{
  const {graphHit}=await import('../../app/static/src/js/maps/scene.js');
  const graph={nodes:[{id:1,x:0,y:0},{id:2,x:200,y:0}],edges:[{id:1,source:1,target:2}]};
  assert.deepEqual(graphHit(graph,100,4),{id:'1',kind:'path'});
  assert.deepEqual(graphHit(graph,0,0),{id:'1',kind:'location'});
  assert.equal(graphHit(graph,100,50),null);
  assert.equal(graphHit({...graph,nodes:graph.nodes.slice(0,1)},100,0),null);
});

test('realm geography has layered distinct markers and foreground-first hit testing', async()=>{
  const {graphHit,nodeAppearance}=await import('../../app/static/src/js/maps/scene.js');
  const graph={kind:'realm',nodes:[
    {id:1,category:'terrain',number:1,title:'Hills',x:300,y:250},
    {id:2,category:'water',number:2,title:'River',x:410,y:375},
    {id:3,category:'waypoint',number:3,title:'Tower',x:300,y:250},
    {id:4,category:'settlement',number:4,title:'Town',x:155,y:185}],
    edges:[{id:1,source:3,target:4,path_type:'hidden'}]};
  const shapes=graphShapes(graph);
  assert.equal(shapes[0].type,'line');
  assert.equal(shapes[0].locked,false);
  assert.equal(shapes[0].points.length,5);
  assert.equal(shapes.find(shape=>shape.id==='kw-node-2').type,'ellipse');
  assert.equal(shapes.find(shape=>shape.id==='kw-node-3').type,'diamond');
  assert.match(shapes.find(shape=>shape.id==='kw-label-2').text,/Water/);
  assert.equal(new Set(graph.nodes.map(node=>nodeAppearance(node,'realm').fill)).size,4);
  assert.deepEqual(graphHit(graph,300,250),{id:'3',kind:'location'});
  assert.deepEqual(graphHit(graph,410,375),{id:'2',kind:'location'});
  assert.deepEqual(graphHit(graph,100,100),{id:'1',kind:'location'});
  assert.deepEqual(graphHit(graph,227.5,217.5),{id:'1',kind:'path'});
  assert.equal(movedLocations([{...shapes[0],x:50,y:60}],graph)[0].geometry.x,50);
  assert.deepEqual(drawingFromScene(shapes,{}),{elements:[],files:{}});
});

test('terrain partitions surround landmark seeds and follow moved landmarks without leaking into drawings',async()=>{
  const {terrainRegions,insideRegion}=await import('../../app/static/src/js/maps/terrain.js');
  const graph={kind:'realm',edges:[],nodes:[
    {id:1,category:'terrain',title:'Hills',x:0,y:0},
    {id:2,category:'terrain',title:'Plains',x:900,y:0},
    {id:3,category:'terrain',title:'Mountains',x:700,y:800},
    {id:4,category:'landmark',title:'Tower',terrain_id:1,x:0,y:0},
    {id:5,category:'landmark',title:'Menhirs',terrain_id:2,x:900,y:0},
    {id:6,category:'landmark',title:'Volcano',terrain_id:3,x:700,y:800}]};
  const regions=terrainRegions(graph);
  assert.equal(regions.size,3);
  for(const region of regions.values())assert(insideRegion(region.polygon,region.x,region.y));
  // Every sampled point belongs to exactly one region; interiors do not overlap.
  for(let x=-300;x<1200;x+=53)for(let y=-300;y<1100;y+=47) {
    assert.equal([...regions.values()].filter(r=>insideRegion(r.polygon,x,y)).length,1);
  }
  const shapes=graphShapes(graph),marker=shapes.find(s=>s.id==='kw-node-4');
  assert.equal(marker.type,'line');
  assert.equal(marker.points.length,4);
  assert.deepEqual(marker.points[0],marker.points[3]);
  assert.deepEqual(movedLocations([{...marker,x:marker.x+120,y:marker.y+40}],graph),[{id:'4',x:120,y:40}]);
  graph.nodes[3].x=120;graph.nodes[3].y=40;
  const updated=terrainRegions(graph);
  assert.equal(updated.get('1').x,120);
  assert.notDeepEqual(updated.get('2').polygon,regions.get('2').polygon);
  assert.deepEqual(drawingFromScene(graphShapes(graph),{}),{elements:[],files:{}});
});

test('realm geography applies through the component endpoint and sends both versions',async t=>{
  const {default:pointcrawl}=await import('../../app/static/src/js/alpine/components/pointcrawl.js');
  const component=pointcrawl();
  const fields=new Map();
  t.mock.method(globalThis,'fetch',async(url,options)=>{
    assert.equal(url,'/maps/7/geography');
    assert.equal(options.method,'POST');
    assert.equal(fields.get('version'),4);
    assert.equal(fields.get('article_version'),2);
    assert.equal(fields.get('children'),'[]');
    return {ok:true,json:async()=>({nodes:[],edges:[],version:5,article_version:2})};
  });
  t.mock.method(globalThis,'FormData',function(){return {set:(key,value)=>fields.set(key,value)};});
  Object.assign(component,{$el:{dataset:{}},$refs:{saveForm:{}},$nextTick:callback=>callback(),fit(){},
    geographyUrl:'/maps/7/geography',geographyDraft:[],graph:{version:4,article_version:2},labels:{saved:'Saved'}});
  await component.applyGeography();
  assert.equal(component.graph.version,5);
  assert.equal(component.geographyDraft,null);
  assert.equal(component.dirty,false);
  assert.equal(component.status,'Saved');
});

test('resized terrain and drawn water retain their shapes and article hit targets',async()=>{
  const {graphHit}=await import('../../app/static/src/js/maps/scene.js');
  const graph={kind:'realm',edges:[],nodes:[{id:1,category:'terrain',title:'Hills',x:300,y:250},
    {id:2,category:'water',title:'River',x:100,y:100}]};
  const shape=graphShapes(graph)[0];
  assert.deepEqual(movedLocations([{...shape,angle:0}],graph),[]);
  assert.deepEqual(movedLocations([{angle:0,...shape,width:shape.width+1e-9}],graph),[]);
  const resized={...shape,width:shape.width*2,points:shape.points.map(([x,y])=>[x*2,y])};
  const [change]=movedLocations([resized],graph);
  Object.assign(graph.nodes[0],change);
  assert.equal(graphShapes(graph)[0].width,resized.width);
  graph.nodes.push({id:3,category:'landmark',title:'Tower',terrain_id:1,x:2000,y:2000});
  assert.deepEqual(graphShapes(graph)[0].points,resized.points);
  graph.nodes[1].geometry={type:'freedraw',x:0,y:0,width:300,height:100,angle:0,strokeWidth:4,
    points:[[0,0],[100,100],[300,0]]};
  const water=graphShapes(graph).find(e=>e.id==='kw-node-2');
  assert.equal(water.type,'freedraw');
  assert.deepEqual(graphHit(graph,200,50),{id:'2',kind:'location'});
  assert.notDeepEqual(graphHit(graph,200,100),{id:'2',kind:'location'});
  assert.deepEqual(drawingFromScene(graphShapes(graph),{}),{elements:[],files:{}});
});

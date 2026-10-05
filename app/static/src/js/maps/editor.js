import {h, render} from 'preact';
import {Excalidraw, convertToExcalidrawElements, restoreElements, CaptureUpdateAction, getCommonBounds} from 'excalidraw';
import {drawingFromScene, emptyDrawing, graphShapes, movedLocations, isManaged, graphHit, editableGeography, shapeGeometry} from './scene.js';
import {loadLibraries} from './libraries.js';
import {fittedViewport} from './viewport.js';

let api, state, applying = false, lastDrawing = '', inputDrawingKey = '', graphKey = '', disposed = false, repairing = false, initialized = false;
let waterTarget=null, brushStartIds=null;
const send = (type, detail = {}) => parent.postMessage({channel: 'kw-map', type, ...detail}, location.origin);
const managedElements = graph => restoreElements(convertToExcalidrawElements(graphShapes(graph, state.selected, state.selectedEdge), {regenerateIds:false}), null);
const orderedScene = (free, managed) => [
  ...managed.filter(e=>e.customData?.nodeId && state.graph.nodes.some(n=>String(n.id)===e.customData.nodeId && n.category==='terrain')),
  ...free,
  ...managed.filter(e=>!e.customData?.nodeId || !state.graph.nodes.some(n=>String(n.id)===e.customData.nodeId && n.category==='terrain')),
];

function fitDrawing() {
  if (!api) return;
  const elements = api.getSceneElements();
  if (!elements.length) return;
  const {width, height} = api.getAppState();
  api.updateScene({appState: fittedViewport(getCommonBounds(elements), width, height),
    captureUpdate: CaptureUpdateAction.NEVER});
}

function applyState(next) {
  const selectionChanged = state?.selected !== next.selected;
  state = next;
  if (!api || !initialized) return;
  applying = true;
  try {
    const drawing = state.graph.drawing || emptyDrawing();
    const nextKey = JSON.stringify([state.graph.nodes, state.graph.edges, state.selected, state.selectedEdge]);
    const drawingKey = JSON.stringify(drawing);
    if (nextKey !== graphKey || drawingKey !== inputDrawingKey) {
      const free = drawingKey === inputDrawingKey
        ? api.getSceneElements().filter(element => !isManaged(element))
        : restoreElements(drawing.elements, null);
      const managed = managedElements(state.graph);
      api.addFiles(Object.values(drawing.files));
      api.updateScene({elements: orderedScene(free, managed), captureUpdate: CaptureUpdateAction.NEVER});
      // Revoked/replaced snapshots must not remain in undo history.
      if (!state.editing || drawingKey !== inputDrawingKey) api.history.clear();
      graphKey = nextKey;
      inputDrawingKey = drawingKey;
      lastDrawing = JSON.stringify(drawingFromScene(api.getSceneElements(), api.getFiles()));
    }
    if (selectionChanged) {
      const selectedElementIds = state.selected ? {[`kw-node-${state.selected}`]: true} : {};
      api.updateScene({appState: {selectedElementIds}, captureUpdate: CaptureUpdateAction.NEVER});
    }
  } finally {applying = false;}
}

function onChange(elements, appState, files) {
  if (!api || !state || applying || disposed) return;
  if (!initialized) {
    if (appState.isLoading) return;
    initialized = true;
    lastDrawing = JSON.stringify(drawingFromScene(elements, files));
    graphKey = JSON.stringify([state.graph.nodes, state.graph.edges, state.selected, state.selectedEdge]);
    send('mounted');
    setTimeout(() => {if (!disposed) {applyState(state); fitDrawing();}}, 0);
    return;
  }
  const selected = elements.find(element => appState.selectedElementIds[element.id] && element.customData?.kwType === 'location');
  if (selected && selected.customData.nodeId !== state.selected) {
    state.selected = selected.customData.nodeId;
    send('select', {id: state.selected, scroll:false});
  }
  if (!state.editing) return;
  if(waterTarget!==null && appState.activeTool.type!=='freedraw') {waterTarget=null;brushStartIds=null;}
  // Graph cards have their own delete/rename workflow. Restore erased, duplicated
  // graph glyphs instead of silently diverging from the saved graph. Terrain
  // and water explicitly support resized and reshaped geometry.
  const managed = elements.filter(element => isManaged(element) && !element.isDeleted);
  const expected = graphShapes(state.graph, state.selected, state.selectedEdge);
  const damaged = managed.length !== expected.length || expected.some(shape => {
    const actual = managed.find(element => element.id === shape.id);
    const node=state.graph.nodes.find(node=>String(node.id)===shape.customData?.nodeId);
    return !actual || shape.customData?.kwType === 'location' && !editableGeography(node) && (actual.type !== shape.type || actual.width !== shape.width || actual.height !== shape.height || actual.angle !== 0)
      || shape.type === 'text' && actual.text !== shape.text;
  });
  if (damaged && !repairing) {
    repairing = true;
    setTimeout(() => {repairing = false; if (!disposed) {graphKey = ''; applyState(state);}}, 0);
  }
  const moves = movedLocations(elements, state.graph);
  const drawing = drawingFromScene(elements, files);
  const key = JSON.stringify(drawing);
  if (key === lastDrawing && !moves.length) return;
  lastDrawing = key;
  inputDrawingKey = key;
  state.graph.drawing = drawing;
  for (const move of moves) Object.assign(state.graph.nodes.find(node => String(node.id) === move.id), move);
  send('change', {drawing, moves});
}

function mount(next) {
  state = next;
  const drawing = next.graph.drawing || emptyDrawing();
  const library = next.editing ? loadLibraries() : Promise.resolve({items: [], failed: false});
  inputDrawingKey = JSON.stringify(drawing);
  render(h(Excalidraw, {
    excalidrawAPI: instance => {
      api = instance;
      library.then(result => {
        if (!disposed && result.failed) api?.setToast({message: 'Some map libraries could not load. Reload the editor to retry.'});
      });
    },
    initialData: {elements: orderedScene(restoreElements(drawing.elements, null),managedElements(next.graph)),
      files: drawing.files, libraryItems: library.then(result => result.items), appState: {gridModeEnabled: true}},
    viewModeEnabled: !next.editing,
    theme: next.dark ? 'dark' : 'light',
    langCode: next.lang || 'en',
    onChange, validateEmbeddable: () => false,
    UIOptions: {canvasActions: {loadScene: false, saveToActiveFile: false, export: false, toggleTheme: false}},
  }), document.getElementById('editor'));
}

window.addEventListener('message', event => {
  if (event.source !== parent || event.origin !== location.origin || event.data?.channel !== 'kw-map') return;
  const message = event.data;
  if (message.type === 'state') {
    if (!state) mount(message);
    else {
      applyState(message);
      // Keep the host's theme in sync without remounting the editor.
      api?.updateScene({appState: {theme: message.dark ? 'dark' : 'light'}});
    }
  } else if (message.type === 'fit') fitDrawing();
  else if (message.type === 'water-brush' && state?.editing && api) {
    const target=state.graph.nodes.find(node=>String(node.id)===String(message.nodeId) && node.category==='water');
    if(!target)return;
    waterTarget=null;
    api.updateScene({appState:{selectedElementIds:{},currentItemStrokeColor:'#1971c2',currentItemBackgroundColor:'transparent',
      currentItemStrokeWidth:[2,4,8].includes(message.width)?message.width:4,currentItemRoughness:0}});
    api.setActiveTool({type:'freedraw'});
    waterTarget=target.id;
    brushStartIds=new Set(api.getSceneElements().map(e=>e.id));
  }
  else if (message.type === 'select-tool' && state?.editing && api) {
    waterTarget=null;brushStartIds=null;api.setActiveTool({type:'selection'});
  }
  else if (message.type === 'clear') {
    disposed = true;
    render(null, document.getElementById('editor'));
    api = null; state = null;
  }
});
send('ready');

let pointerStart;
document.getElementById('editor').addEventListener('keyup',event=>{
  if(event.key.startsWith('Arrow') && state?.editing && state.graph.kind==='realm') {
    graphKey='';applyState(state);
  }
});
document.getElementById('editor').addEventListener('pointerdown',event=>{
  if(event.target.tagName!=='CANVAS' || event.button!==0 || !api)return;
  const tool=api.getAppState().activeTool.type;
  if(state.editing && !['selection','hand'].includes(tool))return;
  pointerStart={x:event.clientX,y:event.clientY};
},true);
document.getElementById('editor').addEventListener('pointerup',event=>{
  if(waterTarget!==null && api?.getAppState().activeTool.type==='freedraw') {
    const target=waterTarget, previousIds=brushStartIds;
    setTimeout(()=>{
      if(disposed || !api)return;
      const stroke=api.getSceneElements().find(e=>e.type==='freedraw' && !previousIds.has(e.id));
      const node=state.graph.nodes.find(n=>n.id===target);
      if(!stroke || !node || stroke.points.length<2)return;
      // The stroke belongs to this water article, so it follows the same
      // visibility rules as its former marker rather than the free drawing.
      node.geometry=shapeGeometry(stroke);
      node.x=stroke.x+stroke.width/2;node.y=stroke.y+stroke.height/2;
      const drawing=drawingFromScene(api.getSceneElements().filter(e=>e.id!==stroke.id),api.getFiles());
      state.graph.drawing=drawing;
      waterTarget=null;brushStartIds=null;
      inputDrawingKey='';graphKey='';
      send('change',{drawing,moves:[{id:String(node.id),x:node.x,y:node.y,geometry:node.geometry}]});
      api.setActiveTool({type:'selection'});applyState(state);
    },0);
  }
  const start=pointerStart;pointerStart=null;
  // Rebuild terrain around the final landmark position after a drag, without
  // replacing the scene while the pointer is still down.
  if(start && state?.editing && state.graph.kind==='realm' && Math.hypot(event.clientX-start.x,event.clientY-start.y)>6) {
    setTimeout(()=>{if(!disposed){graphKey='';applyState(state);}},0);
  }
  if(!start || !api || Math.hypot(event.clientX-start.x,event.clientY-start.y)>6)return;
  const view=api.getAppState(), zoom=view.zoom.value;
  const hit=graphHit(state.graph,(event.clientX-view.offsetLeft)/zoom-view.scrollX,
    (event.clientY-view.offsetTop)/zoom-view.scrollY,10/zoom);
  if(hit)send('select',hit);
},true);

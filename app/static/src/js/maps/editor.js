import {h, render} from 'preact';
import {Excalidraw, convertToExcalidrawElements, restoreElements, CaptureUpdateAction, getCommonBounds} from 'excalidraw';
import {drawingFromScene, emptyDrawing, graphShapes, movedLocations, isManaged, graphHit, editableGeography, shapeGeometry,
  pinShapes, pinHit, pinDiameter, pinTooltip} from './scene.js';
import {createFogLayer} from './whiteboard_fog.js';
import {loadLibraries} from './libraries.js';
import {fittedViewport, imageViewport, clampToImage, wheelScrollsPage} from './viewport.js';
import {editorLocale} from './locale.js';
import {applyCanvasUI} from './canvas_ui.js';

let api, state, applying = false, lastDrawing = '', inputDrawingKey = '', graphKey = '', disposed = false, repairing = false, initialized = false;
let waterTarget=null, brushStartIds=null;
// Party map view only: the party's fog (Warden uncovers it) and pins (click to place one).
let fogLayer=null, picking=false;
const send = (type, detail = {}) => parent.postMessage({channel: 'kw-map', type, ...detail}, location.origin);
const managedElements = graph => restoreElements(convertToExcalidrawElements(
  [...graphShapes(graph, state.selected, state.selectedEdge), ...pinShapes(state.pins, state.selectedPin, pinDiameter(graph))], {regenerateIds:false}), null);
const sceneKey = () => JSON.stringify([state.graph.nodes, state.graph.edges, state.graph.pin_size, state.selected, state.selectedEdge,
  state.pins || [], state.selectedPin || '']);

function syncFog() {
  if (!state?.fog || !api) return;
  if (!fogLayer) fogLayer = createFogLayer({editor: document.getElementById('editor'), getApi: () => api,
    warden: Boolean(state.fogWarden), onOperation: operation => send('fog-operation', {operation})});
  fogLayer.setState(state.fog);
}
const orderedScene = (free, managed) => [
  ...managed.filter(e=>e.customData?.nodeId && state.graph.nodes.some(n=>String(n.id)===e.customData.nodeId && n.category==='terrain')),
  ...free,
  ...managed.filter(e=>!e.customData?.nodeId || !state.graph.nodes.some(n=>String(n.id)===e.customData.nodeId && n.category==='terrain')),
];

// An image map (#506): its drawing is one locked picture at (0, 0), the lowest element. Pins and fog
// are in its coordinates. Readers see the picture alone: no grid, no editor UI, no canvas around it.
const isImageMap = () => state?.graph?.kind === 'image';
const mapImage = () => api?.getSceneElements().find(element => element.type === 'image' && !element.isDeleted);
const imageBounds = image => [image.x, image.y, image.x + image.width, image.y + image.height];
let clamping = false;

function imageMapLook() {
  const image = isImageMap();
  document.body.classList.toggle('image-map', image);
  document.body.classList.toggle('image-map-reading', image && !state.editing);
  // Drawing on a map: the tools are a rail on the side, as on the whiteboard (editor.html).
  document.body.classList.toggle('drawing-editor', !image && Boolean(state.editing));
  // Clean view (Discord feedback): the page's toggles hide Excalidraw's controls (css/canvas_ui.css).
  document.body.classList.toggle('canvas-reading', !state.editing);
  applyCanvasUI(document.body, state.ui);
  return image ? {gridModeEnabled: false, viewBackgroundColor: 'transparent', zenModeEnabled: !state.editing}
    : {gridModeEnabled: true};
}

function fitDrawing() {
  if (!api) return;
  const elements = api.getSceneElements();
  if (!elements.length) return;
  const {width, height} = api.getAppState();
  const image = isImageMap() && mapImage();
  api.updateScene({appState: image ? imageViewport(imageBounds(image), width, height)
    : fittedViewport(getCommonBounds(elements), width, height),
    captureUpdate: CaptureUpdateAction.NEVER});
}

// A pin chosen in a list (#533): the view keeps its zoom and centres on it (inside the picture, on an image map).
function centerOn({x, y}) {
  if (!api || !Number.isFinite(x) || !Number.isFinite(y)) return;
  const {width, height, zoom} = api.getAppState();
  api.updateScene({appState: {scrollX: width / (2 * zoom.value) - x, scrollY: height / (2 * zoom.value) - y},
    captureUpdate: CaptureUpdateAction.NEVER});
  keepInsideImage(api.getAppState());
}

// Readers zoom and pan inside the picture only.
function keepInsideImage(appState) {
  if (clamping || !isImageMap() || state.editing) return;
  const image = mapImage();
  const next = image && clampToImage(imageBounds(image), appState);
  if (!next) return;
  clamping = true;
  try {api.updateScene({appState: next, captureUpdate: CaptureUpdateAction.NEVER});} finally {clamping = false;}
}

// New map > Image, or Replace image: the picture becomes the map's lowest element, locked. A replacement
// keeps the old picture's width, so pins and fog stay where they were on a new version of the same map.
function setMapImage({dataURL, mimeType, width, height}) {
  if (!api || !state?.editing || !dataURL || !(width > 0) || !(height > 0)) return;
  const fileId = crypto.randomUUID().replaceAll('-', '');
  api.addFiles([{id: fileId, dataURL, mimeType, created: Date.now()}]);
  const elements = api.getSceneElements();
  const current = mapImage();
  // A new picture: 1600 units on its long side, so pins and the fog brush keep their usual size on it.
  const scale = current ? current.width / width : 1600 / Math.max(width, height);
  const [image] = restoreElements(convertToExcalidrawElements([{type: 'image', id: current?.id || 'map-image', fileId,
    x: current?.x ?? 0, y: current?.y ?? 0, width: width * scale, height: height * scale, locked: true, status: 'saved'}],
    {regenerateIds: false}), null);
  api.updateScene({elements: [image, ...elements.filter(element => element.id !== image.id)],
    appState: imageMapLook(), captureUpdate: CaptureUpdateAction.IMMEDIATELY});
  fitDrawing();
}

function applyState(next) {
  const selectionChanged = state?.selected !== next.selected;
  state = next;
  if (!api || !initialized) return;
  applying = true;
  try {
    const drawing = state.graph.drawing || emptyDrawing();
    const nextKey = sceneKey();
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
    syncFog();
    applyCanvasUI(document.body, state.ui);
    if (isImageMap() !== document.body.classList.contains('image-map')) {
      api.updateScene({appState: imageMapLook(), captureUpdate: CaptureUpdateAction.NEVER});
    }
    if (selectionChanged) {
      const selectedElementIds = state.selected ? {[`kw-node-${state.selected}`]: true} : {};
      api.updateScene({appState: {selectedElementIds}, captureUpdate: CaptureUpdateAction.NEVER});
    }
  } finally {applying = false;}
}

function onChange(elements, appState, files) {
  fogLayer?.redraw();  // Fog follows panning and zooming.
  if (!api || !state || applying || disposed) return;
  if (initialized) keepInsideImage(appState);
  if (!initialized) {
    if (appState.isLoading) return;
    initialized = true;
    lastDrawing = JSON.stringify(drawingFromScene(elements, files));
    graphKey = sceneKey();
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
  // The players' pins (#482) are drawn here too, read only: they are expected, not damage.
  const expected = [...graphShapes(state.graph, state.selected, state.selectedEdge),
    ...pinShapes(state.pins, state.selectedPin, pinDiameter(state.graph))];
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
        if (!disposed && result.failed) api?.setToast({message: next.libraryError || 'Some map libraries could not load. Reload the editor to retry.'});
      });
    },
    initialData: {elements: orderedScene(restoreElements(drawing.elements, null),managedElements(next.graph)),
      files: drawing.files, libraryItems: library.then(result => result.items), appState: imageMapLook()},
    viewModeEnabled: !next.editing,
    theme: next.dark ? 'dark' : 'light',
    langCode: editorLocale(next.lang),
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
  else if (message.type === 'center') centerOn(message);
  else if (message.type === 'set-image') setMapImage(message);
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
  else if (message.type === 'pick-point') {picking = Boolean(message.value);}
  else if (message.type === 'fog-tool' && fogLayer) {fogLayer.setTool(message.tool || ''); if (message.radius) fogLayer.setRadius(message.radius);}
  else if (message.type === 'fog-preview' && fogLayer) {fogLayer.setPreview(Boolean(message.value));}
  else if (message.type === 'clear') {
    disposed = true;
    render(null, document.getElementById('editor'));
    api = null; state = null;
  }
});
send('ready');

let pointerStart;
// Moving a pin on the party map (#482): its maker or the Warden drags it (the canvas is read only there).
let dragging=null;
const pinReach=zoom=>Math.max(16/zoom,pinDiameter(state.graph)/2+4/zoom);
const scenePoint=(clientX,clientY)=>{
  const view=api.getAppState(), zoom=view.zoom.value;
  return {x:(clientX-view.offsetLeft)/zoom-view.scrollX, y:(clientY-view.offsetTop)/zoom-view.scrollY};
};
document.getElementById('editor').addEventListener('pointerdown',event=>{
  if(event.target.tagName!=='CANVAS' || event.button!==0 || !api || !state || state.editing || picking)return;
  const point=scenePoint(event.clientX,event.clientY);
  const pin=pinHit(state.pins,point.x,point.y,pinReach(api.getAppState().zoom.value));
  if(!pin?.movable)return;
  // Keep the canvas from panning while the pin moves.
  event.stopPropagation();event.preventDefault();
  dragging={pin,start:{x:event.clientX,y:event.clientY},origin:{x:pin.x,y:pin.y},offset:{x:pin.x-point.x,y:pin.y-point.y},moved:false};
},true);
window.addEventListener('pointermove',event=>{
  if(!dragging || !api)return;
  if(!dragging.moved && Math.hypot(event.clientX-dragging.start.x,event.clientY-dragging.start.y)<5)return;
  dragging.moved=true;
  const point=scenePoint(event.clientX,event.clientY);
  dragging.pin.x=Math.round(point.x+dragging.offset.x);dragging.pin.y=Math.round(point.y+dragging.offset.y);
  if(!dragging.frame)dragging.frame=requestAnimationFrame(()=>{if(dragging)dragging.frame=null;applyState(state);});
});
window.addEventListener('pointerup',()=>{
  if(!dragging)return;
  const {pin,moved,origin}=dragging;dragging=null;
  // A click without a drag selects the pin (the pointerup handler below).
  if(moved && (pin.x!==origin.x || pin.y!==origin.y))send('move-pin',{id:String(pin.id),x:pin.x,y:pin.y});
});
document.getElementById('editor').addEventListener('keyup',event=>{
  if(event.key.startsWith('Arrow') && state?.editing && state.graph.kind==='realm') {
    graphKey='';applyState(state);
  }
});
document.getElementById('editor').addEventListener('pointerdown',event=>{
  if(event.target.tagName!=='CANVAS' || event.button!==0 || !api)return;
  const tool=api.getAppState().activeTool.type;
  if(state.editing && !['selection','hand'].includes(tool))return;
  // Screen coordinates measure the drag: focusing the frame can scroll the page between down and up.
  pointerStart={x:event.clientX,y:event.clientY,screenX:event.screenX,screenY:event.screenY};
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
  const moved=start?Math.hypot(event.screenX-start.screenX,event.screenY-start.screenY):0;
  // Rebuild terrain around the final landmark position after a drag, without
  // replacing the scene while the pointer is still down.
  if(start && state?.editing && state.graph.kind==='realm' && moved>6) {
    setTimeout(()=>{if(!disposed){graphKey='';applyState(state);}},0);
  }
  if(!start || !api || moved>6)return;
  const view=api.getAppState(), zoom=view.zoom.value;
  const sceneX=(start.x-view.offsetLeft)/zoom-view.scrollX, sceneY=(start.y-view.offsetTop)/zoom-view.scrollY;
  if(picking){picking=false;send('picked',{x:sceneX,y:sceneY});return;}
  const pin=pinHit(state.pins,sceneX,sceneY,pinReach(zoom));
  if(pin){send('select-pin',{id:String(pin.id)});return;}
  const hit=graphHit(state.graph,sceneX,sceneY,10/zoom);
  if(hit)send('select',hit);
},true);

// A pin's title on hover (#494): pins are drawn without it. Touch screens tap the pin to open it instead.
const tooltip=document.createElement('div');
tooltip.className='pin-tooltip';tooltip.setAttribute('role','tooltip');tooltip.hidden=true;
document.body.append(tooltip);
const hideTooltip=()=>{tooltip.hidden=true;};
document.getElementById('editor').addEventListener('pointermove',event=>{
  if(event.pointerType==='touch' || event.buttons || dragging || !api || !state || event.target.tagName!=='CANVAS')return hideTooltip();
  const zoom=api.getAppState().zoom.value, point=scenePoint(event.clientX,event.clientY);
  const title=pinTooltip(state.graph,state.pins,point.x,point.y,4/zoom);
  if(!title)return hideTooltip();
  tooltip.textContent=title;
  tooltip.classList.toggle('is-dark',Boolean(state.dark));
  tooltip.hidden=false;
  // Beside the pointer, kept inside the frame.
  const x=Math.min(event.clientX+14,innerWidth-tooltip.offsetWidth-4), y=event.clientY+18+tooltip.offsetHeight>innerHeight
    ? event.clientY-tooltip.offsetHeight-10 : event.clientY+18;
  tooltip.style.left=`${Math.max(4,x)}px`;tooltip.style.top=`${Math.max(4,y)}px`;
});
document.getElementById('editor').addEventListener('pointerleave',hideTooltip);
document.getElementById('editor').addEventListener('pointerdown',hideTooltip);
document.getElementById('editor').addEventListener('wheel',hideTooltip,{passive:true});

// An image map being read (#533): the wheel scrolls the page around it (wheelScrollsPage).
document.getElementById('editor').addEventListener('wheel', event => {
  const image = api && state && isImageMap() && mapImage();
  if (!image) return;
  const view = api.getAppState();
  const fit = imageViewport(imageBounds(image), view.width, view.height).zoom.value;
  if (!wheelScrollsPage({editing: state.editing, imageMap: true, zoom: view.zoom.value, fitZoom: fit,
    ctrlKey: event.ctrlKey, metaKey: event.metaKey})) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const lines = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1;
  send('scroll', {x: event.deltaX * lines, y: event.deltaY * lines});
}, {capture: true, passive: false});

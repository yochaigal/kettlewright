import {h, render} from 'preact';
import {Excalidraw, convertToExcalidrawElements, restoreElements, CaptureUpdateAction} from 'excalidraw';
import {drawingFromScene, emptyDrawing, graphShapes, movedLocations, isManaged, graphHit} from './scene.js';
import {loadLibraries} from './libraries.js';

let api, state, applying = false, lastDrawing = '', inputDrawingKey = '', graphKey = '', disposed = false, repairing = false, initialized = false;
const send = (type, detail = {}) => parent.postMessage({channel: 'kw-map', type, ...detail}, location.origin);

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
      const managed = convertToExcalidrawElements(graphShapes(state.graph, state.selected, state.selectedEdge), {regenerateIds: false});
      api.addFiles(Object.values(drawing.files));
      api.updateScene({elements: [...free, ...managed], captureUpdate: CaptureUpdateAction.NEVER});
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
    setTimeout(() => {if (!disposed) {applyState(state); api.scrollToContent(undefined, {fitToContent: true, viewportZoomFactor: 0.7});}}, 0);
    return;
  }
  const selected = elements.find(element => appState.selectedElementIds[element.id] && element.customData?.kwType === 'location');
  if (selected && selected.customData.nodeId !== state.selected) {
    state.selected = selected.customData.nodeId;
    send('select', {id: state.selected});
  }
  if (!state.editing) return;
  // Graph cards have their own delete/rename workflow. Restore erased, duplicated
  // or resized graph glyphs instead of silently diverging from the saved graph.
  const managed = elements.filter(element => isManaged(element) && !element.isDeleted);
  const expected = graphShapes(state.graph, state.selected, state.selectedEdge);
  const damaged = managed.length !== expected.length || expected.some(shape => {
    const actual = managed.find(element => element.id === shape.id);
    return !actual || shape.type === 'ellipse' && (actual.width !== 60 || actual.height !== 60 || actual.angle !== 0)
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
    initialData: {elements: [...restoreElements(drawing.elements, null),
      ...convertToExcalidrawElements(graphShapes(next.graph, next.selected, next.selectedEdge), {regenerateIds: false})],
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
  } else if (message.type === 'fit') api?.scrollToContent(undefined, {fitToContent: true, viewportZoomFactor: 0.7});
  else if (message.type === 'clear') {
    disposed = true;
    render(null, document.getElementById('editor'));
    api = null; state = null;
  }
});
send('ready');

let pointerStart;
document.getElementById('editor').addEventListener('pointerdown',event=>{
  if(event.target.tagName!=='CANVAS' || event.button!==0 || !api)return;
  const tool=api.getAppState().activeTool.type;
  if(state.editing && !['selection','hand'].includes(tool))return;
  pointerStart={x:event.clientX,y:event.clientY};
},true);
document.getElementById('editor').addEventListener('pointerup',event=>{
  const start=pointerStart;pointerStart=null;
  if(!start || !api || Math.hypot(event.clientX-start.x,event.clientY-start.y)>6)return;
  const view=api.getAppState(), zoom=view.zoom.value;
  const hit=graphHit(state.graph,(event.clientX-view.offsetLeft)/zoom-view.scrollX,
    (event.clientY-view.offsetTop)/zoom-view.scrollY,10/zoom);
  if(hit)send('select',hit);
},true);

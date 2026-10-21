import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {drawingFromScene} from '../../app/static/src/js/maps/scene.js';
const source = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_session.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));
const plain = value => JSON.parse(JSON.stringify(value));
class Node {
  constructor(tag) {this.tagName = tag; this.children = []; this.events = {}; this.style = {}; this.hidden = false;}
  append(...children) {this.children.push(...children);}
  replaceChildren(...children) {this.children = children;}
  addEventListener(name, fn) {this.events[name] = fn;}
  removeEventListener() {}
  setAttribute() {}
  remove() {}
  querySelector() {return new Node('button');}
}
const token = (id = 'actor-1-one', canControl = true) => ({id, actor_id: '1', name: 'Moss', kind: 'character', can_control: canControl,
  visible: true, element: {id, type: 'image', fileId: 'f', x: 10, y: 20, width: 80, height: 80, angle: 0}, files: {f: {id:'f', dataURL:'image'}}});
const snapshot = (tokens = [], revisions = {}) => ({protocol:2, scene_id:1, generation:1, activation_version:0, active_scene_id:1,
  name:'Whiteboard', tokens_version:0, encounter_version:0, markers_version:0, tokens, markers:[], encounter:{round:1,participants:[]}, ...revisions});
function setup({warden = false} = {}) {
  const nodes = new Map(), requests = [], handlers = {}, intervals = [], timers = new Map();
  let id = 0, elements = [], stopped = false;
  const doc = {hidden:false, getElementById(name) {if (!warden && ['scene-controls', 'scene-activate'].includes(name)) return null; if (!nodes.has(name)) nodes.set(name,new Node('div')); return nodes.get(name);},
    createElement: tag => new Node(tag), createTextNode: text => ({textContent:text}), addEventListener() {}, removeEventListener() {}, querySelector: () => new Node('div')};
  const api = {getSceneElements: () => elements, getAppState: () => ({selectedElementIds:{},zoom:{value:1},scrollX:0,scrollY:0,width:800,height:600}),
    addFiles() {}, updateScene(data) {if (data.elements) elements = data.elements;}, setToast() {}};
  const config = {boardUrl:'/party/1/shared-map',partyId:1,csrfToken:'csrf',warden,
    messages:{showScene:'Show to party',showingScene:'Showing…',activeScene:'Shown to party',
      shownSceneHelp:'Players stay here until you show another scene.',privateSceneHelp:'Showing this scene moves all players here.'}};
  const context = vm.createContext({document:doc,window:{addEventListener() {},removeEventListener() {},matchMedia: () => ({matches:false})},
    setTimeout(fn) {timers.set(++id,fn); return id;},clearTimeout: key => timers.delete(key),setInterval(fn) {intervals.push(fn);return 1;},clearInterval() {},
    requestAnimationFrame: () => 1,cancelAnimationFrame() {},queueMicrotask,structuredClone,AbortSignal,
    restoreElements: value => value,CaptureUpdateAction:{NEVER:'never'},initials: name => name[0],
    fetch: (url,options) => new Promise(resolve => requests.push({url,options,resolve})),
  });
  vm.runInContext(source+'\nthis.create = createWhiteboardSession;',context);
  const session = context.create({config,socket:{connected:false,on(name,fn) {handlers[name] = fn;},off() {}},getApi: () => api,
    project: fn => fn(),refresh:async () => {},switchScene:async () => {},flushDrawing:async () => {},preserveDraft() {},isPreview: () => false});
  return {session,requests,nodes,config,handlers,api,timers,
    elements: () => elements,
    async timersRun() {const queued=[...timers.values()];timers.clear();queued.forEach(fn=>fn());await tick();},
    async respond(data) {requests.shift().resolve({ok:true,status:200,json:async () => data});await tick();},
    finish() {session.destroy();},
  };
}

test('initial scene includes managed tokens and image files before the first canvas change', () => {
  const s=setup(); s.session.accept(snapshot([token()]));
  const initial=s.session.initialDrawing({elements:[],files:{}});
  assert.equal(initial.elements.length,1); assert.equal(initial.elements[0].customData.kwType,'token');
  assert.equal(initial.files.f.dataURL,'image');
  s.session.capture(initial.elements);
  assert.equal(s.session.busy,false);
  assert.deepEqual(plain(drawingFromScene(initial.elements,initial.files)),{elements:[],files:{}});
  s.finish();
});

test('own token movement uses an explicit scene and a separate token operation', async () => {
  const s=setup(); s.session.accept(snapshot([token()]));
  s.session.capture([{...s.elements()[0],x:90}]); await s.timersRun();
  assert.equal(s.requests.length,1); const body=JSON.parse(s.requests[0].options.body);
  assert.equal(body.scene_id,1); assert.equal(body.protocol,2); assert.equal(body.activation_version,0);
  assert.equal(body.operations[0].geometry.x,90); assert.equal(body.drawing,undefined);
  await s.respond(snapshot([{...token(),element:{...token().element,x:90}}],{tokens_version:1}));
  assert.equal(s.session.busy,false); s.finish();
});

test('foreign token deletion and geometry changes are restored without writes', async () => {
  const s=setup();s.session.accept(snapshot([token('actor-1-one',false)]));
  s.session.capture([]); await tick();
  assert.equal(s.session.busy,false); assert.equal(s.elements().length,1);
  s.session.capture([{...s.elements()[0],x:400}]); await tick();
  assert.equal(s.elements()[0].x,10); assert.equal(s.requests.length,0); s.finish();
});

test('late token responses cannot replace a new scene or undo a newer snapshot', async () => {
  const s=setup();s.session.accept(snapshot([token()]));
  s.session.capture([{...s.elements()[0],x:40}]);await s.timersRun();
  s.session.accept(snapshot([{...token(),element:{...token().element,x:50}}],{tokens_version:3}));
  await s.respond(snapshot([{...token(),element:{...token().element,x:40}}],{tokens_version:1}));
  assert.equal(s.elements()[0].x,50);
  s.session.capture([{...s.elements()[0],x:80}]);await s.timersRun();
  s.session.reset();s.session.accept(snapshot([],{scene_id:2,active_scene_id:2,activation_version:1}));
  await s.respond(snapshot([token()],{tokens_version:4}));
  assert.equal(s.session.context().scene_id,2);assert.equal(s.elements().length,0);s.finish();
});

test('movement during an in-flight create survives creation acknowledgement', async () => {
  const s=setup();s.session.accept(snapshot());
  const t=token(); await s.session.insert({id:'1',name:'Moss'},t.element,t.files.f);
  await s.timersRun();
  s.session.capture([{...s.elements()[0],x:150}]);
  await s.respond(snapshot([token()],{tokens_version:1}));
  assert.equal(s.session.busy,true);assert.equal(s.elements()[0].x,150);
  await s.timersRun();const body=JSON.parse(s.requests[0].options.body);
  assert.equal(body.operations[0].action,'update');assert.equal(body.operations[0].geometry.x,150);
  await s.respond(snapshot([{...token(),element:{...token().element,x:150}}],{tokens_version:2}));s.finish();
});

test('an intermediate empty canvas or free-drawing undo cannot delete an owned token', async () => {
  const s=setup();s.session.accept(snapshot([token()]));s.session.capture([]);await tick();
  assert.equal(s.session.busy,false);assert.equal(s.elements().length,1);assert.equal(s.requests.length,0);s.finish();
});

test('scene activation is available only for a private scene and stays disabled while switching', async () => {
  const s=setup({warden:true}), catalog={active_scene_id:1,scenes:[{id:1,name:'Whiteboard'},{id:2,name:'Prepared room'}]};
  s.session.accept(snapshot());await s.respond(catalog);
  const button=s.nodes.get('scene-activate');
  assert.equal(button.textContent,'Shown to party');assert.equal(button.disabled,true);
  assert.equal(s.nodes.get('scene-visibility-help').textContent,s.config.messages.shownSceneHelp);
  await button.events.click();assert.equal(s.requests.length,0);
  s.session.reset();s.session.accept(snapshot([],{scene_id:2,name:'Prepared room'}));await s.respond(catalog);
  assert.equal(button.textContent,'Show to party');assert.equal(button.disabled,false);
  assert.equal(s.nodes.get('scene-visibility-help').textContent,s.config.messages.privateSceneHelp);
  const activation=button.events.click();
  assert.equal(button.textContent,'Showing…');assert.equal(button.disabled,true);
  await button.events.click();await tick();
  assert.equal(s.requests.length,1);
  assert.equal(JSON.parse(s.requests[0].options.body).action,'activate');
  await s.respond(snapshot([],{scene_id:2,active_scene_id:2,activation_version:1,name:'Prepared room'}));await activation;
  assert.equal(button.textContent,'Shown to party');assert.equal(button.disabled,true);
  assert.equal(s.nodes.get('scene-visibility-help').textContent,s.config.messages.shownSceneHelp);
  await s.respond({...catalog,active_scene_id:2});
  await button.events.click();assert.equal(s.requests.length,0);s.finish();
});

test('activation failure restores the action and stale snapshots do not change the displayed active scene', async () => {
  const s=setup({warden:true});
  s.session.accept(snapshot([],{active_scene_id:2,activation_version:1}));
  await s.respond({active_scene_id:2,scenes:[{id:1,name:'Whiteboard'}]});
  const button=s.nodes.get('scene-activate');
  s.session.accept(snapshot());
  assert.equal(button.textContent,'Show to party');assert.equal(button.disabled,false);
  assert.equal(s.requests.length,0);
  const activation=button.events.click();await tick();
  s.requests.shift().resolve({ok:false,status:503});await activation;
  assert.equal(button.textContent,'Show to party');assert.equal(button.disabled,false);s.finish();
});

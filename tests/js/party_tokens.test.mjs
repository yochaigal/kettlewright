import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../../app/static/src/js/maps/party_tokens.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const scope = vm.createContext({});
vm.runInContext(source + '\nthis.helpers = {initials, tokenElement, groupTokens};', scope);
const {initials, tokenElement, groupTokens} = scope.helpers;
test('fallback initials handle empty and non-Latin names', () => {
  assert.equal(initials(''), '?');
  assert.equal(initials('  Ирина Волкова '), 'ИВ');
  assert.equal(initials('A long character name'), 'AL');
});
test('token stays scene-sized and centered after zoom and pan', () => {
  const token = tokenElement('portrait', {width: 1000, height: 600, zoom: {value: 2}, scrollX: -100, scrollY: 30}, 'token');
  assert.equal(token.x, 310); assert.equal(token.y, 80);
  assert.equal(token.width, 80); assert.equal(token.fileId, 'portrait');
  assert.equal(token.type, 'image'); assert.equal(token.locked, false);
});


function dropBoard() {
  const handlers = {}, nodes = new Map();
  const document = {getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, {addEventListener() {}});
    return nodes.get(id);
  }};
  let generation = 1, editable = true, updates = [], files = [];
  let respond = async () => ({ok: true, json: async () => ({tokens: [{id: 'companion:7', name: 'Wolf'}]})});
  const context = vm.createContext({document, crypto: {randomUUID: () => 'uuid'}, AbortSignal,
    restoreElements: elements => elements, CaptureUpdateAction: {IMMEDIATELY: 'now'},
    fetch: (...args) => respond(...args)});
  vm.runInContext(source + `
    tokenPortrait = async () => ({file: {id: 'portrait', dataURL: 'png'}, fallback: false});
    this.setup = setupPartyTokens;`, context);
  const api = {getAppState: () => ({width: 1000, height: 600, offsetLeft: 100, offsetTop: 50,
    zoom: {value: 2}, scrollX: -20, scrollY: 30}), getSceneElements: () => [],
    addFiles: added => files.push(...added), updateScene: update => updates.push(update), setActiveTool() {}, setToast() {}};
  context.setup({editor: {addEventListener: (event, fn) => handlers[event] = fn},
    config: {tokensUrl: '/tokens', messages: {}}, getApi: () => api,
    getGeneration: () => generation, canInsert: () => editable, beforeInsert() {}});
  const event = (id = 'companion:7') => ({clientX: 500, clientY: 250,
    dataTransfer: {types: ['application/x-kettlewright-actor'], getData: () => id},
    preventDefault() {}, stopPropagation() {}});
  return {handlers, updates, files, event, setGeneration: value => generation = value,
    setEditable: value => editable = value, respond: fn => respond = fn};
}
test('dropping a companion creates a linked token at the drop position', async () => {
  const board = dropBoard();
  await board.handlers.drop(board.event());
  const element = board.updates[0].elements[0];
  assert.equal(element.id, 'actor-companion-7-uuid');
  assert.equal(element.fileId, board.files[0].id);
  assert.equal(element.x, 180); assert.equal(element.y, 30);
  assert.equal(board.updates[0].captureUpdate, 'now');
});
test('unknown actors and view-only boards cannot insert dropped tokens', async () => {
  const board = dropBoard();
  await board.handlers.drop(board.event('999'));
  board.setEditable(false);
  await board.handlers.drop(board.event());
  assert.equal(board.updates.length, 0);
});
test('board replacement while loading a dropped token cancels insertion', async () => {
  const board = dropBoard();
  board.respond(async () => {board.setGeneration(2); return {ok: true,
    json: async () => ({tokens: [{id: 'companion:7', name: 'Wolf'}]})};});
  await board.handlers.drop(board.event());
  assert.equal(board.updates.length, 0);
});

const creature = (id, changes = {}) => ({id:`companion:${id}`,name:'Banshee',kind:'monster',portrait:'/banshee.png',parent:'Party',...changes});

test('the picker groups matching creatures while preserving character, owner and artwork distinctions', () => {
  const tokens=[creature(1),{id:1,name:'Leif',portrait:'/hero.png'},creature(2),
    creature(3,{kind:'pet'}),creature(4,{portrait:'/different.png'}),creature(5,{name:'Chief'}),
    creature(6,{parent:'Different owner'}),{id:2,name:'Leif',portrait:'/hero.png'}];
  const groups=groupTokens(tokens);
  assert.deepEqual(Array.from(groups,group=>Array.from(group,actor=>actor.id)),
    [['companion:1','companion:2'],[1],['companion:3'],['companion:4'],['companion:5'],['companion:6'],[2]]);
});

test('identical parent names cannot merge pets from different characters', () => {
  const pets=[creature(1,{kind:'pet',parent:'Leif',parent_key:'character:1'}),
    creature(2,{kind:'pet',parent:'Leif',parent_key:'character:2'}),creature(3,{kind:'pet',parent:'Leif',parent_key:'character:1'})];
  assert.deepEqual(Array.from(groupTokens(pets),group=>Array.from(group,actor=>actor.id)),
    [['companion:1','companion:3'],['companion:2']]);
});

class PickerNode {
  constructor(tag) {this.tagName=tag;this.children=[];this.events={};this.attrs={};this.textContent='';this.hidden=false;this.open=false;}
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren(...nodes) {this.children=nodes;}
  addEventListener(name,fn) {this.events[name]=fn;}
  setAttribute(name,value) {this.attrs[name]=value;}
  getAttribute(name) {return this.attrs[name];}
  removeAttribute(name) {delete this.attrs[name];}
  focus() {this.focused=true;}
  showModal() {this.open=true;}
  close() {this.open=false;}
  querySelector(tag) {for (const node of this.children) {if (node.tagName===tag) return node;const nested=node.querySelector?.(tag);if (nested) return nested;}return null;}
}
async function tokenPicker(tokens, portrait = async actor=>({file:{id:`portrait-${actor.id}`,dataURL:'png'},fallback:false})) {
  const nodes=new Map(),inserted=[];
  const document={getElementById(id) {if (!nodes.has(id)) nodes.set(id,new PickerNode('div'));return nodes.get(id);},createElement:tag=>new PickerNode(tag)};
  document.getElementById('tokens-title').textContent='Tokens';document.getElementById('tokens-help').textContent='Choose a portrait.';
  const context=vm.createContext({document,AbortSignal,crypto:{randomUUID:()=> 'uuid'},renderPortrait:portrait,
    fetch:async()=>({ok:true,json:async()=>({tokens})}),restoreElements:elements=>elements,CaptureUpdateAction:{IMMEDIATELY:'now'}});
  vm.runInContext(source+'\ntokenPortrait = renderPortrait; this.setup = setupPartyTokens;',context);
  const picker=context.setup({editor:{addEventListener() {}},config:{tokensUrl:'/tokens',messages:{
    tokensLoading:'Loading',tokensChooseGroup:'Choose one',tokensChooseMember:'Choose a creature',tokensEmpty:'Empty',tokensFailed:'Failed'}},
    getApi:()=>({getAppState:()=>({width:1000,height:600,zoom:{value:1},scrollX:0,scrollY:0}),setActiveTool() {}}),
    getGeneration:()=>1,canInsert:()=>true,beforeInsert() {},managedInsert:async(actor,element)=>inserted.push({actor,element})});
  await picker.open();return {picker,nodes,inserted,grid:nodes.get('tokens-grid')};
}
test('a stack shows the total count but at most three cards, and opens individual creatures', async () => {
  const s=await tokenPicker(Array.from({length:5},(_,index)=>creature(index+1)));
  assert.equal(s.grid.children.length,1);
  const stack=s.grid.children[0],button=stack.children[0];
  assert.equal(stack.getAttribute('data-cards'),'3');
  assert.equal(button.children.find(node=>node.className==='token-count').textContent,5);
  await button.events.click();assert.equal(s.inserted.length,0);assert.equal(s.grid.children.length,5);
  assert.equal(s.nodes.get('tokens-title').textContent,'Banshee (5)');assert.equal(s.nodes.get('tokens-back').hidden,false);
  assert.equal(s.grid.children[2].children[1].textContent,'Banshee · 3');
  await s.grid.children[2].events.click();
  assert.equal(s.inserted[0].actor.id,'companion:3');assert.equal(s.inserted[0].actor.name,'Banshee');
  assert.equal(s.inserted[0].element.id,'actor-companion-3-uuid');assert.equal(s.nodes.get('party-tokens').open,false);
});
test('two creatures use two cards, back restores the grouped list, and single characters place directly', async () => {
  const s=await tokenPicker([creature(1),creature(2),{id:7,name:'Leif'}]);
  assert.equal(s.grid.children[0].getAttribute('data-cards'),'2');assert.equal(s.grid.children[1].className,'party-token');
  await s.grid.children[0].children[0].events.click();
  s.nodes.get('tokens-back').events.click();
  assert.equal(s.nodes.get('tokens-title').textContent,'Tokens');assert.equal(s.nodes.get('tokens-back').hidden,true);
  assert.equal(s.grid.children.length,2);assert.equal(s.inserted.length,0);
  await s.grid.children[1].events.click();assert.equal(s.inserted[0].actor.id,7);
  await s.picker.open();assert.equal(s.nodes.get('tokens-title').textContent,'Tokens');assert.equal(s.grid.children.length,2);
});
test('closing a stack while its chosen portrait loads prevents stale placement', async () => {
  let finish;const pending=new Promise(resolve=>finish=resolve);
  const s=await tokenPicker([creature(1),creature(2)],()=>pending);
  await s.grid.children[0].children[0].events.click();
  const placing=s.grid.children[1].events.click();s.picker.close();
  finish({file:{id:'portrait',dataURL:'png'},fallback:false});await placing;
  assert.equal(s.inserted.length,0);
});

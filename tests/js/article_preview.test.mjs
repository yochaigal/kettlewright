import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Exercise the actual panel handlers with a minimal DOM and controlled timers.
function previews(lang='en') {
  const timers=new Map(), panels=[];
  let timerId=0;
  const element=()=>({style:{},attributes:{},listeners:{},textContent:'',
    setAttribute(key,value){this.attributes[key]=value;},
    getAttribute(key){return this.attributes[key];},
    addEventListener(name,handler){this.listeners[name]=handler;}});
  const labels={pin:lang==='ru'?'Закрепить':lang==='uk'?'Закріпити':'Pin',
    unpin:lang==='ru'?'Открепить':lang==='uk'?'Відкріпити':'Unpin'};
  const document={documentElement:{lang},addEventListener(){},
    getElementById(id){return id==='interface-labels'?{textContent:JSON.stringify(labels)}:null;},
    body:{append(panel){panels.push(panel);}},
    createElement(){
      const panel=element(), bar=element();
      const buttons=Object.fromEntries(['[data-pin]','[data-close]','[data-drag]','.article-preview-title'].map(key=>[key,element()]));
      bar.querySelector=key=>buttons[key];
      panel.querySelector=key=>key==='header'?bar:element();
      Object.assign(panel,{dataset:{},offsetWidth:760,offsetHeight:680,
        remove(){this.removed=true;},controller:null});
      panel.pin=buttons['[data-pin]'];
      panel.pin.setAttribute('aria-pressed','false');
      return panel;
    }};
  const context=vm.createContext({document,URL,AbortController,location:{origin:'https://example.test'},
    innerWidth:1280,innerHeight:800,
    setTimeout(fn){timers.set(++timerId,fn);return timerId;},clearTimeout(id){timers.delete(id);},
    previewPosition:()=>({left:8,top:8,maxHeight:780}),addPreviewResizeHandles(){},
    fetch:async()=>({ok:false})});
  const source=readFileSync(new URL('../../app/static/src/js/article-preview.js',import.meta.url),'utf8')
    .replace(/^import .*;\n/gm,'').replace('export function previewURL','function previewURL');
  vm.runInContext(source,context);
  return {panels,async show(){
    context.link={textContent:'Article',getBoundingClientRect:()=>({})};
    await vm.runInContext("show(link, '/materials/1/preview')",context);
    return panels.at(-1);
  },flush(){for(const [id,fn] of [...timers]) {timers.delete(id);fn();}}};
}

test('Pin toggles to Unpin and back; unpinned previews close on pointer leave',async()=>{
  for(const lang of ['en','ru','uk']) {
    const ui=previews(lang), panel=await ui.show();
    panel.pin.onclick();
    assert.equal(panel.pin.getAttribute('aria-pressed'),'true');
    assert.equal(panel.pin.title,lang==='ru'?'Открепить':lang==='uk'?'Відкріпити':'Unpin');
    assert(!panel.pin.disabled);
    panel.listeners.pointerleave();ui.flush();
    assert(!panel.removed);
    panel.pin.onclick();
    assert.equal(panel.pin.getAttribute('aria-pressed'),'false');
    assert.equal(panel.pin.title,lang==='ru'?'Закрепить':lang==='uk'?'Закріпити':'Pin');
    panel.listeners.pointerleave();ui.flush();
    assert(panel.removed);
    assert(panel.controller.signal.aborted);
  }
});

test('unpin replaces an existing transient and cancels its pending close timer',async()=>{
  const ui=previews(), pinned=await ui.show();
  pinned.pin.onclick();
  const transient=await ui.show();
  transient.listeners.pointerleave();
  pinned.pin.onclick();
  assert(transient.removed);
  ui.flush();
  assert(!pinned.removed);
  pinned.listeners.pointerleave();ui.flush();
  assert(pinned.removed);
});

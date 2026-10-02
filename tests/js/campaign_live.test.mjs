import test from 'node:test';
import assert from 'node:assert/strict';

test('party article refresh updates its embedded drawing and clears revoked content',async t=>{
  const events=[],children=[];
  const host={dataset:{partyContent:'1'}},container={replaceChildren(...items){children.splice(0,children.length,...items);}};
  const graph={nodes:[{id:1,title:'Published landmark'}],edges:[]};
  const page={getElementById:()=>({childNodes:['Updated article']}),querySelector:()=>({dataset:{graph:JSON.stringify(graph)}})};
  for(const [key,value] of Object.entries({
    window:{addEventListener(){},dispatchEvent(event){events.push(event);}},
    document:{querySelector:selector=>selector==='[data-party-content]'?host:{},getElementById:()=>container},
    location:{href:'/party/1/materials/4'},
    DOMParser:class{parseFromString(){return page;}},
  })) {
    const original=Object.getOwnPropertyDescriptor(globalThis,key);
    Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});
    t.after(()=>original?Object.defineProperty(globalThis,key,original):delete globalThis[key]);
  }
  t.mock.method(globalThis,'setInterval',()=>0);
  t.mock.method(globalThis,'fetch',async()=>({ok:true,redirected:false,text:async()=>''}));
  const {refreshPartyContent}=await import('../../app/static/src/js/campaign_live.js');
  await refreshPartyContent(2);
  assert.equal(events.length,0);
  await refreshPartyContent(1);
  assert.deepEqual(children,['Updated article']);
  assert.equal(events[0].type,'campaign-refresh');
  assert.deepEqual(events[0].detail.graph,graph);
  page.querySelector=()=>null;
  await refreshPartyContent(1);
  assert.equal(events.at(-1).type,'campaign-access-lost');
  t.mock.method(globalThis,'fetch',async()=>({ok:false,status:403}));
  await refreshPartyContent(1);
  assert.deepEqual(children,[]);
  assert.equal(events.at(-1).type,'campaign-access-lost');
});

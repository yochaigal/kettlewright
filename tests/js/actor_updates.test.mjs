import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../../app/static/src/js/maps/actor_updates.js', import.meta.url), 'utf8').replace(/^export /gm, '');
const tick = () => new Promise(resolve => setImmediate(resolve));
function setup(connected = true) {
  const requests = [], events = {}, timers = new Map(), intervals = new Map(), received = {};
  let id = 0, denied = false;
  const document = {hidden: false, addEventListener(name, fn) {events[name] = fn;}, removeEventListener(name) {delete events[name];}};
  const socket = {connected, on(name, fn) {events[name] = fn;}, off(name) {delete events[name];}};
  const context = vm.createContext({document, AbortSignal,
    setTimeout(fn) {timers.set(++id, fn); return id;}, clearTimeout(id) {timers.delete(id);},
    setInterval(fn, delay) {intervals.set(++id, {fn, delay}); return id;}, clearInterval(id) {intervals.delete(id);},
    fetch: (url, options) => new Promise((resolve, reject) => requests.push({url, options, resolve, reject})),
  });
  vm.runInContext(source + '\nthis.create = createActorUpdates;', context);
  const updates = context.create({config: {actorsUrl: '/actors', partyId: 1}, socket, denied: response => {denied = response.status === 403; return denied;}});
  for (const key of ['stats', 'portraits', 'rollActors']) {
    received[key] = []; updates.subscribe(key, value => received[key].push(value));
  }
  return {updates, requests, events, document, socket, intervals, received, get denied() {return denied;},
    async timers() {const queued = [...timers.values()]; timers.clear(); queued.forEach(fn => fn()); await tick();}};
}
const respond = async (request, data = {stats: [], portraits: [], rollActors: []}) => {
  request.resolve({ok: true, status: 200, json: async () => data}); await tick();
};

test('one snapshot feeds three consumers with a slow connected repair poll', async () => {
  const s = setup();
  assert.equal(s.requests.length, 1);
  assert.equal(s.requests[0].url, '/actors');
  assert.equal([...s.intervals.values()][0].delay, 60000);
  const data = {stats: [{id: '1'}], portraits: [{id: '2'}], rollActors: [{id: '3'}]};
  const unsubscribe = s.updates.subscribe('stats', () => {});
  await respond(s.requests.shift(), data);
  for (const key of Object.keys(data)) assert.deepEqual(s.received[key], [data[key]]);
  s.updates.destroy(); assert.equal(s.intervals.size, 0);
  assert.doesNotThrow(unsubscribe);
});

test('event bursts coalesce, with at most one request in flight and one follow-up', async () => {
  const s = setup(); await respond(s.requests.shift());
  s.events.party_actors_changed({party_id: 2}); await s.timers();
  assert.equal(s.requests.length, 0);
  for (let i = 0; i < 20; i++) s.events.party_members_changed({party_id: 1});
  await s.timers(); assert.equal(s.requests.length, 1);
  for (let i = 0; i < 20; i++) s.events.party_actors_changed({party_id: 1});
  await s.timers(); assert.equal(s.requests.length, 1);
  await respond(s.requests.shift()); await s.timers();
  assert.equal(s.requests.length, 1);
  await respond(s.requests.shift()); await s.timers();
  assert.equal(s.requests.length, 0);
  s.updates.destroy();
});

test('hidden tabs skip HTTP polls and recover on visibility or reconnect', async () => {
  const s = setup(); await respond(s.requests.shift());
  s.document.hidden = true;
  s.events.party_actors_changed({party_id: 1});
  [...s.intervals.values()][0].fn(); await s.timers();
  assert.equal(s.requests.length, 0);
  s.document.hidden = false; s.events.visibilitychange(); await s.timers();
  assert.equal(s.requests.length, 1); await respond(s.requests.shift());
  s.socket.connected = false; s.events.disconnect();
  assert.equal([...s.intervals.values()][0].delay, 15000);
  s.socket.connected = true; s.events.connect(); await s.timers();
  assert.equal([...s.intervals.values()][0].delay, 60000);
  assert.equal(s.requests.length, 1);
  s.updates.destroy();
});

test('failed refresh clears stale permissions and teardown ignores late responses', async () => {
  const s = setup(); s.requests.shift().reject(new Error('offline')); await tick();
  assert.equal(s.received.stats.at(-1), null);
  assert.equal(s.received.rollActors.at(-1), null);
  s.updates.refresh(); const read = s.requests.shift();
  s.updates.destroy(); await respond(read, {stats: [{id: 'private'}]});
  assert.equal(s.received.stats.length, 1);
  assert.equal(Object.keys(s.events).length, 0);
});

test('placement changes refresh artwork while ordinary token movements do not', async () => {
  const s = setup(); await respond(s.requests.shift());
  s.updates.placed([]);
  s.updates.placed([{id: 'background'}]); await s.timers();
  assert.equal(s.requests.length, 0);
  s.updates.placed([{id: 'actor-1-token'}]); await s.timers();
  assert.equal(s.requests.length, 1); await respond(s.requests.shift());
  s.updates.placed([{id: 'actor-1-token', x: 100}]); await s.timers();
  assert.equal(s.requests.length, 0);
  s.updates.destroy();
});

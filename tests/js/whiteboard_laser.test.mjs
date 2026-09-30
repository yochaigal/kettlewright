import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_laser.js', import.meta.url), 'utf8').replace('export ', '');
function setup() {
  const handlers = {}, sent = [], updates = [], timers = new Map(); let clock = 0, n = 0, sweep;
  const socket = {connected: true, on: (key, callback) => {handlers[key] = callback;}, volatile: {emit: (key, value) => sent.push(value)}};
  const scope = vm.createContext({setTimeout: fn => {timers.set(++n, fn); return n;}, clearTimeout: id => timers.delete(id),
    setInterval: fn => {sweep = fn;}, clearInterval() {}});
  vm.runInContext(source + '\nthis.create = createLaserSync;', scope);
  const sync = scope.create({socket, getApi: () => ({updateScene: value => updates.push(value)}), getGeneration: () => 2,
    config: {partyId: 1, csrfToken: 'csrf'}, canSend: () => true, now: () => clock});
  return {sync, socket, handlers, sent, updates, advance(value) {clock += value; for (const fn of timers.values()) fn(); timers.clear(); sweep();}};
}
test('only laser is broadcast, throttled with latest trailing coordinates, without offline buffering', () => {
  const s = setup(); s.sync.pointerUpdate({pointer: {x: 0, y: 0, tool: 'pointer'}, button: 'up'}); assert.equal(s.sent.length, 0);
  for (let x = 0; x < 10; x++) s.sync.pointerUpdate({pointer: {x, y: 5, tool: 'laser'}, button: 'down'});
  assert.equal(s.sent.length, 1); s.advance(40); assert.equal(s.sent.at(-1).pointer.x, 9);
  assert.equal(s.sent[0].generation, 2); assert.equal(s.sent[0].csrf_token, 'csrf');
  s.socket.connected = false; s.sync.pointerUpdate({pointer: {x: 10, y: 5, tool: 'laser'}, button: 'down'});
  s.advance(40); assert.equal(s.sent.length, 2);
});
test('remote laser uses transient collaborators, ignores old boards and expires', () => {
  const s = setup(); const packet = {party_id: 1, generation: 2, sender: 'peer', pointer: {x: 30, y: 40, tool: 'laser'}, button: 'down'};
  s.handlers.whiteboard_laser({...packet, generation: 1}); assert.equal(s.updates.length, 0);
  s.handlers.whiteboard_laser({...packet, party_id: 2}); assert.equal(s.updates.length, 0);
  s.handlers.whiteboard_laser(packet); assert.equal(s.updates.at(-1).collaborators.get('peer').pointer.x, 30);
  assert.equal(Object.keys(s.updates[0]).join(','), 'collaborators');
  s.advance(1600); assert.equal(s.updates.at(-1).collaborators.size, 0);
  s.handlers.whiteboard_laser(packet); s.handlers.disconnect(); assert.equal(s.updates.at(-1).collaborators.size, 0);
});

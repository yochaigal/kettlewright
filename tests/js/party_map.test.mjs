import test from 'node:test';
import assert from 'node:assert/strict';
import partyMap, {listedPins} from '../../app/static/src/js/alpine/components/party-map.js';

const nodes = [{id: 4, title: 'Old **Mill**', x: 10, y: 20}, {id: 9, title: 'Ford', x: 30, y: 40}];
const pins = [{id: 21, title: 'Camp', x: 50, y: 60, color: 'blue'}, {id: 22, title: 'Bones', x: 70, y: 80}];

test('the map\'s own pins and the party\'s are listed together, the map\'s first (#525)', () => {
  assert.deepEqual(listedPins(nodes, pins), [
    {key: 'map-4', kind: 'map', id: '4', title: 'Old **Mill**', x: 10, y: 20},
    {key: 'map-9', kind: 'map', id: '9', title: 'Ford', x: 30, y: 40},
    {key: 'party-21', kind: 'party', id: '21', title: 'Camp', x: 50, y: 60, color: '#1971c2'},  // Its colour (#533).
    {key: 'party-22', kind: 'party', id: '22', title: 'Bones', x: 70, y: 80, color: '#e03131'},  // Red by default.
  ]);
  assert.deepEqual(listedPins([], []), []);
  // A map pin and a party pin with the same id are still two entries.
  assert.deepEqual(listedPins([{id: 1, title: 'A'}], [{id: 1, title: 'B'}]).map(item => item.key), ['map-1', 'party-1']);
});

test('a listed pin opens like one clicked on the map, and the count is every pin', () => {
  const originalStorage = globalThis.localStorage;
  globalThis.localStorage = {getItem: () => null, setItem() {}};
  try {
    const map = partyMap();
    const sent = [];
    const messages = [];
    Object.assign(map, {graph: {nodes, edges: []}, pins, labels: {pinOne: 'pin', pinMany: 'pins'}, sync: () => sent.push('sync'),
      send: (type, detail) => messages.push([type, detail]), $refs: {}});
    assert.equal(map.pinCount, '4 pins');
    map.selectedEdge = '7';
    map.selectListed(map.pinList[1]);
    assert.deepEqual([map.selected, map.selectedPin, map.selectedEdge], ['9', '', '']);
    assert.equal(map.selectedNode.title, 'Ford');
    map.selectListed(map.pinList[2]);
    assert.deepEqual([map.selected, map.selectedPin], ['', '21']);
    assert.equal(map.pin.title, 'Camp');
    assert.equal(sent.length, 2);
    // The map centres on each chosen pin (#533).
    assert.deepEqual(messages, [['center', {x: 30, y: 40}], ['center', {x: 50, y: 60}]]);
    map.pins = [];
    map.graph = {nodes: [{id: 1, title: 'Only'}], edges: []};
    assert.equal(map.pinCount, '1 pin');
  } finally {
    globalThis.localStorage = originalStorage;
  }
});


test('a new pin is red unless its maker chooses another colour, which goes with it (#533)', async () => {
  const originalLocation = globalThis.location, originalDocument = globalThis.document;
  globalThis.location = {origin: 'https://kw.test'};
  globalThis.document = {fullscreenElement: null};
  try {
    const map = partyMap();
    const posted = [];
    Object.assign(map, {urls: {pins: '/pins'}, labels: {}, pins: [], sync() {}, $nextTick: fn => fn(),
      $refs: {canvas: {contentWindow: 'frame'}, pinDialog: {showModal() {}, close() {}}},
      post: async (url, fields) => { posted.push(fields); return {ok: true, data: {pins: []}}; }});
    map.receive({source: 'frame', origin: 'https://kw.test', data: {channel: 'kw-map', type: 'picked', x: 1, y: 2}});
    assert.equal(map.draft.color, 'red');
    map.draft.title = 'Camp';
    await map.savePin();
    map.draft = {x: 1, y: 2, title: 'Ford', body: '', color: 'green'};
    await map.savePin();
    assert.deepEqual(posted.map(fields => fields.color), ['red', 'green']);
    assert.deepEqual(map.pinColors.map(color => color.name), ['red', 'orange', 'yellow', 'green', 'blue', 'purple']);
  } finally {
    globalThis.location = originalLocation;
    globalThis.document = originalDocument;
  }
});

import test from 'node:test';
import assert from 'node:assert/strict';
import partyMap, {listedPins} from '../../app/static/src/js/alpine/components/party-map.js';

const nodes = [{id: 4, title: 'Old **Mill**'}, {id: 9, title: 'Ford'}];
const pins = [{id: 21, title: 'Camp'}, {id: 22, title: 'Bones'}];

test('the map\'s own pins and the party\'s are listed together, the map\'s first (#525)', () => {
  assert.deepEqual(listedPins(nodes, pins), [
    {key: 'map-4', kind: 'map', id: '4', title: 'Old **Mill**'},
    {key: 'map-9', kind: 'map', id: '9', title: 'Ford'},
    {key: 'party-21', kind: 'party', id: '21', title: 'Camp'},
    {key: 'party-22', kind: 'party', id: '22', title: 'Bones'},
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
    Object.assign(map, {graph: {nodes, edges: []}, pins, labels: {pinOne: 'pin', pinMany: 'pins'}, sync: () => sent.push('sync')});
    assert.equal(map.pinCount, '4 pins');
    map.selectedEdge = '7';
    map.selectListed(map.pinList[1]);
    assert.deepEqual([map.selected, map.selectedPin, map.selectedEdge], ['9', '', '']);
    assert.equal(map.selectedNode.title, 'Ford');
    map.selectListed(map.pinList[2]);
    assert.deepEqual([map.selected, map.selectedPin], ['', '21']);
    assert.equal(map.pin.title, 'Camp');
    assert.equal(sent.length, 2);
    map.pins = [];
    map.graph = {nodes: [{id: 1, title: 'Only'}], edges: []};
    assert.equal(map.pinCount, '1 pin');
  } finally {
    globalThis.localStorage = originalStorage;
  }
});

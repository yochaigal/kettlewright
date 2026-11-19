import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_dungeon.js', import.meta.url), 'utf8');
const D = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

const room = (c1, r1, c2, r2, size = 80) => D.paint(D.emptyDungeon(size), D.cellsInBox([c1 * size, r1 * size], [c2 * size, r2 * size], size));
const ids = shapes => shapes.map(shape => shape.id).sort();
const roundTrip = dungeon => D.dungeonFromShapes(D.dungeonShapes(dungeon), dungeon.size);
const same = (a, b) => {
  assert.deepEqual([...a.cells].sort(), [...b.cells].sort());
  assert.deepEqual([...a.edges].sort(), [...b.edges].sort());
};

test('a dragged stroke fills every square it crosses, even when the pointer jumps', () => {
  const cells = D.cellsAlong([10, 10], [10 + 80 * 5, 10], 80);
  assert.deepEqual([...cells].sort(), ['0,0', '1,0', '2,0', '3,0', '4,0', '5,0']);
  assert.deepEqual([...D.cellsAlong([-10, -10], [-10, -10], 80)], ['-1,-1']);
});

test('a room is one floor rectangle with four walls around it', () => {
  const shapes = D.dungeonShapes(room(0, 0, 2, 1));
  assert.deepEqual(ids(shapes), ['dungeon-80-floor-0_0_3_2', 'dungeon-80-wall-h-0_0_30', 'dungeon-80-wall-h-2_0_30',
    'dungeon-80-wall-v-0_0_20', 'dungeon-80-wall-v-3_0_20']);
  const top = shapes.find(shape => shape.id === 'dungeon-80-wall-h-0_0_30');
  assert.deepEqual([top.x, top.y, top.points], [0, 0, [[0, 0], [240, 0]]]);
  const floor = shapes[0];
  assert.deepEqual([floor.type, floor.x, floor.y, floor.width, floor.height, floor.locked], ['rectangle', 0, 0, 240, 160, true]);
});

test('walls follow the floor as it grows and shrinks', () => {
  const corridor = D.paint(room(0, 0, 1, 1), D.cellsAlong([200, 40], [440, 40], 80));
  assert.equal(D.edgeKind(corridor, 'v:2:0'), 'open', 'the room opens into the corridor');
  assert.equal(D.edgeKind(corridor, 'v:2:1'), 'wall');
  assert.equal(D.edgeKind(corridor, 'v:6:0'), 'wall', 'the corridor end is closed');
  const erased = D.paint(corridor, new Set(['5,0']), true);
  assert.equal(D.edgeKind(erased, 'v:5:0'), 'wall');
  assert.equal(D.edgeKind(erased, 'v:6:0'), null);
});

test('floor merges into few rectangles, so big dungeons stay under the shape limit', () => {
  const big = room(0, 0, 39, 39);
  assert.equal(D.floorRectangles(big.cells).length, 1);
  assert.ok(D.dungeonShapes(big).length <= 5);
  const plus = D.paint(room(1, 0, 1, 2), D.cellsInBox([0, 80], [160, 80], 80));
  assert.equal(D.floorRectangles(plus.cells).length, 3);
});

test('outer walls cycle through door and opening; inner edges through wall and door', () => {
  let dungeon = room(0, 0, 1, 0);
  const outer = 'h:0:0', inner = 'v:1:0';
  assert.deepEqual([1, 2, 3].map(() => (dungeon = D.cycleEdge(dungeon, outer), D.edgeKind(dungeon, outer))), ['door', 'open', 'wall']);
  assert.deepEqual([1, 2, 3].map(() => (dungeon = D.cycleEdge(dungeon, inner), D.edgeKind(dungeon, inner))), ['wall', 'door', 'open']);
  assert.equal(dungeon.edges.size, 0, 'defaults are not stored');
  assert.equal(D.cycleEdge(dungeon, 'h:9:9'), dungeon, 'edges away from the floor are ignored');
});

test('a door leaves a gap in the wall and draws a door leaf', () => {
  const dungeon = D.cycleEdge(room(0, 0, 0, 0), 'h:0:0');
  const shapes = D.dungeonShapes(dungeon);
  assert.ok(ids(shapes).includes('dungeon-80-door-h-0_0'));
  assert.ok(ids(shapes).includes('dungeon-80-wall-h-0_0_3') && ids(shapes).includes('dungeon-80-wall-h-0_7_10'));
});

test('the dungeon is read back from its shapes, including doors, openings and inner walls', () => {
  let dungeon = D.paint(room(-3, -2, 1, 1), D.cellsAlong([200, 0], [500, 0], 80));
  for (const edge of ['h:-3:-2', 'h:-1:-2', 'v:-3:0', 'v:0:0', 'h:5:0']) dungeon = D.cycleEdge(dungeon, edge);
  dungeon = D.cycleEdge(dungeon, 'h:-1:-2');
  same(roundTrip(dungeon), dungeon);
  assert.equal(D.edgeKind(roundTrip(dungeon), 'h:-1:-2'), 'open');
  assert.equal(D.edgeKind(roundTrip(dungeon), 'v:0:0'), 'wall');
});

test('only dungeon shapes of the board size are read; other shapes and deleted ones are ignored', () => {
  const shapes = [...D.dungeonShapes(room(0, 0, 0, 0)), ...D.dungeonShapes(room(5, 5, 5, 5, 40)),
    {id: 'dungeon-80-floor-9_9_1_1', isDeleted: true}, {id: 'rect-1'}, {id: 'dungeon-80-floor-bad'}];
  assert.equal(D.boardSize(shapes), 80);
  assert.deepEqual([...D.dungeonFromShapes(shapes, 80).cells], ['0,0']);
  assert.equal(D.boardSize([{id: 'x'}]), null);
  assert.equal(D.isDungeonShape({id: 'dungeon-80-wall-v--2_10_20'}), true);
});

test('the Doors tool picks the edge nearest the pointer', () => {
  assert.equal(D.edgeAt(5, 40, 80), 'v:0:0');
  assert.equal(D.edgeAt(78, 40, 80), 'v:1:0');
  assert.equal(D.edgeAt(40, 3, 80), 'h:0:0');
  assert.equal(D.edgeAt(40, 79, 80), 'h:0:1');
  assert.equal(D.edgeAt(-40, -78, 80), 'h:-1:-1');
});

// The layer imports the geometry module; load it with that import inlined.
const layerSource = readFileSync(new URL('../../app/static/src/js/maps/whiteboard_dungeon_layer.js', import.meta.url), 'utf8')
  .replace("'./whiteboard_dungeon.js'", `'data:text/javascript;base64,${Buffer.from(source).toString('base64')}'`);
const {nextScene} = await import(`data:text/javascript;base64,${Buffer.from(layerSource).toString('base64')}`);
const toElements = shapes => shapes.map(shape => ({...shape, version: 1, versionNonce: 1, isDeleted: false}));

test('rebuilding keeps unchanged shapes, deletes old ones and puts the dungeon underneath', () => {
  const token = {id: 'actor-1', type: 'image', version: 3}, sketch = {id: 'pen', type: 'freedraw', version: 2};
  const before = toElements(D.dungeonShapes(room(0, 0, 1, 0)));
  const all = [token, ...before, sketch];
  const grown = D.paint(D.dungeonFromShapes(all, 80), new Set(['2,0']));
  const {elements, count, tooBig} = nextScene(all, 80, D.dungeonShapes(grown), toElements);
  const alive = elements.filter(element => !element.isDeleted);
  assert.deepEqual(alive.slice(-2).map(element => element.id), ['actor-1', 'pen'], 'other shapes stay on top');
  assert.ok(alive.slice(0, -2).every(D.isDungeonShape));
  const oldFloor = before.find(element => element.id.includes('floor'));
  const deleted = elements.find(element => element.id === oldFloor.id);
  assert.equal(deleted.isDeleted, true); assert.equal(deleted.version, 2);
  const kept = before.find(element => element.id === 'dungeon-80-wall-v-0_0_10');
  assert.equal(elements.find(element => element.id === kept.id), kept, 'unchanged walls are reused as they are');
  assert.equal(count, alive.length); assert.equal(tooBig, false);
});

test('a shape restored after deletion gets a newer version, and the shape limit is enforced', () => {
  const shapes = D.dungeonShapes(room(0, 0, 0, 0));
  const all = toElements(shapes).map(element => ({...element, isDeleted: true, version: 5}));
  const revived = nextScene(all, 80, shapes, toElements).elements.filter(element => !element.isDeleted);
  assert.ok(revived.length === shapes.length && revived.every(element => element.version === 6));
  const crowded = Array.from({length: 1999}, (_, i) => ({id: `x${i}`, version: 1}));
  assert.equal(nextScene(crowded, 80, shapes, toElements).tooBig, true);
});

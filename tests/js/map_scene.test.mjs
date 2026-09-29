import test from 'node:test';
import assert from 'node:assert/strict';
import {drawingFromScene, graphShapes, movedLocations} from '../../app/static/src/js/maps/scene.js';

test('drawing snapshots exclude graph labels, deleted content and unused images', () => {
  const elements = [
    {id: 'kw-label-1', type: 'text', text: 'Private room'},
    {id: 'duplicated', customData: {kwType: 'location'}},
    {id: 'deleted', isDeleted: true},
    {id: 'token', type: 'image', fileId: 'image1'},
  ];
  assert.deepEqual(drawingFromScene(elements, {image1: {id: 'image1'}, private: {id: 'private'}}),
    {elements: [elements[3]], files: {image1: {id: 'image1'}}});
});

test('graph conversion preserves IDs and skips paths with hidden endpoints', () => {
  const graph = {nodes: [{id: 1, x: 50, y: 70, number: 1, title: 'Known room'}],
    edges: [{id: 2, source: 1, target: 3}]};
  const shapes = graphShapes(graph);
  assert.deepEqual(shapes.map(shape => shape.id), ['kw-node-1', 'kw-label-1']);
  assert.equal(shapes[0].x, 20);
  assert.equal(shapes[1].text, '1. Known room');
  assert.deepEqual(movedLocations([{...shapes[0], x: 25, y: 45}], graph), [{id: '1', x: 55, y: 75}]);
  assert.deepEqual(movedLocations([{...shapes[0], id: 'copy', x: 25}], graph), []);
});
